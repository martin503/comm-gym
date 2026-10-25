import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from loguru import logger
from tqdm import tqdm

from commgym.core.config import load_config
from commgym.core.logging import setup_logging
from commgym.dunnhumby.clean import prepare_transactions
from commgym.dunnhumby.config import CleaningConfig, SplitsConfig
from commgym.dunnhumby.load import load_demographics, load_products, load_transactions
from commgym.dunnhumby.splits import Splits, SplitSpec, build_splits
from commgym.replenish.baselines import irls_logistic, logistic_probs
from commgym.replenish.config import TaskConfig
from commgym.replenish.history import (
    HouseholdHistory,
    anchor_grid,
    build_histories,
    day_supply,
    extract_pairs,
    sample_anchors,
)

FEATURES = (
    'weekly_rate',
    'days_since_last',
    'mean_interval',
    'interval_std',
    'n_prior',
    'staple',
    'hh_trip_rate',
)
SUPPLY_THRESHOLDS = (10, 20, 25, 30)
MIN_INTERVAL_DAYS = 7.0  # clamp: two purchases days apart must not blow up due-date math
DUE_BIN_NAMES = (
    'lapsed (>1 gap overdue)',
    'overdue',
    'due in window (0-6)',
    'due 7-14',
    'due later',
)
STRATA = ('2', '3-4', '5+')


@dataclass(frozen=True, slots=True)
class Skill:
    point: float
    lo: float
    hi: float


@dataclass(frozen=True, slots=True)
class PairStats:
    n_train: int
    n_dev: int
    n_dev4: int
    positive_rate: float
    near_det_share: float
    staple_share: float
    brier_constant: float
    brier_weekly: float
    brier_lr: float
    skill_weekly: Skill
    skill_lr: Skill
    skill_lr_4: Skill
    p_window_4: float
    p_after_4: float
    due_curves: tuple[tuple[str, tuple[tuple[str, float, int], ...]], ...]
    zero_positive_instances: float
    all_positive_instances: float
    mean_candidates: float
    mean_positives: float


def main() -> None:
    args = _parse_args()
    setup_logging()
    cfg = TaskConfig(
        granularity=args.granularity,
        history_days=args.history_days,
        min_purchases=args.min_purchases,
        min_history_trips=args.min_history_trips,
    )
    txc, splits, cutoff_day, last_day = _load(args)
    logger.info(
        'cutoff day {}, last day {}, history {}d, horizon {}d, gate {} candidates',
        cutoff_day,
        last_day,
        cfg.history_days,
        cfg.horizon_days,
        args.gate,
    )
    histories = build_histories(txc, cfg.granularity)
    logger.info('built histories for {} households', len(histories))
    side_stats: dict[str, dict[str, float]] = {}
    pair_frames: list[pd.DataFrame] = []
    for name in ('train', 'dev', 'eval_known', 'eval_unseen'):
        spec = splits.spec(name)
        grid = anchor_grid(
            cfg, 'train' if name in ('train', 'dev') else 'eval', cutoff_day, last_day
        )
        stats, pairs = _side_pass(
            histories, spec, grid, cfg, args, collect_pairs=name in ('train', 'dev')
        )
        side_stats[name] = stats
        if pairs is not None:
            pairs['side'] = name
            pair_frames.append(pairs)
    pairs = pd.concat(pair_frames, ignore_index=True)
    train, dev = pairs[pairs['side'] == 'train'], pairs[pairs['side'] == 'dev']
    logger.info('sampled pairs: {} train, {} dev', len(train), len(dev))
    results = _pair_stats(train, dev, seed=args.seed, resamples=args.resamples)
    gates = _gates(results)
    _write_report(args, cfg, side_stats, results, gates)
    for name, ok in gates:
        (logger.success if ok else logger.error)('gate {}: {}', name, 'PASS' if ok else 'FAIL')
    failed = [name for name, ok in gates if not ok]
    if failed:
        logger.error(
            'feasibility gate failed ({}); adjust one parameter or stop', ', '.join(failed)
        )
        sys.exit(1)
    logger.success('all feasibility gates passed')


def _load(args: argparse.Namespace) -> tuple[pd.DataFrame, Splits, int, int]:
    products = load_products(args.data_dir)
    tx = load_transactions(args.data_dir)
    txc, _ = prepare_transactions(tx, products, load_config(CleaningConfig, args.cleaning_config))
    demographics = {d.household_key for d in load_demographics(args.data_dir)}
    coverage = (
        txc.groupby(['commodity', 'WEEK_NO']).agg(n_skus=('PRODUCT_ID', 'nunique')).reset_index()
    )
    splits_cfg = load_config(SplitsConfig, args.splits_config)
    splits = build_splits(txc, demographics, coverage, splits_cfg)
    return txc, splits, splits_cfg.cutoff_week * 7, int(txc['DAY'].max())


def _side_pass(
    histories: dict[int, HouseholdHistory],
    spec: SplitSpec,
    grid: np.ndarray,
    cfg: TaskConfig,
    args: argparse.Namespace,
    *,
    collect_pairs: bool,
) -> tuple[dict[str, float], pd.DataFrame | None]:
    """Day-level supply stats per split side, plus sampled anchor pairs for the fit sides."""
    trips_parts: list[np.ndarray] = []
    elig_parts: list[np.ndarray] = []
    window_parts: list[np.ndarray] = []
    gate_households = 0
    pair_frames: list[pd.DataFrame] = []
    for household in tqdm(sorted(spec.households), desc=spec.name, unit='hh'):
        hh = histories[household]
        supply = day_supply(hh, grid, cfg)
        trips_parts.append(supply.hist_trips)
        elig_parts.append(supply.n_eligible)
        window_parts.append(supply.window_trips)
        gated = (supply.hist_trips >= cfg.min_history_trips) & (supply.n_eligible >= args.gate)
        gate_households += int(gated.any())
        if collect_pairs:
            anchors = sample_anchors(
                supply,
                cfg,
                household=household,
                min_candidates=args.gate,
                max_anchors=args.anchors_per_household,
                seed=args.seed,
            )
            if len(anchors):
                pair_frames.append(extract_pairs(hh, anchors, cfg))
    trips = np.concatenate(trips_parts)
    elig = np.concatenate(elig_parts)
    window = np.concatenate(window_parts)
    qualified = trips >= cfg.min_history_trips
    gated = qualified & (elig >= args.gate)
    stats: dict[str, float] = {
        'households': float(len(trips_parts)),
        'qualified_days': float(qualified.sum()),
        'gate_days': float(gated.sum()),
        'gate_households': float(gate_households),
        'conditioning_drop': float((window[gated] == 0).mean()) if gated.any() else 0.0,
    }
    for threshold in SUPPLY_THRESHOLDS:
        stats[f'elig_ge_{threshold}'] = float((elig[qualified] >= threshold).mean())
    pairs = pd.concat(pair_frames, ignore_index=True) if pair_frames else None
    return stats, pairs


def _pair_stats(train: pd.DataFrame, dev: pd.DataFrame, *, seed: int, resamples: int) -> PairStats:
    """Fit the constant, weekly-rate and logistic baselines on train; score them on dev."""
    y_dev = dev['y'].to_numpy(dtype=float)
    constant = float(train['y'].mean())
    fit = irls_logistic(
        train[list(FEATURES)].to_numpy(dtype=float), train['y'].to_numpy(dtype=float)
    )
    se_const = (constant - y_dev) ** 2
    se_weekly = (dev['weekly_rate'].to_numpy(dtype=float) - y_dev) ** 2
    se_lr = (logistic_probs(fit, dev[list(FEATURES)].to_numpy(dtype=float)) - y_dev) ** 2
    which = _due_bins(dev)
    stratum = _stratum_of(dev)
    due_curves = tuple(
        (name, _curve(y_dev[stratum == name], which[stratum == name])) for name in STRATA
    )
    dev4 = dev[dev['n_prior'].to_numpy() >= 4]
    y4 = dev4['y'].to_numpy(dtype=float)
    which4 = _due_bins(dev4)
    window4 = which4 == 2
    after4 = which4 >= 3
    assert window4.any() and after4.any(), '>=4 stratum must populate the window and after bins'
    train4 = train[train['n_prior'].to_numpy() >= 4]
    fit4 = irls_logistic(
        train4[list(FEATURES)].to_numpy(dtype=float), train4['y'].to_numpy(dtype=float)
    )
    se_weekly4 = (dev4['weekly_rate'].to_numpy(dtype=float) - y4) ** 2
    se_lr4 = (logistic_probs(fit4, dev4[list(FEATURES)].to_numpy(dtype=float)) - y4) ** 2
    near_det = (dev['weekly_rate'] <= 0.1) | (dev['weekly_rate'] >= 0.9)
    per_anchor = dev.groupby(['household', 'anchor_day']).agg(
        n=('y', 'size'), positives=('y', 'sum')
    )
    return PairStats(
        n_train=len(train),
        n_dev=len(dev),
        n_dev4=len(dev4),
        positive_rate=float(y_dev.mean()),
        near_det_share=float(near_det.mean()),
        staple_share=float(dev['staple'].to_numpy().mean()),
        brier_constant=float(se_const.mean()),
        brier_weekly=float(se_weekly.mean()),
        brier_lr=float(se_lr.mean()),
        skill_weekly=_skill(dev, se_weekly, se_const, seed=seed, resamples=resamples),
        skill_lr=_skill(dev, se_lr, se_weekly, seed=seed, resamples=resamples),
        skill_lr_4=_skill(dev4, se_lr4, se_weekly4, seed=seed, resamples=resamples),
        p_window_4=float(y4[window4].mean()),
        p_after_4=float(y4[after4].mean()),
        due_curves=due_curves,
        zero_positive_instances=float((per_anchor['positives'] == 0).mean()),
        all_positive_instances=float((per_anchor['positives'] == per_anchor['n']).mean()),
        mean_candidates=float(per_anchor['n'].mean()),
        mean_positives=float(per_anchor['positives'].mean()),
    )


def _skill(
    dev: pd.DataFrame, se_model: np.ndarray, se_ref: np.ndarray, *, seed: int, resamples: int
) -> Skill:
    """Brier skill of the model over the reference, with an anchor-cluster bootstrap CI."""
    anchor = (
        pd.DataFrame(
            {
                'household': dev['household'].to_numpy(),
                'anchor_day': dev['anchor_day'].to_numpy(),
                'se_model': se_model,
                'se_ref': se_ref,
            }
        )
        .groupby(['household', 'anchor_day'])
        .sum()
    )
    m = anchor['se_model'].to_numpy()
    r = anchor['se_ref'].to_numpy()
    assert r.sum() > 0, 'reference Brier must be positive for a skill score'
    rng = np.random.default_rng(seed)
    n = len(m)
    samples = np.empty(resamples)
    for i in range(resamples):
        idx = rng.integers(0, n, n)
        samples[i] = 1.0 - m[idx].sum() / r[idx].sum()
    lo, hi = np.percentile(samples, [2.5, 97.5])
    return Skill(float(1.0 - m.sum() / r.sum()), float(lo), float(hi))


def _due_bins(pairs: pd.DataFrame) -> np.ndarray:
    """Bin index by where the mean-interval due date falls relative to the target window."""
    interval = np.maximum(pairs['mean_interval'].to_numpy(dtype=float), MIN_INTERVAL_DAYS)
    due_offset = interval - pairs['days_since_last'].to_numpy(dtype=float)
    return np.select(
        [due_offset < -interval, due_offset < 0.0, due_offset <= 6.0, due_offset <= 14.0],
        [0, 1, 2, 3],
        default=4,
    )


def _stratum_of(pairs: pd.DataFrame) -> np.ndarray:
    n_prior = pairs['n_prior'].to_numpy()
    return np.select([n_prior >= 5, n_prior >= 3], ['5+', '3-4'], default='2')


def _curve(y: np.ndarray, which: np.ndarray) -> tuple[tuple[str, float, int], ...]:
    return tuple(
        (
            DUE_BIN_NAMES[b],
            float(y[which == b].mean()) if (which == b).any() else 0.0,
            int((which == b).sum()),
        )
        for b in range(len(DUE_BIN_NAMES))
    )


def _gates(results: PairStats) -> list[tuple[str, bool]]:
    """Pre-registered pass rule, fixed before the recheck run: both must hold on >=4 purchases."""
    return [
        (
            'R1 P(buy | due in window) >= 1.5x P(buy | due after window)',
            results.p_window_4 >= 1.5 * results.p_after_4,
        ),
        (
            'R2 LR skill over weekly >= +0.03 with CI > 0',
            results.skill_lr_4.point >= 0.03 and results.skill_lr_4.lo > 0.0,
        ),
    ]


def _write_report(
    args: argparse.Namespace,
    cfg: TaskConfig,
    side_stats: dict[str, dict[str, float]],
    results: PairStats,
    gates: list[tuple[str, bool]],
) -> None:
    lines = [
        '# Replenishment feasibility report',
        '',
        f'granularity {cfg.granularity}, history {cfg.history_days}d,'
        f' horizon {cfg.horizon_days}d,'
        f' min purchases {cfg.min_purchases}, min history trips {cfg.min_history_trips},'
        f' gate {args.gate} candidates, {args.anchors_per_household} anchors/household,'
        f' seed {args.seed}',
        '',
        '## Day-level supply (F6, F7)',
        '',
        '| side | hhs | qual. days | >=10 | >=20 | >=25 | >=30 | gate days | gate hhs | cond. |',
        '|---|---|---|---|---|---|---|---|---|---|',
    ]
    for name, s in side_stats.items():
        lines.append(
            f'| {name} | {s["households"]:.0f} | {s["qualified_days"]:.0f} '
            f'| {s["elig_ge_10"]:.1%} | {s["elig_ge_20"]:.1%} | {s["elig_ge_25"]:.1%} '
            f'| {s["elig_ge_30"]:.1%} | {s["gate_days"]:.0f} | {s["gate_households"]:.0f} '
            f'| {s["conditioning_drop"]:.1%} |'
        )
    lines += [
        '',
        '## Pair-level on dev (F1, F2, F5, F8)',
        '',
        f'- pairs: {results.n_train} train / {results.n_dev} dev',
        f'- F1 positive rate: {results.positive_rate:.1%} (target 10-60%)',
        f'- F2 near-deterministic share: {results.near_det_share:.1%} (target < 50%);'
        f' staples {results.staple_share:.1%}',
        f'- F8 zero-positive instances: {results.zero_positive_instances:.1%},'
        f' all-positive: {results.all_positive_instances:.1%};'
        f' mean candidates {results.mean_candidates:.1f},'
        f' mean positives {results.mean_positives:.1f}',
        '',
        '## Due-vs-window curve by purchase-count stratum (F3 recheck)',
        '',
        '| stratum | bin | P(bought) | pairs |',
        '|---|---|---|---|',
    ]
    lines += [
        f'| {stratum} | {name} | {rate:.1%} | {n} |'
        for stratum, curve in results.due_curves
        for name, rate, n in curve
    ]
    lines += [
        '',
        '## Brier and skill on dev (F4, F5)',
        '',
        f'- pairs: {results.n_train} train / {results.n_dev} dev,'
        f' of which {results.n_dev4} dev pairs have >=4 purchases',
        f'- constant {results.brier_constant:.4f}, weekly rate {results.brier_weekly:.4f},'
        f' logistic regression {results.brier_lr:.4f}',
        f'- F5 weekly over constant: {results.skill_weekly.point:+.4f}'
        f' [{results.skill_weekly.lo:+.4f}, {results.skill_weekly.hi:+.4f}]',
        f'- F4 LR over weekly: {results.skill_lr.point:+.4f}'
        f' [{results.skill_lr.lo:+.4f}, {results.skill_lr.hi:+.4f}]',
        '',
        '## Pre-registered pass rule (>= 4 purchases)',
        '',
        f'- R1: P(buy | due in window) {results.p_window_4:.1%} vs'
        f' P(buy | due after window) {results.p_after_4:.1%}'
        f' -> ratio {results.p_window_4 / results.p_after_4:.2f} (need >= 1.50)',
        f'- R2: LR over weekly on the stratum {results.skill_lr_4.point:+.4f}'
        f' [{results.skill_lr_4.lo:+.4f}, {results.skill_lr_4.hi:+.4f}]'
        ' (need >= +0.03, CI > 0)',
        '',
        '## Gates',
        '',
    ]
    lines += [f'- {name}: {"PASS" if ok else "FAIL"}' for name, ok in gates]
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text('\n'.join(lines) + '\n')
    logger.info('feasibility report written to {}', args.report)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Run replenishment feasibility checks F1-F8')
    parser.add_argument(
        '--granularity', choices=['commodity', 'sub_commodity'], default='commodity'
    )
    parser.add_argument('--history-days', type=int, default=98)
    parser.add_argument('--min-purchases', type=int, default=2)
    parser.add_argument('--min-history-trips', type=int, default=6)
    parser.add_argument('--gate', type=int, default=30, help='min eligible candidates per anchor')
    parser.add_argument('--anchors-per-household', type=int, default=12)
    parser.add_argument('--resamples', type=int, default=10_000)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--data-dir', type=Path, default=None)
    parser.add_argument('--cleaning-config', type=Path, default=Path('configs/data.yaml'))
    parser.add_argument('--splits-config', type=Path, default=Path('configs/splits.yaml'))
    parser.add_argument(
        '--report',
        type=Path,
        default=Path('experiments/261023_replenish_feasibility/feasibility_report.md'),
    )
    return parser.parse_args()


if __name__ == '__main__':
    main()
