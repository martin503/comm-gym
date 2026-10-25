import argparse
import math
import sys
import zlib
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from loguru import logger
from tqdm import tqdm

from commgym.core.config import load_config
from commgym.core.logging import setup_logging
from commgym.dunnhumby.clean import prepare_transactions
from commgym.dunnhumby.config import CleaningConfig, PricingConfig, SplitsConfig
from commgym.dunnhumby.load import (
    load_campaign_targeting,
    load_campaigns,
    load_coupon_eligibility,
    load_coupon_redemptions,
    load_demographics,
    load_products,
    load_transactions,
)
from commgym.dunnhumby.prices import build_price_table
from commgym.dunnhumby.splits import CampaignCalendar, Splits, SplitSpec, build_splits
from commgym.dunnhumby.types import BrandTier
from commgym.refund.coupons import CouponIndex, build_coupon_index, live_upcs, typical_value
from commgym.refund.instance import ReceiptLine
from commgym.refund.lexicon import unique_reference, words_of

# Pre-registered gates (plan step 1); the script runs once and applies them verbatim.
# Permitted one-shot fallbacks: G1 re-picks tolerance by the grid rule; G3 may drop
# ALREADY_APPLIED per the plan. A second failure stops the task.
TOLERANCE_GRID_CENTS = (5, 10, 15, 25, 50)
TOLERANCE_PICK_CAP = 0.45
G2_MIN_LINES, G2_MIN_BASKETS = 2000, 800
G3_MIN_LINES, G3_MIN_BASKETS = 120, 80
G4_MIN_COUPON, G4_MIN_COUPON_OR_CAMP = 0.25, 0.60
G6_MIN_FIT, G6_MEAN_TOKENS, G6_P95_TOKENS = 0.90, 2800.0, 4200.0
G7_MIN_LINES, G7_MIN_MISSED = 0.80, 0.85
# Recheck rules, pre-registered 2026-10-23 with the user after the original G1/G5 failed:
# G1's 15-50% share band came from an impossible calibration (no more than half of lines can sit
# above their own product-week median), so it becomes an absolute supply gate at the grid-picked
# tolerance. Tolerance stays the grid rule's pick; a failure drops the task.
G1R_MIN_LINES, G1R_MIN_BASKETS = 500, 250
# Decision 2026-10-23, after G5R (90% of baskets with >= 3 resolvable targets) failed at 60%:
# no further gate changes for this task. Breadth is not a validity requirement (supply passes
# 100x); anchors are drawn from the >= 3-resolvable subset and the selection effect is reported
# as selected-vs-all comparisons. Any future validity-gate failure (label correctness, supply)
# means drop.
ANCHOR_MIN_TARGET_LINES = 3
LADDER_SAMPLE_BASKETS = 2000
PROMPT_SAMPLE_BASKETS = 500
TOKENS_PER_CHAR = 4  # fixed chars/4 estimate: no tokenizer dependency at this stage
FIXED_PROMPT_CHARS = 1400  # policy text + headers + message outside the two tables
SIDES = ('train', 'dev', 'eval_known', 'eval_unseen')
EVAL_SIDES = ('eval_known', 'eval_unseen')

RECEIPT_HEADER = (
    '| line | category | sub-category | brand tier | size | qty | regular unit | '
    'loyalty disc | coupon disc | paid | reference |\n'
)
STYLES = ('noun', 'brand_tier', 'size', 'quantity', 'unresolvable')


@dataclass(frozen=True, slots=True)
class BasketRecord:
    """Per-basket counters on the sampled baskets, for the selected-vs-all comparison."""

    n_lines: int
    resolved: int
    price_eligible: int
    missed: int
    applied: int
    covered: int
    over: tuple[int, ...]  # overcharge line count per grid tolerance, grid order


@dataclass(frozen=True, slots=True)
class LineMasks:
    """Per-line boolean masks aligned with the side frame, for per-basket counting."""

    price_eligible: np.ndarray
    missed: np.ndarray
    applied: np.ndarray
    covered: np.ndarray
    over_by_tol: dict[int, np.ndarray]


@dataclass(frozen=True, slots=True)
class SideStats:
    name: str
    n_lines: int
    n_baskets: int
    lexicon_share: float
    has_ref_share: float
    coupon_covered_share: float
    overcharge_shares: dict[int, float]
    over_counts: dict[int, tuple[int, int]]
    missed_lines: int
    missed_baskets: int
    applied_lines: int
    applied_baskets: int
    missed_lexicon_share: float
    provenance: dict[str, int]
    fit_share: float
    resolvable_share: float
    anchor_ready_share: float
    basket_records: tuple[BasketRecord, ...]
    style_hist: dict[str, int]
    ladder_lines: int
    tokens_mean: float
    tokens_p95: float
    prompt_baskets: int


def main() -> None:
    args = _parse_args()
    setup_logging()
    txc, splits, index, live_ids_by_day, prices_ref, last_day = _load(args)
    stats: dict[str, SideStats] = {}
    for name in SIDES:
        stats[name] = _side_pass(txc, splits.spec(name), index, live_ids_by_day, prices_ref, args)
    tolerance, gates = _gates(stats)
    _write_report(args, stats, tolerance, gates, last_day)
    for name, ok, detail in gates:
        level = logger.success if ok else logger.error
        level('gate {}: {} ({})', name, 'PASS' if ok else 'FAIL', detail)
    failed = [name for name, ok, _ in gates if not ok]
    if failed:
        logger.error('feasibility gate failed ({}); stopping per the pre-registered rule', failed)
        sys.exit(1)
    logger.success('all feasibility gates passed; price tolerance frozen at {}c', tolerance)


def _load(
    args: argparse.Namespace,
) -> tuple[pd.DataFrame, Splits, CouponIndex, dict[int, tuple[int, ...]], pd.DataFrame, int]:
    products = load_products(args.data_dir)
    tx = load_transactions(args.data_dir)
    txc, _ = prepare_transactions(tx, products, load_config(CleaningConfig, args.cleaning_config))
    product_sizes = pd.DataFrame(
        {'product_id': [p.product_id for p in products], 'size': [p.size for p in products]}
    )
    txc = txc.merge(product_sizes, left_on='PRODUCT_ID', right_on='product_id').drop(
        columns='product_id'
    )
    prices = build_price_table(txc, load_config(PricingConfig, args.pricing_config))
    prices_ref = pd.DataFrame(
        [
            (product, week, point.shelf_cents - point.loyalty_disc_cents)
            for (product, week), point in prices.items()
        ],
        columns=['PRODUCT_ID', 'WEEK_NO', 'ref_cents'],
    )
    campaigns = tuple(load_campaigns(args.data_dir))
    calendar = CampaignCalendar(campaigns)
    live_ids_by_day = {
        day: tuple(sorted(c.campaign for c in calendar.live_campaigns(day)))
        for day in range(1, int(txc['DAY'].max()) + 1)
    }
    index = build_coupon_index(
        load_coupon_eligibility(args.data_dir),
        list(campaigns),
        load_campaign_targeting(args.data_dir),
        load_coupon_redemptions(args.data_dir),
        txc,
        min_redemptions=args.min_redemptions,
    )
    demographics = {d.household_key for d in load_demographics(args.data_dir)}
    coverage = (
        txc.groupby(['commodity', 'WEEK_NO']).agg(n_skus=('PRODUCT_ID', 'nunique')).reset_index()
    )
    splits = build_splits(
        txc, demographics, coverage, load_config(SplitsConfig, args.splits_config)
    )
    return txc, splits, index, live_ids_by_day, prices_ref, int(txc['DAY'].max())


def _side_pass(
    txc: pd.DataFrame,
    spec: SplitSpec,
    index: CouponIndex,
    live_ids_by_day: dict[int, tuple[int, ...]],
    prices_ref: pd.DataFrame,
    args: argparse.Namespace,
) -> SideStats:
    """Per-line price features, the coupon-coverage walk, and sampled ladder/token stats."""
    live_days = frozenset(day for day, ids in live_ids_by_day.items() if ids)
    side = (
        txc[
            txc['household_key'].isin(spec.households)
            & txc['WEEK_NO'].between(spec.first_week, spec.last_week)
            & txc['DAY'].isin(live_days)
        ]
        .merge(prices_ref, on=['PRODUCT_ID', 'WEEK_NO'], how='left')
        .reset_index(drop=True)
    )
    lexicon = side['commodity'].map(lambda c: bool(words_of(str(c)))).to_numpy()
    has_ref = side['ref_cents'].notna().to_numpy()
    regular_c = (side['regular_unit'] * 100).round().to_numpy(dtype='int64')
    loyalty_disc_c = (
        ((side['regular_unit'] - side['loyalty_unit']) * 100).round().to_numpy(dtype='int64')
    )
    loyalty_c = regular_c - loyalty_disc_c
    diff = loyalty_c - side['ref_cents'].fillna(0).to_numpy(dtype='int64')
    zero_disc = (side['COUPON_DISC'] + side['COUPON_MATCH_DISC'] == 0).to_numpy()
    price_eligible = lexicon & has_ref & zero_disc
    overcharge_shares = {
        tol: float((diff[price_eligible] > tol).mean()) if price_eligible.any() else 0.0
        for tol in TOLERANCE_GRID_CENTS
    }

    hh = side['household_key'].to_numpy()
    day = side['DAY'].to_numpy()
    pid = side['PRODUCT_ID'].to_numpy()
    basket = side['BASKET_ID'].to_numpy()
    over_counts = {
        tol: (
            int((price_eligible & (diff > tol)).sum()),
            int(np.unique(basket[price_eligible & (diff > tol)]).size),
        )
        for tol in TOLERANCE_GRID_CENTS
    }
    covered = np.zeros(len(side), dtype=bool)
    encountered: set[int] = set()
    live_cache: dict[tuple[int, tuple[int, ...]], frozenset[int]] = {}
    for i in tqdm(range(len(side)), desc=f'{spec.name} lines', unit='line'):
        key = (int(hh[i]), live_ids_by_day[int(day[i])])
        live_set = live_cache.get(key)
        if live_set is None:
            live_set = live_upcs(index, int(hh[i]), int(day[i]))
            live_cache[key] = live_set
        ups = index.product_upcs.get(int(pid[i]))
        if ups:
            hitting = ups & live_set
            if hitting:
                covered[i] = True
                encountered.update(hitting)
    missed_mask = lexicon & covered & zero_disc
    applied_mask = lexicon & covered & ~zero_disc
    missed_any = covered & zero_disc
    provenance: dict[str, int] = {}
    for upc in encountered:
        _, source = typical_value(index, upc)
        provenance[source] = provenance.get(source, 0) + 1

    sizes = side.groupby('BASKET_ID').size()
    fit_share = float((sizes <= args.max_receipt_lines).mean())
    masks = LineMasks(
        price_eligible=price_eligible,
        missed=missed_mask,
        applied=applied_mask,
        covered=covered,
        over_by_tol={tol: price_eligible & (diff > tol) for tol in TOLERANCE_GRID_CENTS},
    )
    candidates = sizes[sizes <= args.max_receipt_lines].index.to_numpy()
    rng = np.random.default_rng(zlib.crc32(f'{args.seed}-{spec.name}'.encode()) % (2**32 - 1))
    sampled = rng.choice(candidates, size=min(args.ladder_sample, len(candidates)), replace=False)
    (
        resolvable,
        ready_share,
        style_hist,
        ladder_lines,
        tokens_mean,
        tokens_p95,
        prompt_n,
        records,
    ) = _sample_stats(side, sampled.tolist(), lexicon, index, args, masks)
    return SideStats(
        name=spec.name,
        n_lines=len(side),
        n_baskets=len(sizes),
        lexicon_share=float(lexicon.mean()),
        has_ref_share=float(has_ref.mean()),
        coupon_covered_share=float(covered.mean()),
        overcharge_shares=overcharge_shares,
        over_counts=over_counts,
        missed_lines=int(missed_mask.sum()),
        missed_baskets=int(np.unique(basket[missed_mask]).size),
        applied_lines=int(applied_mask.sum()),
        applied_baskets=int(np.unique(basket[applied_mask]).size),
        missed_lexicon_share=(
            float(missed_mask.sum() / missed_any.sum()) if missed_any.any() else 0.0
        ),
        provenance=provenance,
        fit_share=fit_share,
        resolvable_share=resolvable,
        anchor_ready_share=ready_share,
        basket_records=records,
        style_hist=style_hist,
        ladder_lines=ladder_lines,
        tokens_mean=tokens_mean,
        tokens_p95=tokens_p95,
        prompt_baskets=prompt_n,
    )


def _sample_stats(
    side: pd.DataFrame,
    sampled: list[int],
    lexicon: np.ndarray,
    index: CouponIndex,
    args: argparse.Namespace,
    masks: LineMasks,
) -> tuple[float, float, dict[str, int], int, float, float, int, tuple[BasketRecord, ...]]:
    """Ladder resolvability, per-basket records, and token estimates on a seeded sample."""
    sample_frame = side[side['BASKET_ID'].isin(set(sampled))]
    style_hist = {style: 0 for style in STYLES}
    attempted = 0
    ready = 0
    tokens: list[int] = []
    records: list[BasketRecord] = []
    for _, group in tqdm(
        sample_frame.groupby('BASKET_ID', sort=False), desc='ladder sample', unit='basket'
    ):
        lines = _receipt_lines(group)
        idx = group.index.to_numpy()
        covered_flags = lexicon[idx]
        resolved_in_basket = 0
        for line, covered_line in zip(lines, covered_flags, strict=True):
            if not covered_line:
                continue
            attempted += 1
            found = unique_reference(line, lines)
            style_hist[found[1] if found else 'unresolvable'] += 1
            if found:
                resolved_in_basket += 1
        ready += resolved_in_basket >= ANCHOR_MIN_TARGET_LINES
        records.append(
            BasketRecord(
                n_lines=len(lines),
                resolved=resolved_in_basket,
                price_eligible=int(masks.price_eligible[idx].sum()),
                missed=int(masks.missed[idx].sum()),
                applied=int(masks.applied[idx].sum()),
                covered=int(masks.covered[idx].sum()),
                over=tuple(int(masks.over_by_tol[tol][idx].sum()) for tol in TOLERANCE_GRID_CENTS),
            )
        )
        if len(tokens) < args.prompt_sample:
            tokens.append(_token_estimate(group, lines, index))
    n_baskets = sample_frame['BASKET_ID'].nunique()
    resolvable = 1.0 - style_hist['unresolvable'] / attempted if attempted else 0.0
    ready_share = ready / n_baskets if n_baskets else 0.0
    arr = np.array(tokens) if tokens else np.zeros(1, dtype=int)
    return (
        resolvable,
        ready_share,
        style_hist,
        attempted,
        float(arr.mean()),
        float(np.percentile(arr, 95)),
        len(tokens),
        tuple(records),
    )


def _receipt_lines(group: pd.DataFrame) -> list[ReceiptLine]:
    """Build display-cents receipt lines; paid = regular - loyalty disc - coupon disc exactly."""
    lines: list[ReceiptLine] = []
    for i, (_, row) in enumerate(group.iterrows()):
        regular = int(round(float(row['regular_unit']) * 100))
        loyalty_disc = min(
            max(int(round((float(row['regular_unit']) - float(row['loyalty_unit'])) * 100)), 0),
            regular,
        )
        room = regular - loyalty_disc
        coupon_disc = min(
            max(
                int(
                    round(
                        -(float(row['COUPON_DISC']) + float(row['COUPON_MATCH_DISC']))
                        / int(row['QUANTITY'])
                        * 100
                    )
                ),
                0,
            ),
            room,
        )
        ref = int(row['ref_cents']) if pd.notna(row['ref_cents']) else 0
        lines.append(
            ReceiptLine(
                code=f'L{i + 1:02d}',
                product_id=int(row['PRODUCT_ID']),
                commodity=str(row['commodity']),
                sub_commodity=str(row['sub_commodity']),
                brand_tier=BrandTier(str(row['brand'])),
                size=str(row['size']) if pd.notna(row['size']) else '',
                quantity=int(row['QUANTITY']),
                regular_unit_cents=regular,
                loyalty_disc_unit_cents=loyalty_disc,
                coupon_disc_unit_cents=coupon_disc,
                paid_unit_cents=room - coupon_disc,
                reference_cents=ref,
            )
        )
    return lines


def _token_estimate(group: pd.DataFrame, lines: list[ReceiptLine], index: CouponIndex) -> int:
    household = int(group['household_key'].iloc[0])
    day = int(group['DAY'].iloc[0])
    live_set = live_upcs(index, household, day)
    shown = sorted(
        {
            upc
            for line in lines
            for upc in index.product_upcs.get(line.product_id, frozenset()) & live_set
        }
    )
    chars = len(RECEIPT_HEADER) + FIXED_PROMPT_CHARS
    for line in lines:
        chars += len(
            f'| {line.code} | {line.commodity} | {line.sub_commodity} |'
            f' {line.brand_tier.value} | {line.size} | {line.quantity} |'
            f' ${line.regular_unit_cents / 100:.2f} | ${line.loyalty_disc_unit_cents / 100:.2f} |'
            f' ${line.coupon_disc_unit_cents / 100:.2f} | ${line.paid_unit_cents / 100:.2f} |'
            f' ${line.reference_cents / 100:.2f} |\n'
        )
    for i, upc in enumerate(shown):
        value, _ = typical_value(index, upc)
        covers = [
            line.code
            for line in lines
            if upc in index.product_upcs.get(line.product_id, frozenset())
        ]
        chars += len(f'| C{i + 1:02d} | ${value / 100:.2f} | {",".join(covers)} |\n')
    return math.ceil(chars / TOKENS_PER_CHAR)


def _gates(stats: dict[str, SideStats]) -> tuple[int, list[tuple[str, bool, str]]]:
    eval_stats = [stats[name] for name in EVAL_SIDES]
    tolerance = TOLERANCE_GRID_CENTS[-1]
    for tol in TOLERANCE_GRID_CENTS:
        if all(s.overcharge_shares[tol] <= TOLERANCE_PICK_CAP for s in eval_stats):
            tolerance = tol
            break
    shares = [s.overcharge_shares[tolerance] for s in eval_stats]
    gates: list[tuple[str, bool, str]] = [
        (
            f'G1R overcharge supply at {tolerance}c: >= 500 lines in >= 250 baskets',
            all(
                s.over_counts[tolerance][0] >= G1R_MIN_LINES
                and s.over_counts[tolerance][1] >= G1R_MIN_BASKETS
                for s in eval_stats
            ),
            '; '.join(
                f'{s.name}: {s.over_counts[tolerance][0]}/{s.over_counts[tolerance][1]}'
                for s in eval_stats
            )
            + f' (shares {"; ".join(f"{share:.1%}" for share in shares)})',
        ),
        (
            'G2 missed-coupon lines >= 2000 in >= 800 baskets',
            all(
                s.missed_lines >= G2_MIN_LINES and s.missed_baskets >= G2_MIN_BASKETS
                for s in eval_stats
            ),
            '; '.join(f'{s.name}: {s.missed_lines}/{s.missed_baskets}' for s in eval_stats),
        ),
        (
            'G3 already-applied lines >= 120 in >= 80 baskets',
            all(
                s.applied_lines >= G3_MIN_LINES and s.applied_baskets >= G3_MIN_BASKETS
                for s in eval_stats
            ),
            '; '.join(f'{s.name}: {s.applied_lines}/{s.applied_baskets}' for s in eval_stats),
        ),
        (
            'G4 coupon-level >= 25% and coupon-or-campaign >= 60% of live covering coupons',
            all(_g4_side_ok(s) for s in eval_stats),
            '; '.join(f'{s.name}: {s.provenance}' for s in eval_stats),
        ),
        (
            'G6 basket fit >= 90%, mean tokens <= 2800, p95 <= 4200',
            all(
                s.fit_share >= G6_MIN_FIT
                and s.tokens_mean <= G6_MEAN_TOKENS
                and s.tokens_p95 <= G6_P95_TOKENS
                for s in eval_stats
            ),
            '; '.join(
                f'{s.name}: fit {s.fit_share:.1%}, tok {s.tokens_mean:.0f}/{s.tokens_p95:.0f}'
                for s in eval_stats
            ),
        ),
        (
            'G7 lexicon covers >= 80% of lines, >= 85% of missed-coupon lines',
            all(
                s.lexicon_share >= G7_MIN_LINES and s.missed_lexicon_share >= G7_MIN_MISSED
                for s in eval_stats
            ),
            '; '.join(
                f'{s.name}: {s.lexicon_share:.1%}/{s.missed_lexicon_share:.1%}' for s in eval_stats
            ),
        ),
    ]
    return tolerance, gates


def _g4_side_ok(s: SideStats) -> bool:
    total = sum(s.provenance.values())
    if not total:
        return False
    coupon = s.provenance.get('coupon', 0) / total
    coupon_or_campaign = coupon + s.provenance.get('campaign', 0) / total
    return coupon >= G4_MIN_COUPON and coupon_or_campaign >= G4_MIN_COUPON_OR_CAMP


def _write_report(
    args: argparse.Namespace,
    stats: dict[str, SideStats],
    tolerance: int,
    gates: list[tuple[str, bool, str]],
    last_day: int,
) -> None:
    lines = [
        '# Refund-claim feasibility report',
        '',
        f'max receipt lines {args.max_receipt_lines}, min redemptions {args.min_redemptions},'
        f' seed {args.seed}, last day {last_day},'
        f' ladder sample {args.ladder_sample} baskets/side'
        f' ({args.prompt_sample} token-estimated), tokens = chars/4',
        '',
        '## Per-side supply',
        '',
        '| side | lines | baskets | lexicon | has ref | coup-cov | missed | applied | fit |',
        '|---|---|---|---|---|---|---|---|---|',
    ]
    for s in stats.values():
        lines.append(
            f'| {s.name} | {s.n_lines} | {s.n_baskets} | {s.lexicon_share:.1%}'
            f' | {s.has_ref_share:.1%} | {s.coupon_covered_share:.1%}'
            f' | {s.missed_lines} ({s.missed_baskets}b) | {s.applied_lines} ({s.applied_baskets}b)'
            f' | {s.fit_share:.1%} |'
        )
    lines += [
        '',
        '## F1: overcharge share among price-eligible lines by tolerance',
        '',
        '| side | ' + ' | '.join(f'{t}c' for t in TOLERANCE_GRID_CENTS) + ' |',
        '|' + '---|' * (len(TOLERANCE_GRID_CENTS) + 1),
    ]
    for s in stats.values():
        lines.append(
            f'| {s.name} | '
            + ' | '.join(f'{s.overcharge_shares[t]:.1%}' for t in TOLERANCE_GRID_CENTS)
            + ' |'
        )
    lines += [
        '',
        f'Chosen tolerance (smallest grid value with share <= {TOLERANCE_PICK_CAP:.0%} on both'
        f' eval sides): **{tolerance}c** — frozen as the task `price_tolerance_cents`.'
        ' Overcharge supply (lines/baskets): '
        + '; '.join(
            f'{s.name} {s.over_counts[tolerance][0]}/{s.over_counts[tolerance][1]}'
            for s in stats.values()
        )
        + '.',
        '',
        '## F4: typical-value provenance of live covering coupons',
        '',
    ]
    for s in stats.values():
        total = sum(s.provenance.values())
        if total:
            parts = ', '.join(
                f'{k} {v} ({v / total:.1%})' for k, v in sorted(s.provenance.items())
            )
            lines.append(f'- {s.name}: {parts}')
        else:
            lines.append(f'- {s.name}: no covering coupons encountered')
    lines += [
        '',
        '## F5/F6: reference ladder and prompt size (sampled baskets)',
        '',
        '| side | resolvable | ready >= 3 | noun | tier | size | qty | unres. | tok mean | p95 |',
        '|---|---|---|---|---|---|---|---|---|---|',
    ]
    for s in stats.values():
        lines.append(
            f'| {s.name} | {s.resolvable_share:.1%} | {s.anchor_ready_share:.1%}'
            f' | {s.style_hist["noun"]}'
            f' | {s.style_hist["brand_tier"]} | {s.style_hist["size"]}'
            f' | {s.style_hist["quantity"]} | {s.style_hist["unresolvable"]}'
            f' | {s.tokens_mean:.0f} | {s.tokens_p95:.0f} |'
        )
    lines += [
        '',
        'Note: QUANTITY is int32 in the raw data, so all lines carry unit counts;'
        ' quantity-outlier (weight-priced) lines are dropped by cleaning.',
        '',
        '## Selection effect: anchors = baskets with >= 3 resolvable targets',
        '',
        'G5R (90% breadth) failed at ~60%; per the 2026-10-23 decision it is documented as a'
        ' selection effect rather than a gate. Anchors are drawn from the selected pool only.',
        '',
        '| side | pool | baskets | lines mean/med | missed/b | applied/b | cov | overcharge |',
        '|---|---|---|---|---|---|---|---|',
    ]
    tol_index = TOLERANCE_GRID_CENTS.index(tolerance)
    for s in stats.values():
        for pool in ('all', 'selected'):
            subset = (
                list(s.basket_records)
                if pool == 'all'
                else [r for r in s.basket_records if r.resolved >= ANCHOR_MIN_TARGET_LINES]
            )
            n = len(subset)
            if not n:
                continue
            line_counts = [r.n_lines for r in subset]
            price_lines = sum(r.price_eligible for r in subset)
            over_lines = sum(r.over[tol_index] for r in subset)
            lines.append(
                f'| {s.name} | {pool} | {n} | {np.mean(line_counts):.1f}'
                f'/{np.median(line_counts):.0f}'
                f' | {sum(r.missed for r in subset) / n:.2f}'
                f' | {sum(r.applied for r in subset) / n:.2f}'
                f' | {sum(r.covered for r in subset) / sum(line_counts):.1%}'
                f' | {over_lines / price_lines:.1%} |'
            )
    lines += [
        '',
        '## Gates',
        '',
    ]
    lines += [f'- {name}: {"PASS" if ok else "FAIL"} — {detail}' for name, ok, detail in gates]
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text('\n'.join(lines) + '\n')
    logger.info('feasibility report written to {}', args.report)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Run refund-claim feasibility checks F1-F7')
    parser.add_argument('--data-dir', type=Path, default=None)
    parser.add_argument('--cleaning-config', type=Path, default=Path('configs/data.yaml'))
    parser.add_argument('--pricing-config', type=Path, default=Path('configs/pricing.yaml'))
    parser.add_argument('--splits-config', type=Path, default=Path('configs/splits.yaml'))
    parser.add_argument('--min-redemptions', type=int, default=2)
    parser.add_argument('--max-receipt-lines', type=int, default=40)
    parser.add_argument('--ladder-sample', type=int, default=LADDER_SAMPLE_BASKETS)
    parser.add_argument('--prompt-sample', type=int, default=PROMPT_SAMPLE_BASKETS)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument(
        '--report',
        type=Path,
        default=Path('experiments/261023_refund_feasibility/feasibility_final.md'),
    )
    return parser.parse_args()


if __name__ == '__main__':
    main()
