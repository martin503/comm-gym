import argparse
import json
import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from loguru import logger

from cartgym.logging import setup_logging

PASS_KS = (1, 4, 8)
BOOTSTRAP_RESAMPLES = 10_000


@dataclass(frozen=True, slots=True)
class Rollout:
    """The slice of a rollout record the analysis reads."""

    instance_id: str
    rollout_idx: int
    stratum: str
    reward: float
    parse_ok: bool
    feasible: bool
    exact_opt: bool
    price_ok: bool
    opt: float
    violations: tuple[str, ...]
    cost_gap_cents: int | None
    parse_reason: str | None


def main() -> None:
    args = _parse_args()
    setup_logging()
    params: dict[str, object] = {
        'temperature': args.temperature,
        'max_tokens': args.max_tokens,
        'reasoning_effort': args.reasoning_effort,
    }
    sections = [f'# Eval report — {args.split}', '', f'Sampling params: `{params}`', '']
    for model in args.models:
        sections += [f'## {model}', '']
        sections += _model_sections(args, model, params)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text('\n'.join(sections) + '\n')
    logger.info('report written to {}', args.report)


def _model_sections(args: argparse.Namespace, model: str, params: dict[str, object]) -> list[str]:
    header = (
        '| level | stratum | inst | mean reward [95% CI] | pass@1 | pass@4 | pass@8 '
        '| feasible | price ok | zero-var | within sd |'
    )
    lines = [header, '|---|---|---|---|---|---|---|---|---|---|---|']
    taxonomy_rows: list[str] = []
    examples: list[str] = []
    model_dir = args.rollouts_dir / model.replace('/', '__')
    for level in args.levels:
        records = _load_records(model_dir / f'{args.split}_{level}.jsonl', params)
        if not records:
            logger.warning('{} {}: no rollouts for {}', model, level, params)
            continue
        for stratum in ('all', 'trap', 'no_trap'):
            subset = records if stratum == 'all' else [r for r in records if r.stratum == stratum]
            if not subset:
                continue
            stats = _instance_stats(subset)
            lines.append(
                f'| {level} | {stratum} | {stats.n_instances} '
                f'| {stats.reward_mean:.3f} [{stats.reward_lo:.3f}, {stats.reward_hi:.3f}] '
                f'| {_pct(stats.pass_at[1])} | {_pct(stats.pass_at[4])} '
                f'| {_pct(stats.pass_at[8])} '
                f'| {stats.feasible:.0%} | {stats.price_ok:.0%} '
                f'| {stats.zero_var:.0%} | {stats.within_sd:.3f} |'
            )
        taxonomy_rows.append(f'- **{level}**: {dict(_taxonomy(records))}')
        examples += _examples(level, records)
    return (
        lines
        + ['', '## Failure taxonomy', '']
        + taxonomy_rows
        + ['', '## Examples', '']
        + examples
    )


def _load_records(path: Path, params: dict[str, object]) -> list[Rollout]:
    if not path.is_file():
        return []
    rollouts: list[Rollout] = []
    for line in path.read_text().splitlines():
        record = json.loads(line)
        if record.get('sampling_params') != params:
            continue
        components = record['components']
        assert isinstance(components, dict), 'record components must be a mapping'
        violations = tuple(str(v) for v in components['violations'])
        gap = components['cost_gap_cents']
        rollouts.append(
            Rollout(
                instance_id=str(record['instance_id']),
                rollout_idx=int(record['rollout_idx']),
                stratum=str(record['stratum']),
                reward=float(record['reward']),
                parse_ok=bool(components['parse_ok']),
                feasible=bool(components['feasible']),
                exact_opt=bool(components['exact_opt']),
                price_ok=bool(components['price_ok']),
                opt=float(components['opt']),
                violations=violations,
                cost_gap_cents=int(gap) if gap is not None else None,
                parse_reason=(
                    str(record['parse_reason']) if record['parse_reason'] is not None else None
                ),
            )
        )
    return rollouts


@dataclass(frozen=True, slots=True)
class Stats:
    n_instances: int
    reward_mean: float
    reward_lo: float
    reward_hi: float
    pass_at: dict[int, float | None]
    feasible: float
    price_ok: float
    zero_var: float
    within_sd: float


def _instance_stats(records: list[Rollout]) -> Stats:
    by_instance: dict[str, list[Rollout]] = defaultdict(list)
    for record in records:
        by_instance[record.instance_id].append(record)
    groups = list(by_instance.values())
    instance_rewards = np.array([np.mean([r.reward for r in group]) for group in groups])
    rng = np.random.default_rng(42)
    n = len(instance_rewards)
    if n > 1:
        resampled = instance_rewards[rng.integers(0, n, size=(BOOTSTRAP_RESAMPLES, n))].mean(
            axis=1
        )
        lo, hi = np.percentile(resampled, [2.5, 97.5])
    else:
        lo = hi = float(instance_rewards.mean()) if n else 0.0
    within = [
        float(np.std([r.reward for r in group], ddof=1)) for group in groups if len(group) > 1
    ]
    return Stats(
        n_instances=n,
        reward_mean=float(instance_rewards.mean()) if n else 0.0,
        reward_lo=float(lo),
        reward_hi=float(hi),
        pass_at={k: _pass_at(groups, k) for k in PASS_KS},
        feasible=sum(1 for r in records if r.feasible) / len(records),
        price_ok=sum(1 for r in records if r.price_ok) / len(records),
        zero_var=(
            sum(1 for group in groups if len({r.reward for r in group}) == 1) / n if n else 0.0
        ),
        within_sd=float(np.mean(within)) if within else 0.0,
    )


def _pct(value: float | None) -> str:
    return '—' if value is None else f'{value:.0%}'


def _pass_at(groups: list[list[Rollout]], k: int) -> float | None:
    """Unbiased pass@k averaged over instances with at least k rollouts."""
    estimates = []
    for group in groups:
        if len(group) < k:
            continue
        correct = sum(1 for r in group if r.exact_opt)
        n = len(group)
        estimates.append(1.0 - math.comb(n - correct, k) / math.comb(n, k))
    return float(np.mean(estimates)) if estimates else None


def _taxonomy(records: list[Rollout]) -> Counter:
    counts: Counter = Counter()
    for record in records:
        if not record.parse_ok:
            counts[f'parse:{record.parse_reason}'] += 1
        elif not record.feasible:
            first = record.violations[0] if record.violations else '?'
            counts[f'infeasible:{first}'] += 1
        elif not record.exact_opt:
            counts['arithmetic' if not record.price_ok else 'suboptimal_feasible'] += 1
        elif not record.price_ok:
            counts['arithmetic'] += 1
        else:
            counts['optimal'] += 1
    return counts


def _examples(level: str, records: list[Rollout]) -> list[str]:
    """One success, one near-miss, and the top failure class of this level."""
    lines = [f'**{level}**']
    success = next((r for r in records if r.exact_opt), None)
    near_miss = next((r for r in records if r.feasible and 0.7 <= r.opt < 1), None)
    taxonomy = _taxonomy(records)
    failure_class = next((key for key in taxonomy if key != 'optimal'), None)
    failure = None
    if failure_class is not None:
        for record in records:
            counts = _taxonomy([record])
            if counts.most_common(1)[0][0] == failure_class:
                failure = record
                break
    for label, record in (
        (failure_class, failure),
        ('near-miss', near_miss),
        ('success', success),
    ):
        if record is None:
            continue
        lines.append(
            f'- {label}: instance `{record.instance_id}` rollout {record.rollout_idx} '
            f'(reward {record.reward:.3f}, gap {record.cost_gap_cents}c, '
            f'violations {list(record.violations)})'
        )
    return lines


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Analyze saved rollouts of one split')
    parser.add_argument('--models', required=True, help='comma-separated OpenRouter model ids')
    parser.add_argument('--split', default='eval_unseen')
    parser.add_argument('--levels', default='L1,L2,L3,L4')
    parser.add_argument('--temperature', type=float, default=1.0)
    parser.add_argument('--max-tokens', type=int, default=8192)
    parser.add_argument('--reasoning-effort', default='low')
    parser.add_argument('--rollouts-dir', type=Path, default=Path('rollouts'))
    parser.add_argument('--report', type=Path, default=Path('reports/eval_report.md'))
    args = parser.parse_args()
    args.models = [m.strip() for m in args.models.split(',')]
    args.levels = [level.strip() for level in args.levels.split(',')]
    return args


if __name__ == '__main__':
    main()
