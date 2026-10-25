from dataclasses import dataclass

import pandas as pd
from loguru import logger

from commgym.dunnhumby.load import (
    Campaign,
    CampaignTargeting,
    CouponEligibility,
    CouponRedemption,
)


@dataclass(frozen=True, slots=True)
class CouponIndex:
    """Prejoined coupon tables: eligibility, campaign windows, targeting, and typical values."""

    campaigns: dict[int, Campaign]
    campaign_upcs: dict[int, frozenset[int]]
    upc_campaigns: dict[int, frozenset[int]]
    product_upcs: dict[int, frozenset[int]]
    upc_products: dict[int, frozenset[int]]
    targeting: dict[int, frozenset[int]]
    coupon_values: dict[int, int]
    campaign_values: dict[int, int]
    global_value_cents: int


@dataclass(frozen=True, slots=True)
class LiveCoupon:
    coupon_upc: int
    campaigns: frozenset[int]
    covered_products: frozenset[int]
    typical_value_cents: int
    value_provenance: str


def build_coupon_index(
    eligibility: list[CouponEligibility],
    campaigns: list[Campaign],
    targeting: list[CampaignTargeting],
    redemptions: list[CouponRedemption],
    txc: pd.DataFrame,
    *,
    min_redemptions: int = 2,
) -> CouponIndex:
    """Join the coupon tables and derive each coupon's typical value from real discounts.

    A redemption event carries no amount, so values come from matching that household-day's
    coupon-discount lines covered by the UPC. The fallback chain is coupon -> campaign -> global.
    """
    campaigns_by_id = {c.campaign: c for c in campaigns}
    upc_campaigns: dict[int, set[int]] = {}
    product_upcs: dict[int, set[int]] = {}
    upc_products: dict[int, set[int]] = {}
    campaign_upcs: dict[int, set[int]] = {}
    for row in eligibility:
        upc_campaigns.setdefault(row.coupon_upc, set()).add(row.campaign)
        product_upcs.setdefault(row.product_id, set()).add(row.coupon_upc)
        upc_products.setdefault(row.coupon_upc, set()).add(row.product_id)
        campaign_upcs.setdefault(row.campaign, set()).add(row.coupon_upc)
    targeting_map: dict[int, set[int]] = {}
    for row in targeting:
        targeting_map.setdefault(row.household_key, set()).add(row.campaign)

    disc = txc.loc[txc['COUPON_DISC'] < 0, ['household_key', 'DAY', 'PRODUCT_ID', 'COUPON_DISC']]
    cents = (disc['COUPON_DISC'].abs() * 100).round().astype('int64').to_numpy()
    lines_by_key: dict[tuple[int, int], list[tuple[int, int]]] = {}
    for household, day, product, cent in zip(
        disc['household_key'].to_numpy(),
        disc['DAY'].to_numpy(),
        disc['PRODUCT_ID'].to_numpy(),
        cents,
        strict=True,
    ):
        lines_by_key.setdefault((int(household), int(day)), []).append((int(product), int(cent)))

    upc_values: dict[int, list[int]] = {}
    campaign_value_lists: dict[int, list[int]] = {}
    joined = 0
    for redemption in redemptions:
        covered = upc_products.get(redemption.coupon_upc)
        if not covered:
            continue
        matches = [
            cent
            for product, cent in lines_by_key.get((redemption.household_key, redemption.day), ())
            if product in covered
        ]
        if not matches:
            continue
        joined += 1
        value = max(matches)
        upc_values.setdefault(redemption.coupon_upc, []).append(value)
        campaign_value_lists.setdefault(redemption.campaign, []).append(value)
    logger.info(
        'coupon values: {}/{} redemptions joined to covered discount lines',
        joined,
        len(redemptions),
    )
    return CouponIndex(
        campaigns=campaigns_by_id,
        campaign_upcs={c: frozenset(s) for c, s in campaign_upcs.items()},
        upc_campaigns={upc: frozenset(s) for upc, s in upc_campaigns.items()},
        product_upcs={p: frozenset(s) for p, s in product_upcs.items()},
        upc_products={upc: frozenset(s) for upc, s in upc_products.items()},
        targeting={h: frozenset(s) for h, s in targeting_map.items()},
        coupon_values={
            upc: _lower_median(values)
            for upc, values in upc_values.items()
            if len(values) >= min_redemptions
        },
        campaign_values={
            campaign: _lower_median(values)
            for campaign, values in campaign_value_lists.items()
            if values
        },
        global_value_cents=_lower_median([int(cent) for cent in cents]) if len(cents) else 0,
    )


def live_upcs(index: CouponIndex, household: int, day: int) -> frozenset[int]:
    """UPCs live for a household on a day: any of the UPC's campaigns live and targeting them."""
    upcs: set[int] = set()
    for campaign_id in index.targeting.get(household, frozenset()):
        campaign = index.campaigns.get(campaign_id)
        if campaign is not None and campaign.start_day <= day <= campaign.end_day:
            upcs |= index.campaign_upcs.get(campaign_id, frozenset())
    return frozenset(upcs)


def typical_value(index: CouponIndex, coupon_upc: int) -> tuple[int, str]:
    """Typical value in cents and its provenance: coupon, campaign, or global fallback."""
    if coupon_upc in index.coupon_values:
        return index.coupon_values[coupon_upc], 'coupon'
    campaign_medians = [
        index.campaign_values[campaign]
        for campaign in index.upc_campaigns.get(coupon_upc, frozenset())
        if campaign in index.campaign_values
    ]
    if campaign_medians:
        return _lower_median(campaign_medians), 'campaign'
    return index.global_value_cents, 'global'


def live_coupons(index: CouponIndex, household: int, day: int) -> dict[int, LiveCoupon]:
    live: dict[int, LiveCoupon] = {}
    for upc in live_upcs(index, household, day):
        value, provenance = typical_value(index, upc)
        live[upc] = LiveCoupon(
            coupon_upc=upc,
            campaigns=index.upc_campaigns[upc],
            covered_products=index.upc_products.get(upc, frozenset()),
            typical_value_cents=value,
            value_provenance=provenance,
        )
    return live


def _lower_median(values: list[int]) -> int:
    ordered = sorted(values)
    return ordered[(len(ordered) - 1) // 2]
