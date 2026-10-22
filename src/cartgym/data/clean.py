from dataclasses import dataclass

import pandas as pd
from loguru import logger

from cartgym.config import CleaningConfig
from cartgym.data.load import Product


@dataclass(frozen=True, slots=True)
class CleaningReport:
    n_input: int
    n_kept: int
    dropped: dict[str, int]


def derive_unit_prices(tx: pd.DataFrame) -> pd.DataFrame:
    """Derive regular and loyalty unit prices; source discounts are stored as negative amounts."""
    out = tx.copy()
    coupon_discounts = out['COUPON_DISC'] + out['COUPON_MATCH_DISC']
    out['regular_unit'] = (out['SALES_VALUE'] - out['RETAIL_DISC'] - coupon_discounts) / out[
        'QUANTITY'
    ]
    out['loyalty_unit'] = (out['SALES_VALUE'] - coupon_discounts) / out['QUANTITY']
    return out


def clean_transactions(
    tx: pd.DataFrame, products: list[Product], cfg: CleaningConfig
) -> tuple[pd.DataFrame, CleaningReport]:
    """Apply the exclusion rules in order, counting the rows each rule drops."""
    attrs = _product_attrs(products)
    merged = tx.merge(attrs, left_on='PRODUCT_ID', right_on='product_id', how='left')
    masks: list[tuple[str, pd.Series]] = [
        ('unknown_product', merged['department'].isna()),
        ('nonpositive_quantity', tx['QUANTITY'] <= 0),
        ('nonpositive_sales_value', tx['SALES_VALUE'] <= 0),
        ('excluded_department', merged['department'].isin(cfg.excluded_departments).fillna(False)),
        ('excluded_commodity', merged['commodity'].isin(cfg.excluded_commodities).fillna(False)),
        ('quantity_outlier', tx['QUANTITY'] > cfg.max_quantity),
    ]
    keep = pd.Series(True, index=tx.index)
    dropped: dict[str, int] = {}
    for name, mask in masks:
        dropped[name] = int((mask & keep).sum())
        keep &= ~mask
    cleaned = tx.loc[keep].reset_index(drop=True)
    logger.info('cleaned transactions: {}/{} rows kept', len(cleaned), len(tx))
    return cleaned, CleaningReport(len(tx), len(cleaned), dropped)


def prepare_transactions(
    tx: pd.DataFrame, products: list[Product], cfg: CleaningConfig
) -> tuple[pd.DataFrame, CleaningReport]:
    """Clean, derive unit prices, and attach product attributes in one pass."""
    tx_clean, report = clean_transactions(tx, products, cfg)
    attrs = _product_attrs(products)[['product_id', 'commodity', 'sub_commodity', 'brand']]
    txc = (
        derive_unit_prices(tx_clean)
        .merge(attrs, left_on='PRODUCT_ID', right_on='product_id', how='left')
        .drop(columns='product_id')
    )
    return txc, report


def _product_attrs(products: list[Product]) -> pd.DataFrame:
    attrs = pd.DataFrame(
        [
            {
                'product_id': p.product_id,
                'department': p.department,
                'commodity': p.commodity,
                'sub_commodity': p.sub_commodity,
                'brand': p.brand,
            }
            for p in products
        ]
    )
    assert attrs['product_id'].is_unique, 'duplicate product ids in the product table'
    return attrs
