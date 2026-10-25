from pathlib import Path

import pandas as pd

from commgym.dunnhumby.clean import prepare_transactions
from commgym.dunnhumby.config import CleaningConfig, SplitsConfig
from commgym.dunnhumby.load import (
    Product,
    load_demographics,
    load_products,
    load_transactions,
)
from commgym.dunnhumby.splits import Splits, build_splits


def load_context(
    data_dir: Path | None,
    cleaning: CleaningConfig,
    splits: SplitsConfig,
) -> tuple[list[Product], pd.DataFrame, Splits]:
    """Shared generation preamble: products, cleaned transactions, and household splits."""
    products = load_products(data_dir)
    tx = load_transactions(data_dir)
    txc, _ = prepare_transactions(tx, products, cleaning)
    demographics = {row.household_key for row in load_demographics(data_dir)}
    coverage = (
        txc.groupby(['commodity', 'WEEK_NO']).agg(n_skus=('PRODUCT_ID', 'nunique')).reset_index()
    )
    return products, txc, build_splits(txc, demographics, coverage, splits)
