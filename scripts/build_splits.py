import argparse
from pathlib import Path

import pandas as pd
from loguru import logger

from commgym.core.config import load_config
from commgym.core.logging import setup_logging
from commgym.dunnhumby.clean import prepare_transactions
from commgym.dunnhumby.config import CleaningConfig, SplitsConfig
from commgym.dunnhumby.load import load_demographics, load_products, load_transactions
from commgym.dunnhumby.splits import Splits, build_splits


def main() -> None:
    args = _parse_args()
    setup_logging()
    cfg = load_config(SplitsConfig, args.config)
    products = load_products(args.data_dir)
    tx = load_transactions(args.data_dir)
    txc, _ = prepare_transactions(tx, products, load_config(CleaningConfig, args.cleaning_config))
    demographics = {d.household_key for d in load_demographics(args.data_dir)}
    coverage = (
        txc.groupby(['commodity', 'WEEK_NO']).agg(n_skus=('PRODUCT_ID', 'nunique')).reset_index()
    )
    splits = build_splits(txc, demographics, coverage, cfg)
    _write_summary(splits, txc, args.out)
    logger.info('splits summary written to {}', args.out)


def _write_summary(splits: Splits, txc: pd.DataFrame, out: Path) -> None:
    baskets = txc.groupby('BASKET_ID').agg(
        household_key=('household_key', 'first'), WEEK_NO=('WEEK_NO', 'first')
    )
    lines = [
        '# Splits Summary',
        '',
        '| split | households | weeks | baskets |',
        '|---|---|---|---|',
    ]
    for spec in (splits.train, splits.dev, splits.eval_unseen, splits.eval_known):
        in_split = baskets['household_key'].isin(spec.households) & baskets['WEEK_NO'].between(
            spec.first_week, spec.last_week
        )
        lines.append(
            f'| {spec.name} | {len(spec.households)} | w{spec.first_week}–{spec.last_week} |'
            f' {int(in_split.sum())} |'
        )
    held = sorted(splits.heldout_commodities)
    overlap = splits.train.households & splits.eval_unseen.households
    lines += [
        '',
        f'- cohort A ∩ cohort B = {len(overlap)} households (must be 0)',
        f'- held-out commodities: {len(held)} (eval-only), e.g. {", ".join(held[:10])}',
    ]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text('\n'.join(lines))


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Build household x time splits and summarize them'
    )
    parser.add_argument('--data-dir', type=Path, default=None)
    parser.add_argument('--config', type=Path, default=Path('configs/splits.yaml'))
    parser.add_argument('--cleaning-config', type=Path, default=Path('configs/data.yaml'))
    parser.add_argument('--out', type=Path, default=Path('reports/splits_summary.md'))
    return parser.parse_args()


if __name__ == '__main__':
    main()
