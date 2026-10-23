import argparse
import json
import zlib
from pathlib import Path

from loguru import logger

from commgym.cartopt.config import LevelsConfig
from commgym.cartopt.generator import (
    build_generator_context,
    generate_batch,
    instance_to_record,
    render_preview,
)
from commgym.core.config import load_config
from commgym.core.logging import setup_logging
from commgym.dunnhumby.clean import prepare_transactions
from commgym.dunnhumby.config import CleaningConfig, PricingConfig, SplitsConfig
from commgym.dunnhumby.load import (
    load_campaign_targeting,
    load_campaigns,
    load_coupon_eligibility,
    load_demographics,
    load_products,
    load_transactions,
)
from commgym.dunnhumby.prices import build_price_table
from commgym.dunnhumby.splits import CampaignCalendar, build_splits


def main() -> None:
    args = _parse_args()
    setup_logging()
    levels_cfg = load_config(LevelsConfig, args.levels_config)
    products = load_products(args.data_dir)
    tx = load_transactions(args.data_dir)
    txc, _ = prepare_transactions(tx, products, load_config(CleaningConfig, args.cleaning_config))
    prices = build_price_table(txc, load_config(PricingConfig, args.pricing_config))
    logger.info('price table: {} (product, week) points', len(prices))
    calendar = CampaignCalendar(tuple(load_campaigns(args.data_dir)))
    eligibility: dict[int, set[int]] = {}
    for row in load_coupon_eligibility(args.data_dir):
        eligibility.setdefault(row.product_id, set()).add(row.campaign)
    targeting: dict[int, set[int]] = {}
    for row in load_campaign_targeting(args.data_dir):
        targeting.setdefault(row.household_key, set()).add(row.campaign)
    amounts = (txc.loc[txc['COUPON_DISC'] < 0, 'COUPON_DISC'].abs() * 100).round().astype('int64')
    logger.info('coupon amount pool: {} lines', len(amounts))
    demographics = {d.household_key for d in load_demographics(args.data_dir)}
    coverage = (
        txc.groupby(['commodity', 'WEEK_NO']).agg(n_skus=('PRODUCT_ID', 'nunique')).reset_index()
    )
    splits = build_splits(
        txc, demographics, coverage, load_config(SplitsConfig, args.splits_config)
    )
    ctx = build_generator_context(
        txc,
        products,
        prices,
        calendar,
        eligibility,
        targeting,
        amounts.to_numpy(),
        splits,
        levels_cfg,
    )
    previews: list[str] = []
    for level in args.levels:
        seed = int(zlib.crc32(f'{args.seed}-{args.split}-{level}'.encode()))
        batch = generate_batch(ctx, level, args.split, args.n, seed)
        args.out_dir.mkdir(parents=True, exist_ok=True)
        out_path = args.out_dir / f'{args.split}_{level}.jsonl'
        with out_path.open('w') as f:
            for generated in batch.instances:
                f.write(json.dumps(instance_to_record(generated)) + '\n')
        traps = sum(1 for generated in batch.instances if generated.info['is_trap'])
        logger.info(
            '{}: {}/{} trap instances, written to {}', level, traps, len(batch.instances), out_path
        )
        previews += [render_preview(generated) for generated in batch.instances]
    kept = previews[: args.preview_n]
    args.preview.parent.mkdir(parents=True, exist_ok=True)
    args.preview.write_text('# Instance preview\n\n' + '\n\n---\n\n'.join(kept))
    logger.info('preview of {} instances written to {}', len(kept), args.preview)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Generate cart-optimizer instances for one split')
    parser.add_argument(
        '--split', default='dev', choices=['train', 'dev', 'eval_unseen', 'eval_known']
    )
    parser.add_argument('--levels', default='L1,L2', help='comma-separated level names')
    parser.add_argument('--n', type=int, default=10, help='instances per level')
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--data-dir', type=Path, default=None)
    parser.add_argument('--levels-config', type=Path, default=Path('configs/cartopt/levels.yaml'))
    parser.add_argument('--cleaning-config', type=Path, default=Path('configs/data.yaml'))
    parser.add_argument('--pricing-config', type=Path, default=Path('configs/pricing.yaml'))
    parser.add_argument('--splits-config', type=Path, default=Path('configs/splits.yaml'))
    parser.add_argument('--out-dir', type=Path, default=Path('instances/cartopt'))
    parser.add_argument('--preview', type=Path, default=Path('reports/instances_preview.md'))
    parser.add_argument('--preview-n', type=int, default=20)
    args = parser.parse_args()
    args.levels = [level.strip() for level in args.levels.split(',')]
    return args


if __name__ == '__main__':
    main()
