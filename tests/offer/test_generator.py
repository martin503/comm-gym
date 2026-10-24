import numpy as np
import pandas as pd

from commgym.dunnhumby.load import Campaign, CampaignTargeting, CouponEligibility, Product
from commgym.dunnhumby.splits import SplitSpec
from commgym.dunnhumby.types import BrandTier
from commgym.offer.config import TaskConfig
from commgym.offer.generator import (
    Anchor,
    OfferContext,
    build_instance,
    build_offer_context,
    build_profile,
    instance_to_record,
    record_to_instance,
    sample_anchors,
)

CFG = TaskConfig(
    level_sizes={'L1': 3, 'L2': 5}, relevant_coupons=2, history_days=98, ends_soon_days=7
)


def _frame(rows: list[tuple[int, str, BrandTier]]) -> pd.DataFrame:
    """(day, commodity, brand) rows; one basket per day."""
    days = [day for day, _, _ in rows]
    basket_ids: dict[int, int] = {}
    return pd.DataFrame(
        {
            'DAY': days,
            'BASKET_ID': [basket_ids.setdefault(day, len(basket_ids)) for day in days],
            'commodity': [commodity for _, commodity, _ in rows],
            'brand': [brand for _, _, brand in rows],
        }
    )


def _context(
    campaigns: dict[int, tuple[int, int]],
    coupons: dict[tuple[int, int], tuple[str, ...]],
    targeting: dict[int, frozenset[int]],
    frames: dict[int, pd.DataFrame],
) -> OfferContext:
    by_campaign: dict[int, list[tuple[int, int]]] = {}
    for key in coupons:
        by_campaign.setdefault(key[0], []).append(key)
    return OfferContext(
        targeting=targeting,
        campaign_by_id={
            campaign: Campaign(
                DESCRIPTION='TypeX', CAMPAIGN=campaign, START_DAY=start, END_DAY=end
            )
            for campaign, (start, end) in campaigns.items()
        },
        campaign_coupons={campaign: tuple(sorted(keys)) for campaign, keys in by_campaign.items()},
        coupon_coverage=coupons,
        coupon_top=dict(coupons),
        coupon_products={key: 1 for key in coupons},
        coupon_tier={key: 'Mixed' for key in coupons},
        household_frames=frames,
    )


def test_live_coupon_counts_span_campaign_windows():
    ctx = _context(
        campaigns={1: (1, 10), 2: (5, 15)},
        coupons={
            (1, 101): ('MILK',),
            (1, 102): ('MILK',),
            (2, 103): ('SODA',),
            (2, 104): ('SODA',),
            (2, 105): ('SODA',),
        },
        targeting={10: frozenset({1, 2})},
        frames={},
    )
    counts = ctx.live_coupon_counts(10, 1, 20)
    assert {
        'early': counts[1],
        'overlap': counts[7],
        'tail': counts[12],
        'absent': 16 in counts,
    } == {'early': 2, 'overlap': 5, 'tail': 3, 'absent': False}


def test_same_upc_across_campaigns_stays_distinct():
    products = [
        Product(
            PRODUCT_ID=1,
            MANUFACTURER=1,
            DEPARTMENT='GROCERY',
            BRAND=BrandTier.PRIVATE,
            COMMODITY_DESC='MILK',
            SUB_COMMODITY_DESC='FLUID MILK',
            CURR_SIZE_OF_PRODUCT='1G',
        ),
        Product(
            PRODUCT_ID=2,
            MANUFACTURER=2,
            DEPARTMENT='GROCERY',
            BRAND=BrandTier.NATIONAL,
            COMMODITY_DESC='SODA',
            SUB_COMMODITY_DESC='SODA',
            CURR_SIZE_OF_PRODUCT='2L',
        ),
    ]
    campaigns = [
        Campaign(DESCRIPTION='TypeA', CAMPAIGN=1, START_DAY=1, END_DAY=30),
        Campaign(DESCRIPTION='TypeA', CAMPAIGN=2, START_DAY=1, END_DAY=30),
    ]
    targeting = [
        CampaignTargeting(DESCRIPTION='TypeA', household_key=10, CAMPAIGN=1),
        CampaignTargeting(DESCRIPTION='TypeA', household_key=10, CAMPAIGN=2),
    ]
    eligibility = [
        CouponEligibility(COUPON_UPC=101, PRODUCT_ID=1, CAMPAIGN=1),
        CouponEligibility(COUPON_UPC=101, PRODUCT_ID=2, CAMPAIGN=2),
    ]
    txc = pd.DataFrame(
        {
            'household_key': [10, 10],
            'DAY': [5, 6],
            'BASKET_ID': [1, 2],
            'commodity': ['MILK', 'SODA'],
            'brand': [BrandTier.PRIVATE, BrandTier.NATIONAL],
        }
    )
    ctx = build_offer_context(txc, products, campaigns, targeting, eligibility, CFG)
    assert {
        'campaign1': ctx.coupon_coverage[(1, 101)],
        'campaign2': ctx.coupon_coverage[(2, 101)],
        'tier1': ctx.coupon_tier[(1, 101)],
        'tier2': ctx.coupon_tier[(2, 101)],
        'live': ctx.live_keys(10, 5),
    } == {
        'campaign1': ('MILK',),
        'campaign2': ('SODA',),
        'tier1': 'Private',
        'tier2': 'National',
        'live': ((1, 101), (2, 101)),
    }


def test_profile_counts_and_store_share():
    frame = _frame(
        [
            (5, 'MILK', BrandTier.PRIVATE),
            (5, 'SNACKS', BrandTier.NATIONAL),
            (6, 'MILK', BrandTier.NATIONAL),
            (6, 'SODA', BrandTier.PRIVATE),
        ]
    )
    profile = build_profile(frame, day=7, cfg=CFG)
    assert {
        'counts': profile.commodity_counts,
        'top_order': [entry.commodity for entry in profile.top],
        'milk_store_share': profile.top[0].store_share,
        'overall': profile.overall_store_share,
        'trips': profile.trips_per_week,
        'mass': profile.mass(('MILK', 'SNACKS')),
    } == {
        'counts': {'MILK': 2, 'SNACKS': 1, 'SODA': 1},
        'top_order': ['MILK', 'SNACKS', 'SODA'],
        'milk_store_share': 0.5,
        'overall': 0.5,
        'trips': 0.143,
        'mass': 3,
    }


def test_pool_keeps_relevant_prefix_constant_across_levels():
    coverage: dict[tuple[int, int], tuple[str, ...]] = {
        (10, 101): ('MILK',),
        (10, 102): ('SNACKS',),
        (10, 103): ('MILK', 'SNACKS'),
        (10, 104): ('WATER',),
        (10, 105): ('WATER',),
        (10, 106): ('WATER',),
        (10, 107): ('WATER',),
        (10, 108): ('WATER',),
    }
    # days 1-19 relative to anchor day 20: MILK x10, SNACKS x2, SODA x7
    rows = (
        [(day, 'MILK', BrandTier.PRIVATE) for day in range(1, 11)]
        + [(day, 'SNACKS', BrandTier.PRIVATE) for day in range(11, 13)]
        + [(day, 'SODA', BrandTier.PRIVATE) for day in range(13, 20)]
    )
    ctx = _context(
        campaigns={10: (1, 30)},
        coupons=coverage,
        targeting={1: frozenset({10})},
        frames={1: _frame(rows)},
    )
    instance = build_instance(
        ctx, Anchor(1, 20, len(coverage)), 'dev', CFG, np.random.default_rng(0)
    )
    relevant = {
        key
        for key, commodities in coverage.items()
        if 'MILK' in commodities or 'SNACKS' in commodities
    }
    l1, l2 = instance.slice_for('L1'), instance.slice_for('L2')
    assert {
        'l1_relevant': sum(1 for c in l1 if (c.campaign, c.coupon_upc) in relevant),
        'l2_relevant': sum(1 for c in l2 if (c.campaign, c.coupon_upc) in relevant),
        'l1_in_l2': {c.code for c in l1} < {c.code for c in l2},
        'relevant_first': {(c.campaign, c.coupon_upc) for c in instance.coupons[:2]}
        == {(10, 103), (10, 101)},
        'share': instance.share_relevant,
        'codes': [c.code for c in instance.coupons],
    } == {
        'l1_relevant': 2,
        'l2_relevant': 2,
        'l1_in_l2': True,
        'relevant_first': True,
        'share': 0.375,
        'codes': ['k01', 'k02', 'k03', 'k04', 'k05'],
    }


def test_record_round_trip():
    coverage: dict[tuple[int, int], tuple[str, ...]] = {
        (10, 101): ('MILK',),
        (10, 102): ('WATER',),
        (10, 103): ('WATER',),
        (10, 104): ('WATER',),
        (10, 105): ('WATER',),
    }
    ctx = _context(
        campaigns={10: (1, 30)},
        coupons=coverage,
        targeting={1: frozenset({10})},
        frames={1: _frame([(day, 'MILK', BrandTier.PRIVATE) for day in range(1, 30)])},
    )
    instance = build_instance(ctx, Anchor(1, 20, 5), 'dev', CFG, np.random.default_rng(1))
    assert record_to_instance(instance_to_record(instance)) == instance


def test_anchors_respect_gap_cap_and_supply():
    coupons: dict[tuple[int, int], tuple[str, ...]] = {(10, 100 + i): ('MILK',) for i in range(6)}
    ctx = _context(
        campaigns={10: (1, 21)},
        coupons=coupons,
        targeting={1: frozenset({10})},
        # day 0 keeps the profile window non-empty for every candidate day >= 1
        frames={1: _frame([(day, 'MILK', BrandTier.PRIVATE) for day in range(0, 22)])},
    )
    spec = SplitSpec('dev', frozenset({1}), 1, 3)
    anchors = sample_anchors(ctx, spec, n=10, cfg=CFG, seed=0)
    by_day = sorted(anchors, key=lambda anchor: anchor.day)
    assert {
        # seeded-random greedy picking, so the count varies; the invariants do not
        'n_in_range': 1 <= len(anchors) <= CFG.max_instances_per_hh,
        'households': {a.household for a in anchors},
        'gaps': all(b.day - a.day >= CFG.min_anchor_gap_days for a, b in zip(by_day, by_day[1:])),
        'live_counts': {a.live_count for a in anchors},
    } == {'n_in_range': True, 'households': {1}, 'gaps': True, 'live_counts': {6}}
