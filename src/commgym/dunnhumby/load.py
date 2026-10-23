import csv
import os
from collections.abc import Hashable, Iterator
from pathlib import Path

import pandas as pd
from loguru import logger
from pydantic import BaseModel, Field, ValidationError

from commgym.cartopt.instance import BrandTier

TRANSACTION_DTYPES: dict[Hashable, str] = {
    'household_key': 'int64',
    'BASKET_ID': 'int64',
    'DAY': 'int16',
    'PRODUCT_ID': 'int32',
    'QUANTITY': 'int32',
    'SALES_VALUE': 'float64',
    'STORE_ID': 'int32',
    'RETAIL_DISC': 'float64',
    'TRANS_TIME': 'int32',
    'WEEK_NO': 'int16',
    'COUPON_DISC': 'float64',
    'COUPON_MATCH_DISC': 'float64',
}

KEY_COLUMNS = ('household_key', 'BASKET_ID', 'DAY', 'PRODUCT_ID', 'WEEK_NO')


class Product(BaseModel):
    product_id: int = Field(alias='PRODUCT_ID')
    manufacturer: int = Field(alias='MANUFACTURER')
    department: str = Field(alias='DEPARTMENT')
    brand: BrandTier = Field(alias='BRAND')
    commodity: str = Field(alias='COMMODITY_DESC')
    sub_commodity: str = Field(alias='SUB_COMMODITY_DESC')
    size: str = Field(alias='CURR_SIZE_OF_PRODUCT')


class Campaign(BaseModel):
    description: str = Field(alias='DESCRIPTION')
    campaign: int = Field(alias='CAMPAIGN')
    start_day: int = Field(alias='START_DAY')
    end_day: int = Field(alias='END_DAY')


class CampaignTargeting(BaseModel):
    description: str = Field(alias='DESCRIPTION')
    household_key: int = Field(alias='household_key')
    campaign: int = Field(alias='CAMPAIGN')


class CouponEligibility(BaseModel):
    coupon_upc: int = Field(alias='COUPON_UPC')
    product_id: int = Field(alias='PRODUCT_ID')
    campaign: int = Field(alias='CAMPAIGN')


class CouponRedemption(BaseModel):
    household_key: int = Field(alias='household_key')
    day: int = Field(alias='DAY')
    coupon_upc: int = Field(alias='COUPON_UPC')
    campaign: int = Field(alias='CAMPAIGN')


class Demographics(BaseModel):
    age_desc: str = Field(alias='AGE_DESC')
    marital_status_code: str = Field(alias='MARITAL_STATUS_CODE')
    income_desc: str = Field(alias='INCOME_DESC')
    homeowner_desc: str = Field(alias='HOMEOWNER_DESC')
    hh_comp_desc: str = Field(alias='HH_COMP_DESC')
    household_size_desc: str = Field(alias='HOUSEHOLD_SIZE_DESC')
    kid_category_desc: str = Field(alias='KID_CATEGORY_DESC')
    household_key: int = Field(alias='household_key')


def data_dir() -> Path:
    """Resolve the dataset directory: COMMGYM_DATA_DIR env var or ./data."""
    return Path(os.environ.get('COMMGYM_DATA_DIR', 'data'))


def load_products(root: Path | None = None) -> list[Product]:
    return _load_models((root or data_dir()) / 'product.csv', Product)


def load_campaigns(root: Path | None = None) -> list[Campaign]:
    return _load_models((root or data_dir()) / 'campaign_desc.csv', Campaign)


def load_campaign_targeting(root: Path | None = None) -> list[CampaignTargeting]:
    return _load_models((root or data_dir()) / 'campaign_table.csv', CampaignTargeting)


def load_coupon_eligibility(root: Path | None = None) -> list[CouponEligibility]:
    return _load_models((root or data_dir()) / 'coupon.csv', CouponEligibility)


def load_coupon_redemptions(root: Path | None = None) -> list[CouponRedemption]:
    return _load_models((root or data_dir()) / 'coupon_redempt.csv', CouponRedemption)


def load_demographics(root: Path | None = None) -> list[Demographics]:
    return _load_models((root or data_dir()) / 'hh_demographic.csv', Demographics)


def load_transactions(root: Path | None = None) -> pd.DataFrame:
    """Load transactions with a validated schema (rows stay a DataFrame, not models)."""
    path = (root or data_dir()) / 'transaction_data.csv'
    tx = pd.read_csv(str(path), dtype=TRANSACTION_DTYPES)
    assert set(tx.columns) == set(TRANSACTION_DTYPES), (
        'unexpected transaction schema: '
        f'{sorted(str(c) for c in set(tx.columns) ^ set(TRANSACTION_DTYPES))}'
    )
    assert not tx.loc[:, list(KEY_COLUMNS)].isna().any().any(), 'null keys in transaction data'
    return tx


def iter_causal_chunks(
    root: Path | None = None, chunksize: int = 1_000_000
) -> Iterator[pd.DataFrame]:
    """Stream causal_data.csv (36.8M rows); only loaded behind an explicit flag."""
    path = (root or data_dir()) / 'causal_data.csv'
    yield from pd.read_csv(path, chunksize=chunksize)


def _load_models[T: BaseModel](path: Path, model: type[T]) -> list[T]:
    """Parse a CSV into pydantic models, dropping and loudly logging invalid rows."""
    rows: list[T] = []
    failed = 0
    with path.open(newline='', encoding='utf-8') as f:
        for record in csv.DictReader(f):
            try:
                rows.append(model.model_validate(record))
            except ValidationError:
                failed += 1
    if failed:
        logger.warning(
            '{}: dropped {} rows failing {} validation', path.name, failed, model.__name__
        )
    return rows
