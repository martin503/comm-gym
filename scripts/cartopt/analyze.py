import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

from loguru import logger

from commgym.core.cli import comma_list, write_report
from commgym.core.config import load_models
from commgym.core.eval import select_models
from commgym.core.logging import setup_logging
from commgym.core.rollouts import read_jsonl, rollouts_path
from commgym.core.stats import instance_stats


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
    models = select_models(load_models(args.config), args.models)
    sections = [f'# Eval report — {args.split}', '']
    for model, params in models.items():
        sections += [f'## {model}', '', f'Sampling params: `{params.sampling_params()}`', '']
        sections += _model_sections(args, model, params.sampling_params())
    write_report(args.report, sections)


def _model_sections(args: argparse.Namespace, model: str, params: dict[str, object]) -> list[str]:
    header = (
        '| level | stratum | inst | mean reward [95% CI] | pass@1 | pass@4 | pass@8 '
        '| feasible | price ok | zero-var | within sd |'
    )
    lines = [header, '|---|---|---|---|---|---|---|---|---|---|---|']
    taxonomy_rows: list[str] = []
    examples: list[str] = []
    for level in args.levels:
        path = rollouts_path(args.rollouts_dir, model, args.split, level)
        records = _load_records(path, params)
        if not records:
            logger.warning('{} {}: no rollouts for {}', model, level, params)
            continue
        for stratum in ('all', 'trap', 'no_trap'):
            subset = records if stratum == 'all' else [r for r in records if r.stratum == stratum]
            if not subset:
                continue
            stats = instance_stats(*_groups(subset))
            feasible = sum(1 for r in subset if r.feasible) / len(subset)
            price_ok = sum(1 for r in subset if r.price_ok) / len(subset)
            lines.append(
                f'| {level} | {stratum} | {stats.n_instances} '
                f'| {stats.reward_mean:.3f} [{stats.reward_lo:.3f}, {stats.reward_hi:.3f}] '
                f'| {_pct(stats.pass_at[1])} | {_pct(stats.pass_at[4])} '
                f'| {_pct(stats.pass_at[8])} '
                f'| {feasible:.0%} | {price_ok:.0%} '
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
    for record in read_jsonl(path):
        if record.get('sampling_params') != params:
            continue
        components = record['components']
        assert isinstance(components, dict), 'record components must be a mapping'
        rollout_idx = record['rollout_idx']
        reward = record['reward']
        assert isinstance(rollout_idx, int), 'rollout_idx must be an int'
        assert isinstance(reward, int | float), 'reward must be numeric'
        violations = tuple(str(v) for v in components['violations'])
        gap = components['cost_gap_cents']
        rollouts.append(
            Rollout(
                instance_id=str(record['instance_id']),
                rollout_idx=rollout_idx,
                stratum=str(record['stratum']),
                reward=float(reward),
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


def _groups(records: list[Rollout]) -> tuple[list[list[float]], list[list[bool]]]:
    by_instance: dict[str, list[Rollout]] = defaultdict(list)
    for record in records:
        by_instance[record.instance_id].append(record)
    groups = list(by_instance.values())
    return (
        [[r.reward for r in group] for group in groups],
        [[r.exact_opt for r in group] for group in groups],
    )


def _pct(value: float | None) -> str:
    return '—' if value is None else f'{value:.0%}'


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
    parser.add_argument(
        '--config', type=Path, default=Path('configs/cartopt/models.yaml'), help='models config'
    )
    parser.add_argument(
        '--models', type=comma_list, default=[], help='subset of configured models (default: all)'
    )
    parser.add_argument('--split', default='eval_unseen')
    parser.add_argument('--levels', type=comma_list, default=['L1', 'L2', 'L3', 'L4'])
    parser.add_argument('--rollouts-dir', type=Path, default=Path('rollouts/cartopt'))
    parser.add_argument('--report', type=Path, default=Path('reports/cartopt/eval_report.md'))
    return parser.parse_args()


if __name__ == '__main__':
    main()
