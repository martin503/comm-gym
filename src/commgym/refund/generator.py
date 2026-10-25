import random
import zlib
from collections.abc import Sequence
from dataclasses import dataclass, replace

import pandas as pd
from loguru import logger

from commgym.dunnhumby.load import Campaign
from commgym.dunnhumby.prices import PricePoint
from commgym.dunnhumby.splits import CampaignCalendar, Splits
from commgym.dunnhumby.types import BrandTier
from commgym.refund.config import PolicyParams, TaskConfig
from commgym.refund.coupons import CouponIndex, live_upcs, typical_value
from commgym.refund.coverage import coverage_of, describe_coverage
from commgym.refund.instance import (
    Claim,
    CouponView,
    ReceiptLine,
    RefundInstance,
)
from commgym.refund.policy import (
    Adjudication,
    ClaimFacts,
    ClaimVerdict,
    Decision,
    ReasonCode,
    StatedType,
    adjudicate,
    allocate_refunds,
)
from commgym.refund.renderer import ClaimSpec

ATTEMPT_CAP = 200


@dataclass(frozen=True, slots=True)
class RefundContext:
    """Everything the generator needs, built once per process."""

    tx: pd.DataFrame  # cleaned transactions with the product size column merged
    prices: dict[tuple[int, int], PricePoint]
    coupons: CouponIndex
    splits: Splits
    cfg: TaskConfig
    live_days: frozenset[int]
    hh_categories: dict[int, dict[str, tuple[int, ...]]]


@dataclass(frozen=True, slots=True)
class PlannedClaim:
    """One planned claim: wording target, stated facts, and pre-allocation truth."""

    stated_type: StatedType
    kind: str  # 'unique' | 'clarify' | 'absent'
    target_lines: tuple[str, ...]
    absent_item: str | None
    stated_cents: int | None
    truth_line: str | None
    truth_decision: Decision
    truth_reason: ReasonCode
    truth_refund_cents: int


@dataclass(frozen=True, slots=True)
class AnchorPlan:
    """A fully planned anchor; wording is rendered later by the LLM stage."""

    split: str
    household: int
    basket: int
    purchase_day: int
    claim_day: int
    policy: PolicyParams
    lines: tuple[ReceiptLine, ...]
    coupons: tuple[CouponView, ...]
    claims: tuple[PlannedClaim, ...]
    is_out_of_window: bool

    @property
    def cache_key(self) -> str:
        return f'{self.split}-{self.basket}-{self.claim_day}'


@dataclass(frozen=True, slots=True)
class PlanBatch:
    plans: tuple[AnchorPlan, ...]
    rejects: dict[str, int]
    skipped_coupons: int  # live covering coupons dropped for lack of an exact description


@dataclass(frozen=True, slots=True)
class AnchorFacts:
    """Per-anchor claim-target facts shared by all of the anchor's claims."""

    lines: tuple[ReceiptLine, ...]
    covering: dict[str, tuple[int, ...]]  # line code -> live covering coupon upcs
    absent_items: tuple[str, ...]  # history categories absent from the receipt


@dataclass(frozen=True, slots=True)
class ClaimTarget:
    """A wording target the renderer must express; the key dedups targets per anchor."""

    kind: str
    key: str
    lines: tuple[str, ...]
    absent_item: str | None = None


def build_refund_context(
    tx: pd.DataFrame,
    prices: dict[tuple[int, int], PricePoint],
    coupons: CouponIndex,
    splits: Splits,
    campaigns: tuple[Campaign, ...],
    cfg: TaskConfig,
) -> RefundContext:
    live_days = CampaignCalendar(campaigns).live_days()
    grouped = (
        tx[['household_key', 'commodity', 'PRODUCT_ID']]
        .drop_duplicates()
        .groupby(['household_key', 'commodity'])['PRODUCT_ID']
        .unique()
        .reset_index()
    )
    hh_categories: dict[int, dict[str, tuple[int, ...]]] = {}
    for household, commodity, products in zip(
        grouped['household_key'], grouped['commodity'], grouped['PRODUCT_ID'], strict=True
    ):
        hh_categories.setdefault(int(household), {})[str(commodity)] = tuple(
            int(p) for p in products
        )
    return RefundContext(
        tx=tx,
        prices=prices,
        coupons=coupons,
        splits=splits,
        cfg=cfg,
        live_days=live_days,
        hh_categories=hh_categories,
    )


def claim_spec(claim: PlannedClaim) -> ClaimSpec:
    """The renderer's view of a planned claim; carries no truth."""
    return ClaimSpec(
        stated_type=claim.stated_type,
        kind=claim.kind,
        target_lines=claim.target_lines,
        absent_item=claim.absent_item,
        stated_cents=claim.stated_cents,
    )


def plan_batch(ctx: RefundContext, split: str, n: int, seed: int) -> PlanBatch:
    spec = ctx.splits.spec(split)
    rng = random.Random(zlib.crc32(f'{seed}-{split}-batch'.encode()))
    side = ctx.tx[
        ctx.tx['household_key'].isin(spec.households)
        & ctx.tx['WEEK_NO'].between(spec.first_week, spec.last_week)
        & ctx.tx['DAY'].isin(ctx.live_days)
    ]
    sizes = side.groupby('BASKET_ID').size()
    candidate_ids = set(sizes[sizes <= ctx.cfg.max_receipt_lines].index)
    groups = {
        basket: group
        for basket, group in side[side['BASKET_ID'].isin(candidate_ids)].groupby(
            'BASKET_ID', sort=False
        )
    }
    # baskets carrying a coupon-discount line are scarce; lead with them so the
    # ALREADY_APPLIED quota can be spent before the general pool runs out
    applied_pool = [
        basket
        for basket, group in groups.items()
        if (group['COUPON_DISC'] + group['COUPON_MATCH_DISC'] != 0).any()
    ]
    general_pool = sorted(set(groups) - set(applied_pool))
    rng.shuffle(applied_pool)
    rng.shuffle(general_pool)
    ordered = applied_pool + general_pool

    n_out = round(n * ctx.cfg.out_of_window_anchor_rate)
    quotas = {
        kind: share * (n - n_out) * ctx.cfg.claims_per_anchor
        for kind, share in _normalized_shares(ctx.cfg).items()
    }
    # out-of-window anchors are spread over the whole plan list, not parked at the end:
    # the render stage keeps the first n surviving anchors, so a tail stratum would be cut
    oow_positions = _spread_positions(n, n_out)
    plans: list[AnchorPlan] = []
    rejects: dict[str, int] = {}
    skipped_coupons = 0
    for attempts, basket in enumerate(ordered, start=1):
        if len(plans) >= n:
            break
        if attempts > ATTEMPT_CAP * n:
            rejects['attempt_budget'] = 1
            break
        anchor_rng = random.Random(zlib.crc32(f'{seed}-{split}-{len(plans):04d}'.encode()))
        result = _plan_anchor(
            ctx,
            groups[basket],
            split,
            len(plans),
            len(plans) in oow_positions,
            anchor_rng,
            quotas,
        )
        if isinstance(result, str):
            rejects[result] = rejects.get(result, 0) + 1
            continue
        plan, skipped = result
        skipped_coupons += skipped
        for claim in plan.claims:
            kind = claim.truth_reason.value
            if kind in quotas:
                quotas[kind] = max(quotas[kind] - 1.0, 0.0)
        plans.append(plan)
    if len(plans) < n:
        logger.warning('{}: only {}/{} anchors planned, rejects {}', split, len(plans), n, rejects)
    else:
        logger.info('{}: {}/{} anchors planned, rejects {}', split, len(plans), n, rejects)
    return PlanBatch(plans=tuple(plans), rejects=rejects, skipped_coupons=skipped_coupons)


def _spread_positions(n: int, k: int) -> frozenset[int]:
    """k positions evenly spread over range(n), so keep-the-first-survivors never cuts them."""
    if k <= 0:
        return frozenset()
    step = n / k
    return frozenset(min(n - 1, round(i * step)) for i in range(k))


def finalize_anchor(
    plan: AnchorPlan, index: int, references: Sequence[str], sentences: Sequence[str]
) -> tuple[RefundInstance, ...]:
    """Bind the rendered wording to the plan; each level's prefix gets its own allocation."""
    claims = [
        Claim(
            stated_type=claim.stated_type,
            reference_text=references[i],
            reference_kind=claim.kind,
            truth_line=claim.truth_line,
            truth_decision=claim.truth_decision,
            truth_reason=claim.truth_reason,
            truth_refund_cents=claim.truth_refund_cents,
            stated_number=claim.stated_cents is not None,
            stated_cents=claim.stated_cents,
        )
        for i, claim in enumerate(plan.claims)
    ]
    return tuple(
        RefundInstance(
            instance_id=f'{plan.split}-L{k + 1}-{index:04d}',
            anchor_id=f'{plan.split}-{index:04d}',
            split=plan.split,
            level=f'L{k + 1}',
            household=plan.household,
            basket=plan.basket,
            purchase_day=plan.purchase_day,
            claim_day=plan.claim_day,
            policy=plan.policy,
            lines=plan.lines,
            coupons=plan.coupons,
            message=' '.join(sentences[: k + 1]),
            claims=_allocated_prefix(claims, k + 1, plan.policy),
            is_out_of_window=plan.is_out_of_window,
        )
        for k in range(len(claims))
    )


def _plan_anchor(
    ctx: RefundContext,
    group: pd.DataFrame,
    split: str,
    index: int,
    out_of_window: bool,
    rng: random.Random,
    quotas: dict[str, float],
) -> tuple[AnchorPlan, int] | str:
    cfg = ctx.cfg
    household = int(group['household_key'].iloc[0])
    purchase_day = int(group['DAY'].iloc[0])
    lines = _receipt_lines(group, ctx.prices)
    if len(lines) > cfg.max_receipt_lines:
        return 'too_many_lines'
    if len(lines) < cfg.anchor_min_target_lines:
        return 'too_few_targets'
    policy = _sample_policy(cfg, rng)
    live = live_upcs(ctx.coupons, household, purchase_day)
    raw_covering = {
        line.code: tuple(sorted(ctx.coupons.product_upcs.get(line.product_id, frozenset()) & live))
        for line in lines
    }
    coupons, covering, skipped = _describable_coupons(ctx.coupons, raw_covering, lines)
    receipt_categories = {line.commodity for line in lines}
    # a history category is claimable as absent only when the receipt carries none of it, so
    # 'cereal' can never be called absent while oatmeal is on the receipt
    absent_items = tuple(
        category
        for category in ctx.hh_categories.get(household, {})
        if category not in receipt_categories
    )
    facts = AnchorFacts(lines=tuple(lines), covering=covering, absent_items=absent_items)
    pools = _claim_pools(facts, policy)
    if out_of_window:
        codes = [line.code for line in lines]
        rng.shuffle(codes)
        if len(codes) < cfg.claims_per_anchor:
            return 'plan_unfillable'
        codes = codes[: cfg.claims_per_anchor]
        start = rng.randrange(2)
        plan = [
            (
                (StatedType.PRICE, StatedType.COUPON)[(i + start) % 2],
                ClaimTarget('unique', code, (code,)),
            )
            for i, code in enumerate(codes)
        ]
    else:
        kinds = _plan_kinds(pools, quotas, cfg.claims_per_anchor, rng)
        if len(kinds) < cfg.claims_per_anchor:
            return 'plan_unfillable'
        plan = _assign_targets(kinds, pools, rng, cfg)
        if plan is None:
            return 'target_conflict'
    if out_of_window:
        delay = policy.claim_window_days + rng.randint(1, 30)
    else:
        delay = rng.randint(1, max(1, policy.claim_window_days - 1))
    claims = tuple(
        _planned_claim(
            ctx.cfg,
            ctx.coupons,
            facts,
            stated_type,
            target,
            delay,
            policy,
            rng,
        )
        for stated_type, target in plan
    )
    return (
        AnchorPlan(
            split=split,
            household=household,
            basket=int(group['BASKET_ID'].iloc[0]),
            purchase_day=purchase_day,
            claim_day=purchase_day + delay,
            policy=policy,
            lines=facts.lines,
            coupons=coupons,
            claims=claims,
            is_out_of_window=out_of_window,
        ),
        skipped,
    )


def _sample_policy(cfg: TaskConfig, rng: random.Random) -> PolicyParams:
    """Per-anchor policy draw (spec §12): window, tolerance, cap, and match scope."""
    return PolicyParams(
        claim_window_days=rng.choice(cfg.policy_window_days),
        price_tolerance_cents=rng.choice(cfg.policy_tolerance_cents),
        refund_cap_cents=rng.choice(cfg.policy_refund_caps_cents),
        price_match_national_only=rng.random() < cfg.policy_national_only_prob,
    )


def _describable_coupons(
    coupons: CouponIndex,
    covering: dict[str, tuple[int, ...]],
    lines: list[ReceiptLine],
) -> tuple[tuple[CouponView, ...], dict[str, tuple[int, ...]], int]:
    """Keep only live coupons whose covered lines admit an exact attribute description."""
    views: list[CouponView] = []
    kept: set[int] = set()
    for upc in sorted({up for ups in covering.values() for up in ups}):
        codes = tuple(line.code for line in lines if upc in covering[line.code])
        text = describe_coverage(codes, lines)
        if text is None:
            continue
        assert coverage_of(text, lines) == codes, 'coverage text must re-parse to its lines'
        kept.add(upc)
        views.append(
            CouponView(
                coupon_id=f'C{len(views) + 1:02d}',
                typical_value_cents=typical_value(coupons, upc)[0],
                coverage=text,
            )
        )
    filtered = {code: tuple(up for up in ups if up in kept) for code, ups in covering.items()}
    skipped = len(set().union(*covering.values()) - kept)
    return tuple(views), filtered, skipped


def _allocated_prefix(claims: list[Claim], n: int, policy: PolicyParams) -> tuple[Claim, ...]:
    """Each level's prefix gets its own allocation run: the cap is prefix-local by design."""
    prefix = claims[:n]
    verdicts = [
        ClaimVerdict(claim.truth_decision, claim.truth_line, claim.truth_refund_cents)
        for claim in prefix
    ]
    refunds = allocate_refunds(verdicts, policy)
    return tuple(
        replace(claim, truth_refund_cents=refund)
        for claim, refund in zip(prefix, refunds, strict=True)
    )


def _claim_pools(
    facts: AnchorFacts, policy: PolicyParams
) -> dict[str, list[tuple[ClaimTarget, StatedType]]]:
    by_code = {line.code: line for line in facts.lines}
    covered = {code for code, ups in facts.covering.items() if ups}
    diffs = {line.code: line.loyalty_unit_cents - line.reference_cents for line in facts.lines}
    tol = policy.price_tolerance_cents
    # iterate in receipt order: pool order feeds rng.choice, so a set here would make
    # generation depend on PYTHONHASHSEED
    codes = [line.code for line in facts.lines]
    price_ok = [
        c
        for c in codes
        if not policy.price_match_national_only or by_code[c].brand_tier is BrandTier.NATIONAL
    ]
    price_barred = [c for c in codes if c not in set(price_ok)]
    groups = _clarify_groups(facts.lines)
    clarify = [
        (group, (StatedType.PRICE, StatedType.COUPON)[i % 2]) for i, group in enumerate(groups)
    ]
    absent = [
        (ClaimTarget('absent', f'absent:{c}', (), c), StatedType.MISSING_ITEM)
        for c in facts.absent_items
    ]
    return {
        'PRICE_MATCH': [
            (ClaimTarget('unique', c, (c,)), StatedType.PRICE) for c in price_ok if diffs[c] > tol
        ],
        'WITHIN_TOLERANCE': [
            (ClaimTarget('unique', c, (c,)), StatedType.PRICE) for c in price_ok if diffs[c] <= tol
        ],
        'NOT_ELIGIBLE': [
            *((ClaimTarget('unique', c, (c,)), StatedType.PRICE) for c in price_barred),
            *(
                (ClaimTarget('unique', c, (c,)), StatedType.COUPON)
                for c in codes
                if c not in covered
            ),
        ],
        'MISSED_COUPON': [
            (ClaimTarget('unique', c, (c,)), StatedType.COUPON)
            for c in codes
            if c in covered and by_code[c].coupon_disc_unit_cents == 0
        ],
        'ALREADY_APPLIED': [
            (ClaimTarget('unique', c, (c,)), StatedType.COUPON)
            for c in codes
            if c in covered and by_code[c].coupon_disc_unit_cents != 0
        ],
        'NEEDS_CLARIFICATION': clarify,
        'NOT_ON_RECEIPT': absent,
    }


def _clarify_groups(lines: Sequence[ReceiptLine]) -> list[ClaimTarget]:
    """Whole-category groups plus proper sub-category groups; both need at least two lines."""
    by_commodity: dict[str, list[str]] = {}
    by_sub: dict[tuple[str, str], list[str]] = {}
    for line in lines:
        by_commodity.setdefault(line.commodity, []).append(line.code)
        by_sub.setdefault((line.commodity, line.sub_commodity), []).append(line.code)
    groups = [
        ClaimTarget('clarify', f'grp:{",".join(codes)}', tuple(codes))
        for codes in by_commodity.values()
        if len(codes) >= 2
    ]
    groups += [
        ClaimTarget('clarify', f'sub:{",".join(codes)}', tuple(codes))
        for (commodity, _sub), codes in by_sub.items()
        if len(codes) >= 2 and len(codes) < len(by_commodity[commodity])
    ]
    return groups


def _assign_targets(
    kinds: list[str],
    pools: dict[str, list[tuple[ClaimTarget, StatedType]]],
    rng: random.Random,
    cfg: TaskConfig,
) -> list[tuple[StatedType, ClaimTarget]] | None:
    """Bind kinds to distinct targets; sometimes the second claim repeats the first line."""
    plan: list[tuple[StatedType, ClaimTarget]] = []
    used: set[str] = set()
    for kind in kinds:
        options = [entry for entry in pools[kind] if entry[0].key not in used]
        if not options:
            return None
        target, stated = rng.choice(options)
        used.add(target.key)
        plan.append((stated, target))
    if (
        rng.random() < cfg.same_line_claim_prob
        and len(plan) >= 2
        and kinds[1] != kinds[0]
        and plan[0][1].kind == 'unique'
        and any(entry[0].key == plan[0][1].key for entry in pools[kinds[1]])
    ):
        stated = next(entry[1] for entry in pools[kinds[1]] if entry[0].key == plan[0][1].key)
        plan[1] = (stated, plan[0][1])
    return plan


def _planned_claim(
    cfg: TaskConfig,
    coupons: CouponIndex,
    facts: AnchorFacts,
    stated_type: StatedType,
    target: ClaimTarget,
    days_since: int,
    policy: PolicyParams,
    rng: random.Random,
) -> PlannedClaim:
    if target.kind == 'absent':
        truth = adjudicate(_lineless_facts(stated_type, days_since, 0), policy)
        return _claim_of(stated_type, target, None, None, truth)
    if target.kind == 'clarify':
        truth = adjudicate(_lineless_facts(stated_type, days_since, len(target.lines)), policy)
        return _claim_of(stated_type, target, None, None, truth)
    line = next(item for item in facts.lines if item.code == target.lines[0])
    values = tuple(typical_value(coupons, upc)[0] for upc in facts.covering[line.code])
    truth = adjudicate(
        ClaimFacts(
            stated_type=stated_type,
            days_since_purchase=days_since,
            n_matched_lines=1,
            line_code=line.code,
            loyalty_unit_cents=line.loyalty_unit_cents,
            reference_cents=line.reference_cents,
            quantity=line.quantity,
            covering_coupon_values_cents=values,
            coupon_disc_applied=line.coupon_disc_unit_cents != 0,
            brand_tier=line.brand_tier,
            paid_unit_cents=line.paid_unit_cents,
        ),
        policy,
    )
    stated_cents = _stated_number(cfg, stated_type, line, values, rng)
    return _claim_of(stated_type, target, line.code, stated_cents, truth)


def _claim_of(
    stated_type: StatedType,
    target: ClaimTarget,
    truth_line: str | None,
    stated_cents: int | None,
    truth: Adjudication,
) -> PlannedClaim:
    return PlannedClaim(
        stated_type=stated_type,
        kind=target.kind,
        target_lines=target.lines,
        absent_item=target.absent_item,
        stated_cents=stated_cents,
        truth_line=truth_line,
        truth_decision=truth.decision,
        truth_reason=truth.reason,
        truth_refund_cents=truth.refund_cents,
    )


def _lineless_facts(stated_type: StatedType, days_since: int, n_matched: int) -> ClaimFacts:
    return ClaimFacts(
        stated_type=stated_type,
        days_since_purchase=days_since,
        n_matched_lines=n_matched,
        line_code=None,
        loyalty_unit_cents=None,
        reference_cents=None,
        quantity=None,
        covering_coupon_values_cents=(),
        coupon_disc_applied=False,
    )


def _stated_number(
    cfg: TaskConfig,
    stated_type: StatedType,
    line: ReceiptLine,
    covering_values: tuple[int, ...],
    rng: random.Random,
) -> int | None:
    """A customer-quoted amount contradicting the receipt; receipt values always win."""
    if rng.random() >= cfg.stated_number_prob:
        return None
    if stated_type is StatedType.PRICE:
        paid = line.paid_unit_cents
        delta = max(25, int(round(paid * rng.uniform(0.15, 0.45))))
        wrong = paid + delta if rng.random() < 0.5 else max(1, paid - delta)
        displayed = {
            line.paid_unit_cents,
            line.loyalty_unit_cents,
            line.regular_unit_cents,
            line.reference_cents,
        }
        while wrong in displayed:
            wrong += 1
        return wrong
    if stated_type is StatedType.COUPON and covering_values:
        value = max(covering_values)
        return value + max(25, int(round(value * rng.uniform(0.5, 1.5))))
    return None


def _receipt_lines(
    group: pd.DataFrame, prices: dict[tuple[int, int], PricePoint]
) -> list[ReceiptLine]:
    """Build display-cents receipt lines; paid = regular - loyalty disc - coupon disc exactly."""
    lines: list[ReceiptLine] = []
    for i, (_, row) in enumerate(group.iterrows()):
        regular = int(round(float(row['regular_unit']) * 100))
        loyalty_disc = min(
            max(int(round((float(row['regular_unit']) - float(row['loyalty_unit'])) * 100)), 0),
            regular,
        )
        room = regular - loyalty_disc
        coupon_disc = min(
            max(
                int(
                    round(
                        -(float(row['COUPON_DISC']) + float(row['COUPON_MATCH_DISC']))
                        / int(row['QUANTITY'])
                        * 100
                    )
                ),
                0,
            ),
            room,
        )
        product, week = int(row['PRODUCT_ID']), int(row['WEEK_NO'])
        assert (product, week) in prices, 'price table must cover every receipt line'
        point = prices[(product, week)]
        lines.append(
            ReceiptLine(
                code=f'L{i + 1:02d}',
                product_id=product,
                commodity=str(row['commodity']),
                sub_commodity=str(row['sub_commodity']),
                brand_tier=BrandTier(str(row['brand'])),
                size=str(row['size']) if pd.notna(row['size']) else '',
                quantity=int(row['QUANTITY']),
                regular_unit_cents=regular,
                loyalty_disc_unit_cents=loyalty_disc,
                coupon_disc_unit_cents=coupon_disc,
                paid_unit_cents=room - coupon_disc,
                reference_cents=point.shelf_cents - point.loyalty_disc_cents,
            )
        )
    return lines


def _normalized_shares(cfg: TaskConfig) -> dict[str, float]:
    total = sum(cfg.in_window_type_shares.values())
    return {kind: share / total for kind, share in cfg.in_window_type_shares.items()}


def _plan_kinds(
    pools: dict[str, list[tuple[ClaimTarget, StatedType]]],
    quotas: dict[str, float],
    n_claims: int,
    rng: random.Random,
) -> list[str]:
    """Pick claim kinds: distinct first (quota-weighted), then repeats to fill, pool-limited."""
    sizes = {kind: len(codes) for kind, codes in pools.items()}
    plan: list[str] = []
    for kind in _weighted_order([k for k, s in sizes.items() if s > 0], quotas, rng):
        if len(plan) >= n_claims:
            break
        plan.append(kind)
        sizes[kind] -= 1
    while len(plan) < n_claims and any(s > 0 for s in sizes.values()):
        options = [(max(quotas.get(k, 0.0), 0.01), k) for k, s in sizes.items() if s > 0]
        pick = rng.random() * sum(w for w, _ in options)
        acc = 0.0
        chosen = options[-1][1]
        for weight, kind in options:
            acc += weight
            if pick <= acc:
                chosen = kind
                break
        plan.append(chosen)
        sizes[chosen] -= 1
    return plan


def _weighted_order(kinds: list[str], quotas: dict[str, float], rng: random.Random) -> list[str]:
    """Shuffle kinds with probability proportional to their remaining quota."""
    remaining = list(kinds)
    ordered: list[str] = []
    while remaining:
        weights = [max(quotas.get(k, 0.0), 0.01) for k in remaining]
        pick = rng.random() * sum(weights)
        acc = 0.0
        chosen = remaining[-1]
        for weight, kind in zip(weights, remaining, strict=True):
            acc += weight
            if pick <= acc:
                chosen = kind
                break
        remaining.remove(chosen)
        ordered.append(chosen)
    return ordered
