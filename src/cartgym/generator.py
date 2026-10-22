from collections.abc import Iterator, Mapping
from dataclasses import asdict, dataclass, replace
from typing import Literal

import numpy as np
import pandas as pd
from loguru import logger
from pydantic import BaseModel, ConfigDict

from cartgym.config import LevelConfig, LevelsConfig
from cartgym.data.load import Product
from cartgym.data.prices import PricePoint
from cartgym.data.splits import CampaignCalendar, Splits, SplitSpec
from cartgym.instance import (
    BrandQuota,
    BrandTier,
    Constraint,
    Coupon,
    Instance,
    LoyalSKU,
    ManufacturerMultiBuy,
    MenuSKU,
    SkuCoupon,
    ThresholdBundle,
    is_feasible,
)
from cartgym.pricing import cost, sku_net_cents
from cartgym.solver import Solution, optimal_cart, solve

CODE_LETTERS = 'ABCDEFGHJKLMNPQRSTUVWXYZ'
DEFAULT_PRIVATE_SHARE = 0.28


@dataclass(frozen=True, slots=True)
class AnchorLine:
    commodity: str
    sub_commodity: str
    product_id: int
    week: int
    pool_size: int


@dataclass(frozen=True, slots=True)
class GeneratedInstance:
    instance: Instance
    info: dict[str, object]


@dataclass(frozen=True, slots=True)
class InstanceStats:
    accept: bool
    reject_reason: str | None
    is_trap: bool
    greedy_cost_cents: int
    greedy_feasible: bool
    greedy_gap_cents: int
    n_feasible: int
    n_optimal: int
    binding_rules: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class BatchResult:
    instances: tuple[GeneratedInstance, ...]
    stats: dict[str, int]


@dataclass(frozen=True, slots=True)
class GeneratorContext:
    tx: pd.DataFrame  # cleaned transactions with product attributes and unit prices
    products: dict[int, Product]
    prices: dict[tuple[int, int], PricePoint]
    calendar: CampaignCalendar
    eligibility: dict[int, set[int]]  # product_id -> campaign ids
    targeting: dict[int, set[int]]  # household_key -> campaign ids
    coupon_amounts_cents: np.ndarray
    splits: Splits
    cfg: LevelsConfig
    baskets: pd.DataFrame  # BASKET_ID, household_key, DAY, WEEK_NO
    menu_pools: dict[tuple[str, int], tuple[int, ...]]  # (sub_commodity, week) -> priced products
    pool_sizes: pd.DataFrame  # sub_commodity, WEEK_NO, pool_size
    history: dict[int, tuple[np.ndarray, np.ndarray]]  # household -> (sorted days, private flags)


def build_generator_context(
    tx: pd.DataFrame,
    products: list[Product],
    prices: dict[tuple[int, int], PricePoint],
    calendar: CampaignCalendar,
    eligibility: dict[int, set[int]],
    targeting: dict[int, set[int]],
    coupon_amounts_cents: np.ndarray,
    splits: Splits,
    cfg: LevelsConfig,
) -> GeneratorContext:
    """Assemble the immutable context that all generation batches share."""
    products_by_id = {p.product_id: p for p in products}
    assert len(products_by_id) == len(products), 'duplicate product ids in the product table'
    pools: dict[tuple[str, int], list[int]] = {}
    for product_id, week in prices:
        pools.setdefault((products_by_id[product_id].sub_commodity, week), []).append(product_id)
    menu_pools = {key: tuple(sorted(value)) for key, value in pools.items()}
    pool_sizes = pd.DataFrame(
        [
            {'sub_commodity': sub, 'WEEK_NO': week, 'pool_size': len(pids)}
            for (sub, week), pids in menu_pools.items()
        ]
    )
    baskets = (
        tx.groupby('BASKET_ID')
        .agg(
            household_key=('household_key', 'first'),
            DAY=('DAY', 'first'),
            WEEK_NO=('WEEK_NO', 'first'),
        )
        .reset_index()
    )
    return GeneratorContext(
        tx=tx,
        products=products_by_id,
        prices=prices,
        calendar=calendar,
        eligibility=eligibility,
        targeting=targeting,
        coupon_amounts_cents=np.asarray(coupon_amounts_cents, dtype=np.int64),
        splits=splits,
        cfg=cfg,
        baskets=baskets,
        menu_pools=menu_pools,
        pool_sizes=pool_sizes,
        history=_household_history(tx),
    )


def private_share_before(
    history: dict[int, tuple[np.ndarray, np.ndarray]], household: int, day: int
) -> float | None:
    """Household private-label share over its transactions strictly before `day`."""
    days, flags = history.get(household, (np.array([], dtype=np.int64), np.array([], dtype=bool)))
    cutoff = int(np.searchsorted(days, day, side='left'))
    if cutoff == 0:
        return None
    return float(flags[:cutoff].mean())


def generate_batch(
    ctx: GeneratorContext, level_name: str, split_name: str, n: int, seed: int
) -> BatchResult:
    """Generate n accepted instances for one level and split, deduped and trap-rate sampled."""
    level = ctx.cfg.levels[level_name]
    spec = ctx.splits.spec(split_name)
    rng = np.random.default_rng(seed)
    pool = _anchor_pool(ctx, spec)
    lines_by_basket = _anchor_lines(ctx, pool)
    basket_ids = np.array(sorted(lines_by_basket), dtype=np.int64)
    assert len(basket_ids) > 0, (
        f'{spec.name} has no baskets that can feed a level-{level_name} instance'
    )
    facts = {
        int(basket): (int(household), int(day), int(week))
        for basket, household, day, week in zip(
            pool['BASKET_ID'].to_numpy(),
            pool['household_key'].to_numpy(),
            pool['DAY'].to_numpy(),
            pool['WEEK_NO'].to_numpy(),
            strict=True,
        )
        if int(basket) in lines_by_basket
    }
    logger.info(
        '{}/{}: {} anchor baskets ({} pass the menu-size filter)',
        split_name,
        level_name,
        len(pool),
        len(basket_ids),
    )
    needs = {'trap': round(n * ctx.cfg.trap_rate), 'plain': n - round(n * ctx.cfg.trap_rate)}
    stats: dict[str, int] = {
        'attempts': 0,
        'dup_anchor': 0,
        'dup_fingerprint': 0,
        'stratum_full': 0,
    }
    used: set[int] = set()
    fingerprints: set[tuple[object, ...]] = set()
    accepted: list[GeneratedInstance] = []
    for attempt in range(50 * n + 200):
        if needs['trap'] == 0 and needs['plain'] == 0:
            break
        stats['attempts'] += 1
        basket = int(basket_ids[rng.integers(len(basket_ids))])
        if basket in used:
            stats['dup_anchor'] += 1
            continue
        generated, reason = _build_instance(
            ctx,
            level,
            level_name,
            spec.name,
            basket,
            facts[basket],
            lines_by_basket[basket],
            rng,
            attempt,
        )
        if generated is None:
            reason = reason or 'rejected'
            stats[reason] = stats.get(reason, 0) + 1
            continue
        key = _fingerprint(generated.instance)
        if key in fingerprints:
            stats['dup_fingerprint'] += 1
            continue
        stratum = 'trap' if generated.info['is_trap'] else 'plain'
        if needs[stratum] == 0:
            stats['stratum_full'] += 1
            continue
        needs[stratum] -= 1
        used.add(basket)
        fingerprints.add(key)
        accepted.append(generated)
    missing = needs['trap'] + needs['plain']
    if missing:
        raise RuntimeError(
            f'could not fill {split_name}/{level_name}: {missing} missing'
            f' after {stats["attempts"]} attempts; {stats}'
        )
    logger.info('{}/{}: {} accepted, stats={}', split_name, level_name, len(accepted), stats)
    return BatchResult(tuple(accepted), stats)


def greedy_cheapest_cart(instance: Instance) -> dict[str, str]:
    """Cheapest-net SKU per category, ignoring coupons and constraints."""
    return {c: min(instance.menu[c], key=sku_net_cents).code for c in instance.commodities}


def evaluate_instance(
    instance: Instance, solution: Solution, greedy: dict[str, str], cfg: LevelsConfig
) -> InstanceStats:
    """Acceptance filters, trap tagging, and binding-rule detection for one solved instance."""
    if solution.n_feasible == 0:
        return InstanceStats(False, 'no_feasible_cart', True, 0, False, 0, 0, 0, ())
    c_star = solution.c_star_cents()
    optimal_mask = solution.feasible & (solution.costs_cents <= c_star + cfg.tie_eps_cents)
    n_optimal = int(optimal_mask.sum())
    non_optimal = solution.costs_cents[solution.feasible & ~optimal_mask]
    greedy_cost = cost(greedy, instance).total_cents
    greedy_ok = is_feasible(greedy, instance)
    is_trap = (not greedy_ok) or greedy_cost > c_star + cfg.tie_eps_cents
    gap = greedy_cost - c_star
    if len(non_optimal) == 0:
        return InstanceStats(
            False,
            'all_carts_tie',
            is_trap,
            greedy_cost,
            greedy_ok,
            gap,
            solution.n_feasible,
            n_optimal,
            (),
        )
    if int(non_optimal.min()) - c_star <= cfg.near_tie_delta_cents:
        return InstanceStats(
            False,
            'near_tie',
            is_trap,
            greedy_cost,
            greedy_ok,
            gap,
            solution.n_feasible,
            n_optimal,
            (),
        )
    binding = _binding_rules(instance, solution, cfg)
    return InstanceStats(
        True, None, is_trap, greedy_cost, greedy_ok, gap, solution.n_feasible, n_optimal, binding
    )


def _anchor_pool(ctx: GeneratorContext, spec: SplitSpec) -> pd.DataFrame:
    """Split baskets whose day has a live campaign (coupons must be attachable)."""
    live = ctx.calendar.live_days()
    pool = ctx.baskets[
        ctx.baskets['household_key'].isin(spec.households)
        & ctx.baskets['WEEK_NO'].between(spec.first_week, spec.last_week)
        & ctx.baskets['DAY'].isin(live)
    ]
    assert len(pool) > 0, f'{spec.name} has no campaign-live anchor baskets'
    return pool


def _anchor_lines(ctx: GeneratorContext, pool: pd.DataFrame) -> dict[int, tuple[AnchorLine, ...]]:
    """Pool baskets' lines with menu-pool size, kept when they can feed the largest level."""
    lines = ctx.tx[ctx.tx['BASKET_ID'].isin(pool['BASKET_ID'])]
    merged = lines.merge(ctx.pool_sizes, on=['sub_commodity', 'WEEK_NO'], how='left')
    merged['pool_size'] = merged['pool_size'].fillna(0).astype('int64')
    merged = merged.sort_values('BASKET_ID')
    grouped: dict[int, list[AnchorLine]] = {}
    for basket, commodity, sub, product_id, week, size in zip(
        merged['BASKET_ID'].to_numpy(),
        merged['commodity'].to_numpy(),
        merged['sub_commodity'].to_numpy(),
        merged['PRODUCT_ID'].to_numpy(),
        merged['WEEK_NO'].to_numpy(),
        merged['pool_size'].to_numpy(),
        strict=True,
    ):
        grouped.setdefault(int(basket), []).append(
            AnchorLine(str(commodity), str(sub), int(product_id), int(week), int(size))
        )
    min_s = min(level.skus_per_category for level in ctx.cfg.levels.values())
    max_c = max(level.categories for level in ctx.cfg.levels.values())
    feasible: dict[int, tuple[AnchorLine, ...]] = {}
    for basket, basket_lines in grouped.items():
        ok = [line for line in basket_lines if line.pool_size >= min_s]
        if len({line.commodity for line in ok}) >= max_c:
            feasible[basket] = tuple(ok)
    return feasible


def _build_instance(
    ctx: GeneratorContext,
    level: LevelConfig,
    level_name: str,
    split_name: str,
    basket: int,
    facts: tuple[int, int, int],
    lines: tuple[AnchorLine, ...],
    rng: np.random.Generator,
    attempt: int,
) -> tuple[GeneratedInstance | None, str | None]:
    """One candidate instance from an anchor basket, or a reject reason."""
    household, day, week = facts
    chosen = _choose_categories(lines, level, ctx.splits.heldout_commodities, rng)
    if chosen is None:
        return None, 'too_few_categories'
    codes = iter(_draw_codes(level.categories * level.skus_per_category, rng))
    menu: dict[str, tuple[MenuSKU, ...]] = {}
    bought_code: dict[str, str] = {}
    for commodity, anchor in chosen:
        skus, bought = _build_menu(ctx, anchor, level.skus_per_category, rng, codes)
        menu[commodity] = skus
        bought_code[commodity] = bought
    coupons, provenance, requested = _draw_coupons(ctx, level, menu, day, household, rng)
    constraints = _draw_constraints(ctx, level, menu, household, day)
    instance = Instance(tuple(menu), menu, coupons, constraints)
    solution = solve(instance)
    greedy = greedy_cheapest_cart(instance)
    stats = evaluate_instance(instance, solution, greedy, ctx.cfg)
    if not stats.accept:
        return None, stats.reject_reason
    real = cost(bought_code, instance)
    info: dict[str, object] = {
        'instance_id': f'{split_name}-{level_name}-{attempt}',
        'split': split_name,
        'level': level_name,
        'household': household,
        'basket': basket,
        'day': day,
        'week': week,
        'n_carts': solution.n_carts,
        'n_feasible': stats.n_feasible,
        'n_optimal': stats.n_optimal,
        'c_star_cents': solution.c_star_cents(),
        'greedy_cost_cents': stats.greedy_cost_cents,
        'greedy_feasible': stats.greedy_feasible,
        'greedy_gap_cents': stats.greedy_gap_cents,
        'is_trap': stats.is_trap,
        'binding_rules': list(stats.binding_rules),
        'coupons_requested': requested,
        'coupons_drawn': len(coupons),
        'coupon_provenance': provenance,
        'real_cart_codes': dict(bought_code),
        'real_cart_cost_cents': real.total_cents,
        'real_cart_feasible': is_feasible(bought_code, instance),
        'menu_scope': {commodity: anchor.sub_commodity for commodity, anchor in chosen},
        'bought_products': {commodity: anchor.product_id for commodity, anchor in chosen},
    }
    return GeneratedInstance(instance, info), None


def _draw_codes(n: int, rng: np.random.Generator) -> list[str]:
    """Neutral short codes (e.g. 'K7') in random order; no code encodes category or position."""
    pool = [f'{letter}{digit}' for letter in CODE_LETTERS for digit in range(10)]
    picked = rng.choice(len(pool), size=n, replace=False)
    return [pool[int(i)] for i in picked]


def _choose_categories(
    lines: tuple[AnchorLine, ...],
    level: LevelConfig,
    heldout: frozenset[str],
    rng: np.random.Generator,
) -> list[tuple[str, AnchorLine]] | None:
    by_commodity: dict[str, list[AnchorLine]] = {}
    for line in lines:
        if line.pool_size >= level.skus_per_category and line.commodity not in heldout:
            by_commodity.setdefault(line.commodity, []).append(line)
    if len(by_commodity) < level.categories:
        return None
    commodities = rng.choice(sorted(by_commodity), size=level.categories, replace=False)
    return [
        (str(name), by_commodity[str(name)][int(rng.integers(len(by_commodity[str(name)])))])
        for name in commodities
    ]


def _build_menu(
    ctx: GeneratorContext,
    anchor: AnchorLine,
    s: int,
    rng: np.random.Generator,
    code_iter: Iterator[str],
) -> tuple[tuple[MenuSKU, ...], str]:
    """S SKUs from the anchor's sub-commodity; includes the bought product, tier-mixed."""
    pool = ctx.menu_pools[(anchor.sub_commodity, anchor.week)]
    bought_tier = ctx.products[anchor.product_id].brand
    others = [p for p in pool if p != anchor.product_id]
    opposite = [p for p in others if ctx.products[p].brand is not bought_tier]
    picked: list[int] = []
    if s >= 2 and opposite:
        picked.append(int(rng.choice(opposite)))
    while len(picked) < s - 1:
        remaining = [p for p in others if p not in picked]
        assert remaining, (
            f'menu pool for {(anchor.sub_commodity, anchor.week)} smaller than configured'
        )
        picked.append(int(rng.choice(remaining)))
    products_picked = picked + [anchor.product_id]
    rng.shuffle(products_picked)  # menu order must not reveal the bought item
    skus = []
    for product_id in products_picked:
        product = ctx.products[product_id]
        price = ctx.prices[(product_id, anchor.week)]
        skus.append(
            MenuSKU(
                code=next(code_iter),
                product_id=product_id,
                commodity=anchor.commodity,
                brand_tier=product.brand,
                manufacturer=product.manufacturer,
                size=product.size,
                shelf_cents=price.shelf_cents,
                loyalty_disc_cents=price.loyalty_disc_cents,
            )
        )
    bought = next(sku.code for sku in skus if sku.product_id == anchor.product_id)
    return tuple(skus), bought


def _draw_coupons(
    ctx: GeneratorContext,
    level: LevelConfig,
    menu: dict[str, tuple[MenuSKU, ...]],
    day: int,
    household: int,
    rng: np.random.Generator,
) -> tuple[tuple[Coupon, ...], dict[str, str], int]:
    """Fixed coupon count per level: real eligibility preferred, synthetic-tagged fallback."""
    all_skus = [sku for skus in menu.values() for sku in skus]
    n_sku = (
        int(rng.integers(level.sku_coupons[0], level.sku_coupons[1] + 1))
        if level.sku_coupons[1] > 0
        else 0
    )
    requested = n_sku + level.threshold_bundles
    if requested == 0:
        return (), {}, 0
    amounts = [int(rng.choice(ctx.coupon_amounts_cents)) for _ in range(requested)]
    min_base = sum(min(sku_net_cents(sku) for sku in skus) for skus in menu.values())
    amounts = _fit_amounts(amounts, min_base)
    sku_amounts, bundle_amounts = amounts[:n_sku], amounts[n_sku:]
    coupons: list[Coupon] = []
    provenance: dict[str, str] = {}
    real_codes = _real_eligible_codes(ctx, all_skus, day, household)
    used_codes: set[str] = set()
    for amount in sku_amounts:
        candidates = [code for code in real_codes if code not in used_codes]
        if candidates:
            code, tag = str(rng.choice(candidates)), 'real'
        else:
            code, tag = (
                str(rng.choice([sku.code for sku in all_skus if sku.code not in used_codes])),
                'synthetic',
            )
        used_codes.add(code)
        coupon_id = f'K{len(coupons)}'
        coupons.append(SkuCoupon(coupon_id, code, amount))
        provenance[coupon_id] = tag
    _cap_coupon_amounts(coupons, menu, level, ctx.cfg, rng)
    commodities = sorted(menu)
    for amount in bundle_amounts:
        if len(commodities) < 2:
            break
        pair = [str(c) for c in rng.choice(commodities, size=2, replace=False)]
        nets = [[sku_net_cents(sku) for sku in menu[c]] for c in pair]
        cheapest, largest = sum(min(n) for n in nets), sum(max(n) for n in nets)
        if cheapest >= largest:
            continue  # identical prices: no threshold can couple anything
        threshold = int(rng.integers(cheapest + 1, largest + 1))
        coupon_id = f'K{len(coupons)}'
        coupons.append(ThresholdBundle(coupon_id, (pair[0], pair[1]), threshold, amount))
        provenance[coupon_id] = 'synthetic'
    return tuple(coupons), provenance, requested


def _real_eligible_codes(
    ctx: GeneratorContext, skus: list[MenuSKU], day: int, household: int
) -> list[str]:
    """Menu codes with live-campaign coupon eligibility; campaigns targeting the household win."""
    live = {c.campaign for c in ctx.calendar.live_campaigns(day)}
    if not live:
        return []
    targeted = ctx.targeting.get(household, set())
    eligible: list[str] = []
    targeted_eligible: list[str] = []
    for sku in skus:
        campaigns = ctx.eligibility.get(sku.product_id, set()) & live
        if not campaigns:
            continue
        (targeted_eligible if campaigns & targeted else eligible).append(sku.code)
    return targeted_eligible if targeted_eligible else eligible


def _draw_constraints(
    ctx: GeneratorContext,
    level: LevelConfig,
    menu: dict[str, tuple[MenuSKU, ...]],
    household: int,
    day: int,
) -> tuple[Constraint, ...]:
    """Brand quota derived from the household's real history strictly before the target day."""
    if not level.brand_quota:
        return ()
    share = private_share_before(ctx.history, household, day)
    if share is None:
        share = DEFAULT_PRIVATE_SHARE
    tier = BrandTier.PRIVATE if share >= 0.5 else BrandTier.NATIONAL
    tier_share = share if tier is BrandTier.PRIVATE else 1.0 - share
    quota = round(tier_share * len(menu))
    available = sum(1 for skus in menu.values() for sku in skus if sku.brand_tier is tier)
    if quota < 1 or available < 1:
        return ()
    return (BrandQuota(tier, min(quota, available)),)


def _fit_amounts(amounts: list[int], min_base: int) -> list[int]:
    """Shrink coupon amounts so even the cheapest cart cannot price negative."""
    fitted = list(amounts)
    while fitted and sum(fitted) > min_base:
        index = fitted.index(max(fitted))
        room = min_base - (sum(fitted) - fitted[index])
        if room >= 1:
            fitted[index] = room
        else:
            fitted.pop(index)
    return fitted


def _cap_coupon_amounts(
    coupons: list[Coupon],
    menu: dict[str, tuple[MenuSKU, ...]],
    level: LevelConfig,
    cfg: LevelsConfig,
    rng: np.random.Generator,
) -> None:
    """Gap-cap: with prob, shrink a flip-inducing amount so taking the coupon is wrong.

    Without this, amounts drawn from the empirical pool dominate within-menu price gaps, so
    the couponed SKU is almost always cheapest post-coupon and always-coupon-SKU is optimal.
    The cap leaves the couponed SKU above the cheapest alternative by a margin that clears
    the near-tie band, so the acceptance filter keeps the instance.
    """
    if level.coupon_gap_cap_prob <= 0:
        return
    by_code = {sku.code: sku for skus in menu.values() for sku in skus}
    for i, coupon in enumerate(coupons):
        if not isinstance(coupon, SkuCoupon) or rng.random() >= level.coupon_gap_cap_prob:
            continue
        sku = by_code[coupon.code]
        others = [other for other in menu[sku.commodity] if other.code != sku.code]
        gap = sku_net_cents(sku) - min(sku_net_cents(o) for o in others) if others else 0
        if gap <= 0 or coupon.amount_cents < gap:
            continue
        lo, hi = cfg.gap_cap_margin_cents
        margin = int(rng.integers(lo, hi + 1))
        capped = max(1, gap - margin)
        if capped < coupon.amount_cents:
            coupons[i] = replace(coupon, amount_cents=capped)


def _binding_rules(instance: Instance, solution: Solution, cfg: LevelsConfig) -> tuple[str, ...]:
    best = optimal_cart(instance, solution, cfg.tie_eps_cents)
    applied = list(cost(best, instance).applied_coupon_ids)
    by_code = {sku.code: sku for skus in instance.menu.values() for sku in skus}
    for constraint in instance.constraints:
        if isinstance(constraint, BrandQuota):
            count = sum(1 for code in best.values() if by_code[code].brand_tier is constraint.tier)
            if count == constraint.min_count:
                applied.append(f'quota:{constraint.tier.value}')
    return tuple(applied)


def _fingerprint(instance: Instance) -> tuple[object, ...]:
    """Dedupe key: menu products, normalized rules, and constraints (codes excluded)."""
    pid = {sku.code: sku.product_id for skus in instance.menu.values() for sku in skus}
    products = tuple(sorted(pid.values()))
    coupons = tuple(
        sorted(
            ('sku', pid[c.code], c.amount_cents)
            if isinstance(c, SkuCoupon)
            else ('bundle', tuple(sorted(c.commodities)), c.threshold_cents, c.amount_cents)
            if isinstance(c, ThresholdBundle)
            else ('multibuy', c.manufacturer, c.min_items, c.amount_cents)
            for c in instance.coupons
        )
    )
    constraints = tuple(
        sorted(
            ('quota', constraint.tier.value, constraint.min_count)
            if isinstance(constraint, BrandQuota)
            else ('loyal', pid[constraint.code])
            for constraint in instance.constraints
        )
    )
    return (products, coupons, constraints)


def _household_history(tx: pd.DataFrame) -> dict[int, tuple[np.ndarray, np.ndarray]]:
    """Per household: sorted transaction days and Private-brand flags."""
    ordered = tx[['household_key', 'DAY', 'brand']].sort_values('DAY')
    history: dict[int, tuple[np.ndarray, np.ndarray]] = {}
    for household, group in ordered.groupby('household_key'):
        history[int(household)] = (
            group['DAY'].to_numpy(),
            (group['brand'] == 'Private').to_numpy(),
        )
    return history


def instance_to_record(generated: GeneratedInstance) -> dict[str, object]:
    """JSON-ready record of an instance plus its info."""
    instance = generated.instance
    menu = {
        commodity: [asdict(sku) | {'brand_tier': sku.brand_tier.value} for sku in skus]
        for commodity, skus in instance.menu.items()
    }
    coupons = []
    for coupon in instance.coupons:
        record = asdict(coupon) | {'kind': type(coupon).__name__}
        if isinstance(coupon, ThresholdBundle):
            record['commodities'] = list(coupon.commodities)
        coupons.append(record)
    constraints = []
    for constraint in instance.constraints:
        record = asdict(constraint) | {'kind': type(constraint).__name__}
        if isinstance(constraint, BrandQuota):
            record['tier'] = constraint.tier.value
        constraints.append(record)
    return {
        'info': generated.info,
        'instance': {
            'commodities': list(instance.commodities),
            'menu': menu,
            'coupons': coupons,
            'constraints': constraints,
        },
    }


class SkuRecord(BaseModel):
    model_config = ConfigDict(extra='forbid')

    code: str
    product_id: int
    commodity: str
    brand_tier: BrandTier
    manufacturer: int
    size: str
    shelf_cents: int
    loyalty_disc_cents: int


class CouponRecord(BaseModel):
    model_config = ConfigDict(extra='forbid')

    kind: Literal['SkuCoupon', 'ThresholdBundle', 'ManufacturerMultiBuy']
    coupon_id: str
    amount_cents: int
    code: str | None = None
    commodities: tuple[str, ...] | None = None
    threshold_cents: int | None = None
    manufacturer: int | None = None
    min_items: int | None = None


class ConstraintRecord(BaseModel):
    model_config = ConfigDict(extra='forbid')

    kind: Literal['BrandQuota', 'LoyalSKU']
    tier: BrandTier | None = None
    min_count: int | None = None
    code: str | None = None


class InstanceRecord(BaseModel):
    model_config = ConfigDict(extra='forbid')

    commodities: tuple[str, ...]
    menu: dict[str, tuple[SkuRecord, ...]]
    coupons: tuple[CouponRecord, ...] = ()
    constraints: tuple[ConstraintRecord, ...] = ()


def record_to_instance(record: Mapping[str, object]) -> Instance:
    """Rebuild an Instance from its JSONL record (inverse of instance_to_record)."""
    parsed = InstanceRecord.model_validate(record['instance'])
    menu = {
        commodity: tuple(
            MenuSKU(
                code=sku.code,
                product_id=sku.product_id,
                commodity=sku.commodity,
                brand_tier=sku.brand_tier,
                manufacturer=sku.manufacturer,
                size=sku.size,
                shelf_cents=sku.shelf_cents,
                loyalty_disc_cents=sku.loyalty_disc_cents,
            )
            for sku in skus
        )
        for commodity, skus in parsed.menu.items()
    }
    coupons = tuple(_coupon_of(coupon) for coupon in parsed.coupons)
    constraints = tuple(_constraint_of(constraint) for constraint in parsed.constraints)
    return Instance(parsed.commodities, menu, coupons, constraints)


def _coupon_of(record: CouponRecord) -> Coupon:
    match record.kind:
        case 'SkuCoupon':
            assert record.code is not None, f'coupon {record.coupon_id}: missing code'
            return SkuCoupon(record.coupon_id, record.code, record.amount_cents)
        case 'ThresholdBundle':
            assert record.commodities is not None, (
                f'coupon {record.coupon_id}: missing commodities'
            )
            assert record.threshold_cents is not None, (
                f'coupon {record.coupon_id}: missing threshold'
            )
            return ThresholdBundle(
                record.coupon_id, record.commodities, record.threshold_cents, record.amount_cents
            )
        case 'ManufacturerMultiBuy':
            assert record.manufacturer is not None, (
                f'coupon {record.coupon_id}: missing manufacturer'
            )
            assert record.min_items is not None, f'coupon {record.coupon_id}: missing min_items'
            return ManufacturerMultiBuy(
                record.coupon_id, record.manufacturer, record.min_items, record.amount_cents
            )


def _constraint_of(record: ConstraintRecord) -> Constraint:
    match record.kind:
        case 'BrandQuota':
            assert record.tier is not None, 'brand quota record: missing tier'
            assert record.min_count is not None, 'brand quota record: missing min_count'
            return BrandQuota(record.tier, record.min_count)
        case 'LoyalSKU':
            assert record.code is not None, 'loyal SKU record: missing code'
            return LoyalSKU(record.code)


def _int_of(value: object) -> int:
    assert isinstance(value, int), f'expected an int field, got {type(value).__name__}'
    return value


def render_preview(generated: GeneratedInstance) -> str:
    """Human-readable dump of one instance for hand inspection."""
    instance = generated.instance
    info = generated.info
    provenance = (
        dict(info['coupon_provenance']) if isinstance(info['coupon_provenance'], dict) else {}
    )
    lines = [
        f'### {info["instance_id"]} — trap={info["is_trap"]} '
        f'C*=${_int_of(info["c_star_cents"]) / 100:.2f} '
        f'greedy=${_int_of(info["greedy_cost_cents"]) / 100:.2f} '
        f'(gap {info["greedy_gap_cents"]}c)'
    ]
    scope = dict(info['menu_scope']) if isinstance(info['menu_scope'], dict) else {}
    real_codes = dict(info['real_cart_codes']) if isinstance(info['real_cart_codes'], dict) else {}
    for commodity, skus in instance.menu.items():
        lines.append(f'\n**{commodity}** ({scope.get(commodity)})')
        lines.append('| code | brand | mfr | size | shelf | loyalty | net |')
        lines.append('|---|---|---|---|---|---|---|')
        for sku in skus:
            bought = ' ←bought' if real_codes.get(commodity) == sku.code else ''
            lines.append(
                f'| {sku.code} | {sku.brand_tier.value} | {sku.manufacturer} | {sku.size or "—"} '
                f'| ${sku.shelf_cents / 100:.2f} | ${sku.loyalty_disc_cents / 100:.2f} '
                f'| ${sku_net_cents(sku) / 100:.2f}{bought} |'
            )
    for coupon in instance.coupons:
        tag = provenance.get(coupon.coupon_id, 'synthetic')
        match coupon:
            case SkuCoupon(coupon_id=coupon_id, code=code, amount_cents=amount):
                lines.append(f'- coupon {coupon_id}: ${amount / 100:.2f} off SKU {code} ({tag})')
            case ThresholdBundle(
                coupon_id=coupon_id,
                commodities=commodities,
                threshold_cents=threshold,
                amount_cents=amount,
            ):
                names = ', '.join(commodities)
                lines.append(
                    f'- bundle {coupon_id}: ${amount / 100:.2f} off when spend on {names} '
                    f'≥ ${threshold / 100:.2f} ({tag})'
                )
            case ManufacturerMultiBuy(
                coupon_id=coupon_id,
                manufacturer=manufacturer,
                min_items=min_items,
                amount_cents=amount,
            ):
                lines.append(
                    f'- multibuy {coupon_id}: ${amount / 100:.2f} off when buying'
                    f' ≥ {min_items} items from manufacturer {manufacturer} ({tag})'
                )
    for constraint in instance.constraints:
        if isinstance(constraint, BrandQuota):
            lines.append(f'- constraint: ≥ {constraint.min_count} {constraint.tier.value} items')
        else:
            lines.append(f'- constraint: must buy {constraint.code}')
    lines.append(
        f'\n- n_carts={info["n_carts"]}, feasible={info["n_feasible"]},'
        f' optimal={info["n_optimal"]}, binding={info["binding_rules"]}'
    )
    lines.append(
        f'- real cart {real_codes} → ${_int_of(info["real_cart_cost_cents"]) / 100:.2f} '
        f'(feasible={info["real_cart_feasible"]})'
    )
    return '\n'.join(lines)
