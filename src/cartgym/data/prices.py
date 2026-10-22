from dataclasses import dataclass

import numpy as np
import pandas as pd
from loguru import logger

from cartgym.config import PricingConfig


@dataclass(frozen=True, slots=True)
class PricePoint:
    shelf_cents: int
    loyalty_disc_cents: int
    n_obs: int


def build_price_table(txc: pd.DataFrame, cfg: PricingConfig) -> dict[tuple[int, int], PricePoint]:
    """Chain-level (product, week) median prices as integer cents."""
    unit_discount = txc['regular_unit'] - txc['loyalty_unit']
    grouped = (
        txc.assign(unit_discount=unit_discount)
        .groupby(['PRODUCT_ID', 'WEEK_NO'])
        .agg(
            regular=('regular_unit', 'median'),
            discount=('unit_discount', 'median'),
            n_obs=('regular_unit', 'size'),
        )
        .reset_index()
    )
    usable = grouped[(grouped['n_obs'] >= cfg.min_price_obs) & (grouped['regular'] > 0)]
    if len(usable) < len(grouped):
        logger.warning(
            'price table: dropped {} groups (too few obs or non-positive price)',
            len(grouped) - len(usable),
        )
    shelves = (usable['regular'] * 100).round().astype('int64').to_numpy()
    discounts = (usable['discount'] * 100).round().astype('int64').to_numpy()
    # round-half-up on medians can push the discount onto the shelf price; cents cannot go negative
    discounts = np.minimum(discounts, shelves)
    return {
        (int(product_id), int(week)): PricePoint(int(shelf), int(discount), int(n_obs))
        for product_id, week, shelf, discount, n_obs in zip(
            usable['PRODUCT_ID'].to_numpy(),
            usable['WEEK_NO'].to_numpy(),
            shelves,
            discounts,
            usable['n_obs'].to_numpy(),
            strict=True,
        )
    }
