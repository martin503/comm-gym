from dataclasses import dataclass, replace

import pandas as pd
import pytest
from _mocks.fake_text import FakeTextModel

from commgym.dunnhumby.clean import prepare_transactions
from commgym.dunnhumby.config import CleaningConfig, PricingConfig
from commgym.dunnhumby.load import Campaign, CampaignTargeting, CouponEligibility, Product
from commgym.dunnhumby.prices import PricePoint, build_price_table
from commgym.dunnhumby.splits import Splits, SplitSpec
from commgym.refund.config import TaskConfig
from commgym.refund.coupons import CouponIndex, build_coupon_index, live_upcs, typical_value
from commgym.refund.coverage import coverage_of
from commgym.refund.generator import (
    RefundContext,
    _spread_positions,
    build_refund_context,
    claim_spec,
    finalize_anchor,
    plan_batch,
)
from commgym.refund.instance import Claim, RefundInstance
from commgym.refund.policy import ClaimVerdict, Decision, StatedType, allocate_refunds
from commgym.refund.renderer import render_anchor, split_sentences

# Two households buy identical 9-line baskets on days 240/247/253 (weeks 35/36/37); filler
# households 3/4 buy every product a day earlier at the filler price so the chain-median
# reference prices land where each product needs: 101/107 overcharged, 102/103 within
# tolerance, 106 already coupon-discounted, 104/110 covered-but-undiscounted, 105 uncovered.
# Product 109 (soda) appears only in pre-window history baskets -> NOT_ON_RECEIPT supply.
PRODUCT_SPECS: dict[int, tuple[str, str, str, float, float, float, int, float]] = {
    101: ('POTATOES', 'Private', '5 LB', 3.20, 0.0, 0.0, 2, 1.00),
    102: ('BAG SNACKS', 'National', '12 OZ', 1.03, 0.0, 0.0, 1, 1.00),
    103: ('FLUID MILK PRODUCTS', 'National', '1 GAL', 1.00, -0.20, 0.0, 1, 1.00),
    104: ('YOGURT', 'Private', '6 OZ', 1.50, 0.0, 0.0, 1, 1.50),
    105: ('YOGURT', 'National', '32 OZ', 3.00, 0.0, 0.0, 1, 3.00),
    106: ('CHEESE', 'National', '8 OZ', 2.00, 0.0, -0.30, 1, 2.00),
    107: ('COFFEE', 'Private', '12 OZ', 4.50, 0.0, 0.0, 3, 1.40),
    108: ('FROZEN PIZZA', 'National', '14 OZ', 1.00, 0.0, 0.0, 1, 1.00),
    110: ('CANDY - CHECKLANE', 'National', '8 OZ', 1.00, 0.0, 0.0, 1, 1.00),
    # 111 is overcharged 100c (above every sampled tolerance) AND covered-but-undiscounted,
    # so it sits in both approve pools and lets two claims about one line both approve
    111: ('BEEF', 'National', '1 LB', 3.00, 0.0, 0.0, 1, 2.00),
}
HISTORY = (109, 'SOFT DRINKS', 'National', '2 LT')
ANCHOR_DAYS = (240, 247, 253)

SPLITS = Splits(
    train=SplitSpec('train', frozenset({2}), 33, 38),
    dev=SplitSpec('dev', frozenset({1}), 33, 38),
    eval_unseen=SplitSpec('eval_unseen', frozenset({1}), 33, 38),
    eval_known=SplitSpec('eval_known', frozenset({2}), 33, 38),
    heldout_commodities=frozenset(),
)

SIX_KIND_CFG = TaskConfig(claims_per_anchor=6)
OOW_CFG = TaskConfig(out_of_window_anchor_rate=1.0)
STATED_CFG = TaskConfig(stated_number_prob=1.0)
PAIR_CFG = TaskConfig(same_line_claim_prob=1.0)


@dataclass(frozen=True, slots=True)
class MiniWorld:
    ctx: RefundContext
    txc: pd.DataFrame
    prices: dict[tuple[int, int], PricePoint]
    coupons: CouponIndex


@pytest.fixture(scope='module')
def world() -> MiniWorld:
    products = [
        Product.model_validate(
            {
                'PRODUCT_ID': pid,
                'MANUFACTURER': 1,
                'DEPARTMENT': 'GROCERY',
                'BRAND': spec[1],
                'COMMODITY_DESC': spec[0],
                'SUB_COMMODITY_DESC': 'MISC',
                'CURR_SIZE_OF_PRODUCT': spec[2],
            }
        )
        for pid, spec in {**PRODUCT_SPECS, HISTORY[0]: HISTORY[1:4]}.items()
    ]
    tx = pd.DataFrame(_rows())
    txc, _ = prepare_transactions(tx, products, CleaningConfig())
    sizes = pd.DataFrame(
        {
            'product_id': [p.product_id for p in products],
            'size': [p.size for p in products],
        }
    )
    txc = txc.merge(sizes, left_on='PRODUCT_ID', right_on='product_id').drop(columns='product_id')
    prices = build_price_table(txc, PricingConfig())
    campaigns = (
        Campaign.model_validate(
            {'DESCRIPTION': 'TypeA', 'CAMPAIGN': 10, 'START_DAY': 230, 'END_DAY': 260}
        ),
    )
    coupons = build_coupon_index(
        [
            CouponEligibility.model_validate(
                {'COUPON_UPC': upc, 'PRODUCT_ID': pid, 'CAMPAIGN': 10}
            )
            for upc, pid in ((5001, 104), (5002, 106), (5003, 110), (5004, 111))
        ],
        list(campaigns),
        [
            CampaignTargeting.model_validate(
                {'DESCRIPTION': 'TypeA', 'household_key': hh, 'CAMPAIGN': 10}
            )
            for hh in (1, 2)
        ],
        [],
        txc,
        min_redemptions=2,
    )
    ctx = build_refund_context(txc, prices, coupons, SPLITS, campaigns, TaskConfig())
    return MiniWorld(ctx=ctx, txc=txc, prices=prices, coupons=coupons)


def _row(
    household: int,
    basket: int,
    day: int,
    product_id: int,
    sales: float,
    retail: float,
    coupon: float,
    quantity: int,
) -> dict[str, object]:
    return {
        'household_key': household,
        'BASKET_ID': basket,
        'DAY': day,
        'PRODUCT_ID': product_id,
        'QUANTITY': quantity,
        'SALES_VALUE': sales,
        'STORE_ID': 364,
        'RETAIL_DISC': retail,
        'TRANS_TIME': 1200,
        'WEEK_NO': (day - 1) // 7 + 1,
        'COUPON_DISC': coupon,
        'COUPON_MATCH_DISC': 0.0,
    }


def _rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for household, base in ((1, 1000), (2, 2000)):
        for i, day in enumerate(ANCHOR_DAYS):
            for pid, spec in PRODUCT_SPECS.items():
                rows.append(
                    _row(household, base + i + 1, day, pid, spec[3], spec[4], spec[5], spec[6])
                )
        rows.append(_row(household, base + 900, 220, HISTORY[0], 1.00, 0.0, 0.0, 1))
    for day in ANCHOR_DAYS:
        for household in (3, 4):
            for pid, spec in PRODUCT_SPECS.items():
                rows.append(
                    _row(
                        household,
                        3000 + household * 10 + day,
                        day - 1,
                        pid,
                        spec[7],
                        0.0,
                        0.0,
                        1,
                    )
                )
    return rows


async def _rendered(
    ctx: RefundContext, split: str, n: int, seed: int, text: FakeTextModel | None = None
) -> tuple[tuple[RefundInstance, ...], ...]:
    """Plan, render with the well-behaved fake, and finalize every plan that passes."""
    batch = plan_batch(ctx, split, n, seed)
    text = text or FakeTextModel()
    anchors = []
    for index, plan in enumerate(batch.plans):
        outcome = await render_anchor(
            plan.lines,
            [claim_spec(claim) for claim in plan.claims],
            text,
            'writer',
            ('v1',),
        )
        if outcome.ok:
            anchors.append(finalize_anchor(plan, index, outcome.references, outcome.sentences))
    return tuple(anchors)


_BATCHES: dict[str, tuple[tuple[RefundInstance, ...], ...]] = {}


async def _batches(world: MiniWorld) -> dict[str, tuple[tuple[RefundInstance, ...], ...]]:
    for name, ctx, split, seed in (
        ('dev', world.ctx, 'dev', 11),
        ('train', world.ctx, 'train', 12),
        ('six_kind', replace(world.ctx, cfg=SIX_KIND_CFG), 'dev', 13),
        ('out_of_window', replace(world.ctx, cfg=OOW_CFG), 'dev', 14),
        ('stated', replace(world.ctx, cfg=STATED_CFG), 'dev', 16),
    ):
        if name not in _BATCHES:
            _BATCHES[name] = await _rendered(ctx, split, 3, seed)
    return _BATCHES


@pytest.mark.anyio
async def test_truth_matches_recomputation_from_raw_transactions(world: MiniWorld):
    checked = 0
    for batch in (await _batches(world)).values():
        for anchor in batch:
            inst = anchor[-1]
            base = [_expected(claim, inst, world) for claim in inst.claims]
            refunds = allocate_refunds(
                [
                    ClaimVerdict(Decision(decision), claim.truth_line, refund)
                    for claim, (decision, _, refund) in zip(inst.claims, base, strict=True)
                ],
                inst.policy,
            )
            for claim, (decision, reason, refund), allocated in zip(
                inst.claims, base, refunds, strict=True
            ):
                assert (
                    claim.truth_decision.value,
                    claim.truth_reason.value,
                    claim.truth_refund_cents,
                ) == (decision, reason, allocated)
                checked += 1
    assert checked >= 30


def _expected(claim: Claim, inst: RefundInstance, world: MiniWorld) -> tuple[str, str, int]:
    """Hand-written spec adjudication straight off the cleaned transactions and price table."""
    if inst.claim_day - inst.purchase_day > inst.policy.claim_window_days:
        return ('reject', 'OUTSIDE_WINDOW', 0)
    if claim.truth_line is None:
        if claim.reference_kind == 'clarify':
            return ('reject', 'NEEDS_CLARIFICATION', 0)
        return ('reject', 'NOT_ON_RECEIPT', 0)
    line = next(item for item in inst.lines if item.code == claim.truth_line)
    row = world.txc[
        (world.txc['BASKET_ID'] == inst.basket) & (world.txc['PRODUCT_ID'] == line.product_id)
    ].iloc[0]
    point = world.prices[(line.product_id, int(row['WEEK_NO']))]
    reference = point.shelf_cents - point.loyalty_disc_cents
    loyalty_unit = int(round(float(row['loyalty_unit']) * 100))
    quantity = int(row['QUANTITY'])
    coupon_disc_unit = int(
        round(-float(row['COUPON_DISC'] + row['COUPON_MATCH_DISC']) / quantity * 100)
    )
    if claim.stated_type is StatedType.PRICE:
        if inst.policy.price_match_national_only and line.brand_tier.value != 'National':
            return ('reject', 'NOT_ELIGIBLE', 0)
        if loyalty_unit - reference > inst.policy.price_tolerance_cents:
            paid_unit = loyalty_unit - coupon_disc_unit
            return (
                'approve',
                'PRICE_MATCH',
                min((loyalty_unit - reference) * quantity, paid_unit * quantity),
            )
        return ('reject', 'WITHIN_TOLERANCE', 0)
    covered = world.coupons.product_upcs.get(line.product_id, frozenset()) & live_upcs(
        world.coupons, inst.household, inst.purchase_day
    )
    if not covered:
        return ('reject', 'NOT_ELIGIBLE', 0)
    if coupon_disc_unit != 0:
        return ('reject', 'ALREADY_APPLIED', 0)
    return ('approve', 'MISSED_COUPON', max(typical_value(world.coupons, u)[0] for u in covered))


@pytest.mark.anyio
async def test_claims_match_their_reference_kinds(world: MiniWorld):
    for batch in (await _batches(world)).values():
        for anchor in batch:
            inst = anchor[-1]
            codes = {line.code for line in inst.lines}
            sentences = split_sentences(inst.message)
            assert len(sentences) == len(inst.claims)
            for claim in inst.claims:
                if claim.reference_kind == 'unique':
                    assert claim.truth_line in codes
                    assert claim.stated_number == (claim.stated_cents is not None)
                elif claim.reference_kind == 'clarify':
                    assert (
                        claim.truth_line,
                        claim.truth_reason.value,
                        claim.truth_refund_cents,
                        claim.stated_cents,
                    ) == (None, 'NEEDS_CLARIFICATION', 0, None)
                else:
                    assert (
                        claim.truth_line,
                        claim.truth_reason.value,
                        claim.reference_kind,
                    ) == (None, 'NOT_ON_RECEIPT', 'absent')


def test_missing_item_claims_come_from_household_history(world: MiniWorld):
    for plan in plan_batch(world.ctx, 'dev', 3, 11).plans:
        receipt_categories = {line.commodity for line in plan.lines}
        history = world.ctx.tx[
            (world.ctx.tx['household_key'] == plan.household)
            & (world.ctx.tx['DAY'] < plan.purchase_day)
        ]
        history_categories = {str(c) for c in history['commodity'].unique()}
        for claim in plan.claims:
            if claim.kind == 'absent':
                assert claim.absent_item in history_categories - receipt_categories


def test_clarify_targets_share_one_category(world: MiniWorld):
    seen = 0
    for plan in plan_batch(replace(world.ctx, cfg=SIX_KIND_CFG), 'dev', 3, 13).plans:
        by_code = {line.code: line for line in plan.lines}
        for claim in plan.claims:
            if claim.kind != 'clarify':
                continue
            seen += 1
            commodities = {by_code[code].commodity for code in claim.target_lines}
            assert len(claim.target_lines) >= 2 and len(commodities) == 1
    assert seen >= 1


@pytest.mark.anyio
async def test_nested_levels_prefix_claims_and_messages(world: MiniWorld):
    l1, l2, l3 = (await _batches(world))['dev'][0]
    sentences = split_sentences(l3.message)
    assert {
        'prefix': (l1.claims, l2.claims) == (l3.claims[:1], l3.claims[:2]),
        'messages': (l1.message, l2.message) == (' '.join(sentences[:1]), ' '.join(sentences[:2])),
        'same_receipt': (l1.lines, l1.coupons, l1.purchase_day, l1.claim_day, l1.policy)
        == (l3.lines, l3.coupons, l3.purchase_day, l3.claim_day, l3.policy),
        'ids': [i.instance_id for i in (l1, l2, l3)],
        'anchor_ids': {i.anchor_id for i in (l1, l2, l3)},
        'levels': [i.level for i in (l1, l2, l3)],
    } == {
        'prefix': True,
        'messages': True,
        'same_receipt': True,
        'ids': ['dev-L1-0000', 'dev-L2-0000', 'dev-L3-0000'],
        'anchor_ids': {'dev-0000'},
        'levels': ['L1', 'L2', 'L3'],
    }


@pytest.mark.anyio
async def test_out_of_window_anchors_reject_every_claim(world: MiniWorld):
    for anchor in (await _batches(world))['out_of_window']:
        inst = anchor[-1]
        gap = inst.claim_day - inst.purchase_day
        window = inst.policy.claim_window_days
        assert {
            'flag': inst.is_out_of_window,
            'gap_in_range': window < gap <= window + 30,
            'reasons': {c.truth_reason.value for c in inst.claims},
            'stated': {c.stated_type for c in inst.claims}
            <= {StatedType.PRICE, StatedType.COUPON},
        } == {
            'flag': True,
            'gap_in_range': True,
            'reasons': {'OUTSIDE_WINDOW'},
            'stated': True,
        }


def test_out_of_window_positions_spread_across_the_plan():
    # the render stage keeps the first surviving anchors, so a tail-only stratum would be
    # cut whenever discards eat the surplus; positions must interleave the whole range
    positions = _spread_positions(150, 22)
    assert {
        'count': len(positions),
        'early': len([p for p in positions if p < 100]) >= 14,
        'deterministic': positions == _spread_positions(150, 22),
        'all': _spread_positions(3, 3) == frozenset({0, 1, 2}),
        'none': _spread_positions(5, 0) == frozenset(),
    } == {'count': 22, 'early': True, 'deterministic': True, 'all': True, 'none': True}


def test_planning_is_deterministic(world: MiniWorld):
    first = plan_batch(world.ctx, 'dev', 3, 11)
    second = plan_batch(world.ctx, 'dev', 3, 11)
    assert first.plans == second.plans


@pytest.mark.anyio
async def test_price_claims_reproduce_refunds_from_displayed_columns(world: MiniWorld):
    for anchor in (await _batches(world))['dev']:
        for inst in anchor:
            for claim in inst.claims:
                if claim.stated_type is not StatedType.PRICE or claim.truth_line is None:
                    continue
                line = next(item for item in inst.lines if item.code == claim.truth_line)
                diff = line.loyalty_unit_cents - line.reference_cents
                base = min(diff, line.paid_unit_cents) * line.quantity
                cap = inst.policy.refund_cap_cents
                # L1 is a single claim, so its refund is the base clamped by the cap alone;
                # deeper prefixes can additionally lose money to same-line dedup
                assert {
                    'integer_qty': isinstance(line.quantity, int) and line.quantity >= 1,
                    'refund_l1': inst.level != 'L1'
                    or claim.truth_refund_cents == min(base, cap if cap is not None else base),
                    'refund_bounded': claim.truth_refund_cents <= base,
                    'within_tolerance_bounds': (diff > inst.policy.price_tolerance_cents)
                    == (claim.truth_reason.value == 'PRICE_MATCH'),
                } == {
                    'integer_qty': True,
                    'refund_l1': True,
                    'refund_bounded': True,
                    'within_tolerance_bounds': True,
                }


@pytest.mark.anyio
async def test_stated_numbers_contradict_the_displayed_values(world: MiniWorld):
    quoted = 0
    for anchor in (await _batches(world))['stated']:
        inst = anchor[-1]
        for claim in inst.claims:
            if not claim.stated_number:
                continue
            assert claim.stated_cents is not None
            assert f'${claim.stated_cents / 100:.2f}' in inst.message
            line = next(item for item in inst.lines if item.code == claim.truth_line)
            if claim.stated_type is StatedType.COUPON:
                values = [
                    coupon.typical_value_cents
                    for coupon in inst.coupons
                    if claim.truth_line in coverage_of(coupon.coverage, inst.lines)
                ]
                assert values and claim.stated_cents not in values
            else:
                assert claim.stated_cents not in {
                    line.paid_unit_cents,
                    line.loyalty_unit_cents,
                    line.regular_unit_cents,
                    line.reference_cents,
                }
            quoted += 1
    assert quoted >= 3


@pytest.mark.anyio
async def test_paired_claims_on_one_line_pay_only_the_first(world: MiniWorld):
    pairs = approve_pairs = 0
    for seed in range(12):
        for anchor in await _rendered(replace(world.ctx, cfg=PAIR_CFG), 'dev', 3, seed):
            claims = anchor[-1].claims
            if len(claims) < 2 or claims[0].truth_line != claims[1].truth_line:
                continue
            pairs += 1
            if (
                claims[0].truth_decision is Decision.APPROVE
                and claims[1].truth_decision is Decision.APPROVE
            ):
                approve_pairs += 1
                assert claims[1].truth_refund_cents == 0
    assert pairs >= 1 and approve_pairs >= 1


@pytest.mark.anyio
async def test_coupon_coverage_text_selects_exactly_the_covered_lines(world: MiniWorld):
    # coupon ids follow sorted kept UPCs: 5001->yogurt, 5002->cheese, 5003->candy, 5004->beef
    upc_products = {5001: {104}, 5002: {106}, 5003: {110}, 5004: {111}}
    for anchor in (await _batches(world))['dev']:
        inst = anchor[-1]
        assert [c.coupon_id for c in inst.coupons] == ['C01', 'C02', 'C03', 'C04']
        for coupon, upc in zip(inst.coupons, (5001, 5002, 5003, 5004), strict=True):
            expected = tuple(
                line.code for line in inst.lines if line.product_id in upc_products[upc]
            )
            assert coverage_of(coupon.coverage, inst.lines) == expected
