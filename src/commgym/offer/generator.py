from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
import pandas as pd
from pydantic import BaseModel

from commgym.dunnhumby.load import Campaign, CampaignTargeting, CouponEligibility, Product
from commgym.dunnhumby.splits import SplitSpec
from commgym.dunnhumby.types import BrandTier
from commgym.offer.config import TaskConfig
from commgym.offer.instance import (
    MIXED,
    OfferCoupon,
    OfferInstance,
    Profile,
    ProfileEntry,
)

CouponKey = tuple[int, int]


@dataclass(frozen=True, slots=True)
class OfferContext:
    targeting: dict[int, frozenset[int]]
    campaign_by_id: dict[int, Campaign]
    campaign_coupons: dict[int, tuple[CouponKey, ...]]
    coupon_coverage: dict[CouponKey, tuple[str, ...]]
    coupon_top: dict[CouponKey, tuple[str, ...]]
    coupon_products: dict[CouponKey, int]
    coupon_tier: dict[CouponKey, str]
    household_frames: dict[int, pd.DataFrame]

    def live_keys(self, household: int, day: int) -> tuple[CouponKey, ...]:
        """All coupon keys of campaigns live on `day` and targeted at `household`."""
        keys: set[CouponKey] = set()
        for campaign in self.targeting.get(household, ()):
            spec = self.campaign_by_id.get(campaign)
            if spec is not None and spec.start_day <= day <= spec.end_day:
                keys.update(self.campaign_coupons.get(campaign, ()))
        return tuple(sorted(keys))

    def live_coupon_counts(self, household: int, first_day: int, last_day: int) -> dict[int, int]:
        """Live targeted coupon count per day in the window; days with none are omitted."""
        span = last_day - first_day + 1
        delta = np.zeros(span + 1, dtype=np.int64)
        for campaign in self.targeting.get(household, ()):
            coupons = self.campaign_coupons.get(campaign)
            spec = self.campaign_by_id.get(campaign)
            if not coupons or spec is None:
                continue
            lo, hi = max(spec.start_day, first_day), min(spec.end_day, last_day)
            if lo > hi:
                continue
            delta[lo - first_day] += len(coupons)
            delta[hi - first_day + 1] -= len(coupons)
        counts = np.cumsum(delta[:-1])
        return {first_day + i: int(c) for i, c in enumerate(counts) if c > 0}


@dataclass(frozen=True, slots=True)
class Anchor:
    household: int
    day: int
    live_count: int


def build_offer_context(
    txc: pd.DataFrame,
    products: Sequence[Product],
    campaigns: Sequence[Campaign],
    targeting_rows: Sequence[CampaignTargeting],
    eligibility_rows: Sequence[CouponEligibility],
    cfg: TaskConfig,
) -> OfferContext:
    """Precompute everything instance building needs: coupon coverage, top commodities,
    and tier per (campaign, coupon_upc), plus the household frames for profiles."""
    products_df = pd.DataFrame(
        {
            'product_id': [p.product_id for p in products],
            'commodity': [p.commodity for p in products],
            'brand': [p.brand for p in products],
        }
    )
    eligibility = pd.DataFrame(
        {
            'campaign': [row.campaign for row in eligibility_rows],
            'coupon_upc': [row.coupon_upc for row in eligibility_rows],
            'product_id': [row.product_id for row in eligibility_rows],
        }
    ).merge(products_df, on='product_id', how='left')
    assert not eligibility['commodity'].isna().any(), 'eligible product missing from product.csv'
    eligibility['is_private'] = eligibility['brand'] == BrandTier.PRIVATE
    coverage, top, n_products, tier = _coupon_attributes(eligibility, cfg)
    campaign_coupons: dict[int, list[CouponKey]] = {}
    for campaign, upc in coverage:
        campaign_coupons.setdefault(campaign, []).append((campaign, upc))
    targeting: dict[int, set[int]] = {}
    for row in targeting_rows:
        targeting.setdefault(row.household_key, set()).add(row.campaign)
    household_frames: dict[int, pd.DataFrame] = {}
    ordered = txc[['household_key', 'DAY', 'BASKET_ID', 'commodity', 'brand']].sort_values('DAY')
    for household, frame in ordered.groupby('household_key'):
        household_frames[int(household)] = frame
    return OfferContext(
        targeting={household: frozenset(campaigns) for household, campaigns in targeting.items()},
        campaign_by_id={campaign.campaign: campaign for campaign in campaigns},
        campaign_coupons={c: tuple(sorted(keys)) for c, keys in campaign_coupons.items()},
        coupon_coverage=coverage,
        coupon_top=top,
        coupon_products=n_products,
        coupon_tier=tier,
        household_frames=household_frames,
    )


def sample_anchors(
    ctx: OfferContext, spec: SplitSpec, n: int, cfg: TaskConfig, seed: int
) -> tuple[Anchor, ...]:
    """Seeded anchor draw: candidate days with >= pool_size live coupons, >= gap apart,
    <= max per household, non-empty profile window, capped at n across the split."""
    rng = np.random.default_rng(seed)
    first_day, last_day = (spec.first_week - 1) * 7 + 1, spec.last_week * 7
    picked: list[tuple[int, int, int]] = []
    for household in sorted(spec.households & set(ctx.targeting)):
        counts = ctx.live_coupon_counts(household, first_day, last_day)
        candidates = sorted(
            (day, count) for day, count in counts.items() if count >= cfg.pool_size
        )
        picked += [
            (household, day, count)
            for day, count in _pick_spread(candidates, cfg, rng)
            if _has_history(ctx, household, day, cfg)
        ]
    order = rng.permutation(len(picked))
    return tuple(Anchor(*picked[i]) for i in order[:n])


def build_profile(frame: pd.DataFrame, day: int, cfg: TaskConfig) -> Profile:
    """Household profile over [day - history_days, day): top commodities with counts
    and store-brand share, overall store-brand share, trips per week, full counts."""
    window = frame[(frame['DAY'] >= day - cfg.history_days) & (frame['DAY'] < day)]
    counts = {str(k): int(v) for k, v in window.groupby('commodity').size().items()}
    private = window['brand'] == BrandTier.PRIVATE
    store_share = {
        str(commodity): float(share)
        for commodity, share in private.groupby(window['commodity']).mean().items()
    }
    ranked = sorted(counts, key=lambda commodity: (-counts[commodity], commodity))
    top = tuple(
        ProfileEntry(commodity, counts[commodity], round(store_share.get(commodity, 0.0), 3))
        for commodity in ranked[: cfg.profile_top_commodities]
    )
    overall = float(private.mean()) if len(window) else 0.0
    trips = window['BASKET_ID'].nunique() / (cfg.history_days / 7)
    return Profile(
        top=top,
        overall_store_share=round(overall, 3),
        trips_per_week=round(float(trips), 3),
        commodity_counts=counts,
    )


def build_instance(
    ctx: OfferContext, anchor: Anchor, split: str, cfg: TaskConfig, rng: np.random.Generator
) -> OfferInstance:
    """One anchor to one pool: the constant relevant-coupon prefix, then seeded
    distractors, so every level slice keeps the same relevant count."""
    profile = build_profile(ctx.household_frames[anchor.household], anchor.day, cfg)
    live = ctx.live_keys(anchor.household, anchor.day)
    assert len(live) >= cfg.pool_size, 'anchor below the pool threshold'
    mass = {key: profile.mass(ctx.coupon_coverage[key]) for key in live}
    relevant = sorted((key for key, m in mass.items() if m > 0), key=lambda key: (-mass[key], key))
    n_relevant = min(cfg.relevant_coupons, len(relevant))
    distractors = [key for key, m in mass.items() if m == 0]
    n_distractors = cfg.pool_size - n_relevant
    # when a household's live set is nearly all relevant, pad with leftover relevant
    if len(distractors) < n_distractors:
        distractors += relevant[n_relevant:]
    assert len(distractors) >= n_distractors, 'live set cannot fill the pool'
    picks = rng.permutation(len(distractors))[:n_distractors]
    pool = relevant[:n_relevant] + [distractors[i] for i in picks]
    coupons = tuple(_coupon(ctx, code, key, anchor.day, cfg) for code, key in enumerate(pool))
    return OfferInstance(
        instance_id=f'offer-{split}-{anchor.household}-{anchor.day}',
        split=split,
        household=anchor.household,
        day=anchor.day,
        coupons=coupons,
        profile=profile,
        level_sizes=dict(cfg.level_sizes),
        n_live_coupons=len(live),
        share_relevant=round(len(relevant) / len(live), 3),
    )


class CouponRecord(BaseModel):
    code: str
    campaign: int
    coupon_upc: int
    top_commodities: tuple[str, ...]
    commodities: tuple[str, ...]
    tier: str
    ends_soon: bool
    n_products: int


class ProfileEntryRecord(BaseModel):
    commodity: str
    count: int
    store_share: float


class ProfileRecord(BaseModel):
    top: tuple[ProfileEntryRecord, ...]
    overall_store_share: float
    trips_per_week: float
    commodity_counts: dict[str, int]


class InstanceRecord(BaseModel):
    instance_id: str
    split: str
    household: int
    day: int
    coupons: tuple[CouponRecord, ...]
    profile: ProfileRecord
    level_sizes: dict[str, int]
    n_live_coupons: int
    share_relevant: float


def instance_to_record(instance: OfferInstance) -> InstanceRecord:
    return InstanceRecord(
        instance_id=instance.instance_id,
        split=instance.split,
        household=instance.household,
        day=instance.day,
        coupons=[
            CouponRecord(
                code=c.code,
                campaign=c.campaign,
                coupon_upc=c.coupon_upc,
                top_commodities=c.top_commodities,
                commodities=c.commodities,
                tier=c.tier,
                ends_soon=c.ends_soon,
                n_products=c.n_products,
            )
            for c in instance.coupons
        ],
        profile=ProfileRecord(
            top=[
                ProfileEntryRecord(commodity=e.commodity, count=e.count, store_share=e.store_share)
                for e in instance.profile.top
            ],
            overall_store_share=instance.profile.overall_store_share,
            trips_per_week=instance.profile.trips_per_week,
            commodity_counts=instance.profile.commodity_counts,
        ),
        level_sizes=instance.level_sizes,
        n_live_coupons=instance.n_live_coupons,
        share_relevant=instance.share_relevant,
    )


def record_to_instance(record: InstanceRecord) -> OfferInstance:
    return OfferInstance(
        instance_id=record.instance_id,
        split=record.split,
        household=record.household,
        day=record.day,
        coupons=tuple(
            OfferCoupon(
                code=c.code,
                campaign=c.campaign,
                coupon_upc=c.coupon_upc,
                top_commodities=c.top_commodities,
                commodities=c.commodities,
                tier=c.tier,
                ends_soon=c.ends_soon,
                n_products=c.n_products,
            )
            for c in record.coupons
        ),
        profile=Profile(
            top=tuple(
                ProfileEntry(commodity=e.commodity, count=e.count, store_share=e.store_share)
                for e in record.profile.top
            ),
            overall_store_share=record.profile.overall_store_share,
            trips_per_week=record.profile.trips_per_week,
            commodity_counts=record.profile.commodity_counts,
        ),
        level_sizes=record.level_sizes,
        n_live_coupons=record.n_live_coupons,
        share_relevant=record.share_relevant,
    )


def render_preview(instance: OfferInstance) -> str:
    top = ', '.join(
        f'{e.commodity} ({e.count}, {e.store_share:.0%} store)' for e in instance.profile.top
    )
    lines = [
        f'### {instance.instance_id}',
        f'- household {instance.household}, day {instance.day}; '
        f'{instance.n_live_coupons} live coupons, {instance.share_relevant:.0%} relevant',
        f'- profile: {top}; store share {instance.profile.overall_store_share:.0%}, '
        f'{instance.profile.trips_per_week:.1f} trips/week',
        '| code | covers | tier | ends soon |',
        '|---|---|---|---|',
    ]
    for coupon in instance.coupons:
        ends = 'yes' if coupon.ends_soon else ''
        covers = ', '.join(coupon.top_commodities)
        lines.append(f'| {coupon.code} | {covers} | {coupon.tier} | {ends} |')
    return '\n'.join(lines)


def _coupon_attributes(
    eligibility: pd.DataFrame, cfg: TaskConfig
) -> tuple[
    dict[CouponKey, tuple[str, ...]],
    dict[CouponKey, tuple[str, ...]],
    dict[CouponKey, int],
    dict[CouponKey, str],
]:
    rows = (
        eligibility.groupby(['campaign', 'coupon_upc', 'commodity'], sort=True)
        .agg(n=('product_id', 'size'), private=('is_private', 'sum'))
        .reset_index()
        # per coupon: commodities by product count descending, name ascending for ties
        .sort_values(
            ['campaign', 'coupon_upc', 'n', 'commodity'], ascending=[True, True, False, True]
        )
    )
    commodities: dict[CouponKey, list[str]] = {}
    n_products: dict[CouponKey, int] = {}
    private_lines: dict[CouponKey, int] = {}
    for campaign, upc, commodity, n, private in rows.itertuples(index=False):
        key = (int(campaign), int(upc))
        commodities.setdefault(key, []).append(str(commodity))
        n_products[key] = n_products.get(key, 0) + int(n)
        private_lines[key] = private_lines.get(key, 0) + int(private)
    coverage = {key: tuple(sorted(names)) for key, names in commodities.items()}
    top = {key: tuple(names[: cfg.coupon_top_commodities]) for key, names in commodities.items()}
    tier: dict[CouponKey, str] = {}
    for key in n_products:
        private_share = private_lines[key] / n_products[key]
        if private_share >= cfg.tier_dominance:
            tier[key] = BrandTier.PRIVATE.value
        elif private_share <= 1 - cfg.tier_dominance:
            tier[key] = BrandTier.NATIONAL.value
        else:
            tier[key] = MIXED
    return coverage, top, n_products, tier


def _coupon(
    ctx: OfferContext, code: int, key: CouponKey, day: int, cfg: TaskConfig
) -> OfferCoupon:
    campaign = ctx.campaign_by_id[key[0]]
    return OfferCoupon(
        code=f'k{code + 1:02d}',
        campaign=key[0],
        coupon_upc=key[1],
        top_commodities=ctx.coupon_top[key],
        commodities=ctx.coupon_coverage[key],
        tier=ctx.coupon_tier[key],
        ends_soon=campaign.end_day - day <= cfg.ends_soon_days,
        n_products=ctx.coupon_products[key],
    )


def _pick_spread(
    candidates: Sequence[tuple[int, int]], cfg: TaskConfig, rng: np.random.Generator
) -> tuple[tuple[int, int], ...]:
    """Up to max_instances_per_hh candidate days at least min_anchor_gap_days apart."""
    order = rng.permutation(len(candidates))
    picked: list[tuple[int, int]] = []
    for i in order:
        day, count = candidates[i]
        if all(abs(day - other) >= cfg.min_anchor_gap_days for other, _ in picked):
            picked.append((day, count))
            if len(picked) == cfg.max_instances_per_hh:
                break
    return tuple(sorted(picked))


def _has_history(ctx: OfferContext, household: int, day: int, cfg: TaskConfig) -> bool:
    frame = ctx.household_frames.get(household)
    if frame is None:
        return False
    return bool(((frame['DAY'] >= day - cfg.history_days) & (frame['DAY'] < day)).any())
