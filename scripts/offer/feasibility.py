import argparse
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import numpy as np
from loguru import logger
from tqdm import tqdm

from commgym.core.config import load_config
from commgym.core.logging import setup_logging
from commgym.dunnhumby.clean import prepare_transactions
from commgym.dunnhumby.config import CleaningConfig, SplitsConfig
from commgym.dunnhumby.load import (
    CouponRedemption,
    load_campaign_targeting,
    load_campaigns,
    load_coupon_eligibility,
    load_coupon_redemptions,
    load_demographics,
    load_products,
    load_transactions,
)
from commgym.dunnhumby.load import (
    data_dir as default_data_dir,
)
from commgym.dunnhumby.splits import Splits, build_splits
from commgym.offer.config import TaskConfig
from commgym.offer.generator import (
    Anchor,
    OfferContext,
    build_offer_context,
    build_profile,
    sample_anchors,
)
from commgym.offer.lexicon import SYNONYMS, build_lexicon, normalize

SPLITS = ('train', 'dev', 'eval_unseen', 'eval_known')
NEEDED_ANCHORS = 50
SAMPLED_ANCHORS = 100
REDEMPTION_INDICATIVE = 0.05
AnchorsBySplit = dict[str, tuple[Anchor, ...]]


@dataclass(frozen=True, slots=True)
class CheckResult:
    name: str
    markdown: str
    go: bool | None  # None = report-only


def main() -> None:
    args = _parse_args()
    setup_logging()
    cfg = load_config(TaskConfig, args.task_config)
    root = args.data_dir if args.data_dir is not None else default_data_dir()
    logger.info('loading dataset from {}', root.resolve())
    products = load_products(root)
    tx = load_transactions(root)
    txc, _ = prepare_transactions(tx, products, load_config(CleaningConfig, args.cleaning_config))
    campaigns = load_campaigns(root)
    targeting = load_campaign_targeting(root)
    eligibility = load_coupon_eligibility(root)
    redemptions = load_coupon_redemptions(root)
    demographics = {row.household_key for row in load_demographics(root)}
    coverage = (
        txc.groupby(['commodity', 'WEEK_NO']).agg(n_skus=('PRODUCT_ID', 'nunique')).reset_index()
    )
    splits = build_splits(
        txc, demographics, coverage, load_config(SplitsConfig, args.splits_config)
    )
    logger.info('building offer context (coupon coverage, tiers, household frames)')
    ctx = build_offer_context(txc, products, campaigns, targeting, eligibility, cfg)
    commodity_names = sorted(
        {commodity for coverage in ctx.coupon_coverage.values() for commodity in coverage}
    )
    args.commodities_out.parent.mkdir(parents=True, exist_ok=True)
    args.commodities_out.write_text('\n'.join(commodity_names) + '\n')
    logger.info('wrote {} commodity names to {}', len(commodity_names), args.commodities_out)

    f1 = check_supply(ctx, splits, cfg)
    logger.info('sampling {} anchors per split for the distribution checks', SAMPLED_ANCHORS)
    anchors: AnchorsBySplit = {
        split: sample_anchors(ctx, splits.spec(split), SAMPLED_ANCHORS, cfg, seed=args.seed + i)
        for i, split in enumerate(SPLITS)
    }
    results = [
        f1,
        check_coupon_breadth(ctx),
        check_affinity_spread(ctx, anchors, cfg),
        check_redemption_signal(ctx, anchors, redemptions),
        check_tier_mix(ctx, anchors),
        check_lexicon(ctx),
        check_gate_feature_availability(ctx, anchors, cfg),
    ]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(_render(results))
    logger.info('feasibility report written to {}', args.out)
    failed = [result.name for result in results if result.go is False]
    logger.info('{}', 'GO' if not failed else f'NO-GO: {failed}')


def check_supply(ctx: OfferContext, splits: Splits, cfg: TaskConfig) -> CheckResult:
    """F1: (household, day) pairs and anchor supply at the 5/10/20-coupon thresholds."""
    thresholds = sorted({5, 10, cfg.pool_size})
    lines = [
        '| split | threshold | households | (hh, day) pairs | anchor supply (gap+cap) |',
        '|---|---|---|---|---|',
    ]
    go = False
    for split in SPLITS:
        spec = splits.spec(split)
        first_day, last_day = (spec.first_week - 1) * 7 + 1, spec.last_week * 7
        households = {t: 0 for t in thresholds}
        pairs = {t: 0 for t in thresholds}
        supply = {t: 0 for t in thresholds}
        for household in tqdm(
            sorted(spec.households & set(ctx.targeting)),
            desc=f'F1 {split}',
            unit='hh',
            leave=False,
        ):
            counts = ctx.live_coupon_counts(household, first_day, last_day)
            for threshold in thresholds:
                days = sorted(day for day, count in counts.items() if count >= threshold)
                if days:
                    households[threshold] += 1
                    pairs[threshold] += len(days)
                    supply[threshold] += _spread_capacity(days, cfg)
        for threshold in thresholds:
            lines.append(
                f'| {split} | {threshold} | {households[threshold]} | {pairs[threshold]} '
                f'| {supply[threshold]} |'
            )
            if threshold == cfg.pool_size and supply[threshold] >= NEEDED_ANCHORS:
                go = True
    return CheckResult('F1 instance supply', '\n'.join(lines), go)


def check_coupon_breadth(ctx: OfferContext) -> CheckResult:
    """F2: commodities and products covered per coupon."""
    commodities = [len(ctx.coupon_coverage[key]) for key in ctx.coupon_coverage]
    products = [ctx.coupon_products[key] for key in ctx.coupon_coverage]
    lines = [
        f'- coupons: {len(commodities)}',
        f'- commodities per coupon: median {int(np.median(commodities))}, '
        f'p90 {int(np.percentile(commodities, 90))}, max {max(commodities)}',
        f'- products per coupon: median {int(np.median(products))}, '
        f'p90 {int(np.percentile(products, 90))}, max {max(products)}',
    ]
    return CheckResult('F2 coupon breadth', '\n'.join(lines), None)


def check_affinity_spread(
    ctx: OfferContext, anchors: AnchorsBySplit, cfg: TaskConfig
) -> CheckResult:
    """F3: share of live coupons relevant to the household's history."""
    lines = ['| split | anchors | median relevant share | within 20-80% |', '|---|---|---|---|']
    medians = []
    for split, split_anchors in anchors.items():
        shares = []
        for anchor in tqdm(split_anchors, desc=f'F3 {split}', unit='anchor', leave=False):
            profile = build_profile(ctx.household_frames[anchor.household], anchor.day, cfg)
            live = ctx.live_keys(anchor.household, anchor.day)
            relevant = sum(1 for key in live if profile.mass(ctx.coupon_coverage[key]) > 0)
            shares.append(relevant / len(live))
        median = float(np.median(shares)) if shares else float('nan')
        medians.append(median)
        within = 'yes' if 0.2 <= median <= 0.8 else 'no'
        lines.append(f'| {split} | {len(shares)} | {median:.1%} | {within} |')
    ok = all(0.2 <= median <= 0.8 for median in medians if not np.isnan(median))
    return CheckResult('F3 affinity spread', '\n'.join(lines), ok)


def check_redemption_signal(
    ctx: OfferContext, anchors: AnchorsBySplit, redemptions: list[CouponRedemption]
) -> CheckResult:
    """F4: anchors where the household later redeems one of its live coupons."""
    by_household: dict[int, list[CouponRedemption]] = {}
    for row in redemptions:
        by_household.setdefault(row.household_key, []).append(row)
    lines = ['| split | anchors | with later redemption | share |', '|---|---|---|---|']
    shares = []
    for split, split_anchors in anchors.items():
        hits = 0
        for anchor in split_anchors:
            live = set(ctx.live_keys(anchor.household, anchor.day))
            hits += any(
                row.day > anchor.day and (row.campaign, row.coupon_upc) in live
                for row in by_household.get(anchor.household, ())
            )
        share = hits / len(split_anchors) if split_anchors else float('nan')
        shares.append(share)
        lines.append(f'| {split} | {len(split_anchors)} | {hits} | {share:.1%} |')
    total = float(np.mean([s for s in shares if not np.isnan(s)]))
    verdict = (
        'dense enough for the metric'
        if total >= REDEMPTION_INDICATIVE
        else f'below {REDEMPTION_INDICATIVE:.0%}: redemption hit is indicative only'
    )
    return CheckResult(
        'F4 redemption signal', '\n'.join(lines) + f'\n\nmean {total:.1%}; {verdict}', None
    )


def check_tier_mix(ctx: OfferContext, anchors: AnchorsBySplit) -> CheckResult:
    """F5: Private/National/Mixed across coupons and anchor availability."""
    tiers = Counter(ctx.coupon_tier.values())
    total = sum(tiers.values())
    lines = [
        'coupon tiers: '
        + ', '.join(f'{tier} {count} ({count / total:.0%})' for tier, count in tiers.most_common())
    ]
    for split, split_anchors in anchors.items():
        non_mixed = sum(
            1
            for anchor in split_anchors
            if any(
                ctx.coupon_tier[key] != 'Mixed'
                for key in ctx.live_keys(anchor.household, anchor.day)
            )
        )
        lines.append(
            f'- {split}: {non_mixed}/{len(split_anchors)} anchors with a non-Mixed live coupon'
        )
    return CheckResult('F5 brand-tier mix', '\n'.join(lines), None)


def check_lexicon(ctx: OfferContext) -> CheckResult:
    """F6: keyword collisions plus synonym-target coverage."""
    names = sorted(
        {commodity for coverage in ctx.coupon_coverage.values() for commodity in coverage}
    )
    name_set = {normalize(name) for name in names}
    lex = build_lexicon(names)
    missing = sorted({target for target in SYNONYMS.values() if normalize(target) not in name_set})
    lines = [
        f'- coupon-eligible commodities: {len(names)}',
        f'- keywords: {len(lex.keywords)}, collision rate {lex.collision_rate:.1%}',
        f'- synonym phrases: {len(SYNONYMS)}, unmatched targets: {len(missing)}',
    ]
    if missing:
        lines.append(f'- unmatched synonym targets (curate these): {", ".join(missing)}')
    return CheckResult('F6 lexicon collisions', '\n'.join(lines), None)


def check_gate_feature_availability(
    ctx: OfferContext, anchors: AnchorsBySplit, cfg: TaskConfig
) -> CheckResult:
    """F8: anchors with at least one ends-soon live coupon (urgency is checkable)."""
    lines = ['| split | anchors | with ends-soon coupon |', '|---|---|---|']
    for split, split_anchors in anchors.items():
        with_ends_soon = sum(
            1
            for anchor in split_anchors
            if any(
                ctx.campaign_by_id[key[0]].end_day - anchor.day <= cfg.ends_soon_days
                for key in ctx.live_keys(anchor.household, anchor.day)
            )
        )
        lines.append(f'| {split} | {len(split_anchors)} | {with_ends_soon} |')
    return CheckResult('F8 gate feature availability', '\n'.join(lines), None)


def _spread_capacity(days: list[int], cfg: TaskConfig) -> int:
    """Earliest-first greedy: the max anchor days this household can contribute."""
    picked = 0
    last: int | None = None
    for day in days:
        if last is None or day - last >= cfg.min_anchor_gap_days:
            picked += 1
            last = day
            if picked == cfg.max_instances_per_hh:
                break
    return picked


def _render(results: list[CheckResult]) -> str:
    lines = [
        '# Offer Task Feasibility',
        '',
        f'- generated: {datetime.now().isoformat(timespec="seconds")}',
        '',
    ]
    for result in results:
        verdict = 'GO' if result.go else 'REPORT' if result.go is None else 'NO-GO'
        lines += [f'## {result.name} — {verdict}', '', result.markdown, '']
    return '\n'.join(lines)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Offer-message task feasibility checks F1-F8')
    parser.add_argument('--data-dir', type=Path, default=None)
    parser.add_argument('--task-config', type=Path, default=Path('configs/offer/task.yaml'))
    parser.add_argument('--cleaning-config', type=Path, default=Path('configs/data.yaml'))
    parser.add_argument('--splits-config', type=Path, default=Path('configs/splits.yaml'))
    parser.add_argument('--out', type=Path, default=Path('reports/offer/offer_feasibility.md'))
    parser.add_argument(
        '--commodities-out',
        type=Path,
        default=Path('configs/offer/commodities.txt'),
        help='all coupon-eligible commodity names; gate and prompts build their lexicon from this',
    )
    parser.add_argument('--seed', type=int, default=42)
    return parser.parse_args()


if __name__ == '__main__':
    main()
