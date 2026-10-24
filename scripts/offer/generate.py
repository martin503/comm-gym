import argparse
import json
import zlib
from pathlib import Path

import numpy as np
from loguru import logger

from commgym.core.config import load_config
from commgym.core.logging import setup_logging
from commgym.dunnhumby.clean import prepare_transactions
from commgym.dunnhumby.config import CleaningConfig, SplitsConfig
from commgym.dunnhumby.load import (
    data_dir as default_data_dir,
)
from commgym.dunnhumby.load import (
    load_campaign_targeting,
    load_campaigns,
    load_coupon_eligibility,
    load_demographics,
    load_products,
    load_transactions,
)
from commgym.dunnhumby.splits import build_splits
from commgym.offer.config import TaskConfig
from commgym.offer.generator import (
    build_instance,
    build_offer_context,
    instance_to_record,
    render_preview,
    sample_anchors,
)


def main() -> None:
    args = _parse_args()
    setup_logging()
    cfg = load_config(TaskConfig, args.task_config)
    root = args.data_dir if args.data_dir is not None else default_data_dir()
    products = load_products(root)
    tx = load_transactions(root)
    txc, _ = prepare_transactions(tx, products, load_config(CleaningConfig, args.cleaning_config))
    demographics = {row.household_key for row in load_demographics(root)}
    coverage = (
        txc.groupby(['commodity', 'WEEK_NO']).agg(n_skus=('PRODUCT_ID', 'nunique')).reset_index()
    )
    splits = build_splits(
        txc, demographics, coverage, load_config(SplitsConfig, args.splits_config)
    )
    ctx = build_offer_context(
        txc,
        products,
        load_campaigns(root),
        load_campaign_targeting(root),
        load_coupon_eligibility(root),
        cfg,
    )
    seed = zlib.crc32(f'{args.seed}-{args.split}'.encode())
    anchors = sample_anchors(ctx, splits.spec(args.split), args.n, cfg, seed)
    logger.info('sampled {} anchors for {}', len(anchors), args.split)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    out_path = args.out_dir / f'{args.split}.jsonl'
    previews = []
    with out_path.open('w') as f:
        for anchor in anchors:
            rng = np.random.default_rng(
                zlib.crc32(f'{seed}-{anchor.household}-{anchor.day}'.encode())
            )
            instance = build_instance(ctx, anchor, args.split, cfg, rng)
            f.write(json.dumps(instance_to_record(instance).model_dump()) + '\n')
            previews.append(render_preview(instance))
    logger.info('wrote {} instances to {}', len(anchors), out_path)
    args.preview.parent.mkdir(parents=True, exist_ok=True)
    kept = previews[: args.preview_n]
    args.preview.write_text('# Offer instance preview\n\n' + '\n\n---\n\n'.join(kept))
    logger.info('preview of {} instances written to {}', len(kept), args.preview)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Generate offer-message instances for one split')
    parser.add_argument(
        '--split', default='dev', choices=['train', 'dev', 'eval_unseen', 'eval_known']
    )
    parser.add_argument('--n', type=int, default=50, help='anchors (one instance each)')
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--data-dir', type=Path, default=None)
    parser.add_argument('--task-config', type=Path, default=Path('configs/offer/task.yaml'))
    parser.add_argument('--cleaning-config', type=Path, default=Path('configs/data.yaml'))
    parser.add_argument('--splits-config', type=Path, default=Path('configs/splits.yaml'))
    parser.add_argument('--out-dir', type=Path, default=Path('instances/offer'))
    parser.add_argument('--preview', type=Path, default=Path('reports/offer_instances_preview.md'))
    parser.add_argument('--preview-n', type=int, default=10)
    return parser.parse_args()


if __name__ == '__main__':
    main()
