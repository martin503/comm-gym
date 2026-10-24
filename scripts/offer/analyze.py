import argparse
import json
from collections import Counter
from pathlib import Path

from loguru import logger

from commgym.core.config import load_config
from commgym.core.logging import setup_logging
from commgym.core.stats import bootstrap_mean_ci
from commgym.offer.config import RewardConfig
from commgym.offer.reward import final_reward

JUDGE_TAG = 'judged'
MIN_JUDGED_COVERAGE = 0.95
Key = tuple[str, int]


def main() -> None:
    args = _parse_args()
    setup_logging()
    reward_cfg = load_config(RewardConfig, args.reward_config)
    models = args.models or sorted(
        {path.parent.name for path in args.rollouts_dir.glob(f'*/{args.split}_*.jsonl')}
    )
    assert models, f'no rollout files under {args.rollouts_dir} for split {args.split}'
    lines = [
        '# Offer Eval Report',
        '',
        f'- split: {args.split}; judged term weight {reward_cfg.w_judge}',
        '',
        '| model | level | rollouts | gate pass | judge-free mean [CI] | judged | '
        'judge win [CI] | final [CI] | words |',
        '|---|---|---|---|---|---|---|---|---|',
    ]
    failures: dict[tuple[str, str], Counter[str]] = {}
    examples: list[str] = []
    judged_errors = 0
    for model in models:
        for level in args.levels:
            rollouts = _read_jsonl(args.rollouts_dir / model / f'{args.split}_{level}.jsonl')
            sidecar = args.rollouts_dir / model / f'{args.split}_{level}.{JUDGE_TAG}.jsonl'
            judged = _judged_by_key(sidecar) if sidecar.is_file() else {}
            judged_errors = sum(1 for row in judged.values() if row.get('error'))
            gate_passers = [r for r in rollouts if _component(r, 'gate_pass') is True]
            covered = sum(1 for r in gate_passers if _key(r) in judged)
            judged_share = covered / len(gate_passers) if gate_passers else 1.0
            prefix = [_reward(r) for r in rollouts]
            wins = [
                _judged_win(judged[_key(r)])
                for r in gate_passers
                if _key(r) in judged and not judged[_key(r)].get('error')
            ]
            finals = [
                final_reward(_reward(r), _judged_win(judged[_key(r)]), reward_cfg)
                for r in gate_passers
                if _key(r) in judged and not judged[_key(r)].get('error')
            ]
            failures[(model, level)] = _failure_taxonomy(rollouts)
            p_mean, p_lo, p_hi = bootstrap_mean_ci(prefix)
            w_mean, w_lo, w_hi = bootstrap_mean_ci(wins)
            f_mean, f_lo, f_hi = bootstrap_mean_ci(finals)
            words = _mean([_word_count(r) for r in rollouts])
            gate_rate = len(gate_passers) / len(rollouts) if rollouts else 0.0
            if gate_passers and judged_share < MIN_JUDGED_COVERAGE:
                lines.append(
                    f'> {model} {level}: only {judged_share:.0%} of gate-passers judged '
                    f'(threshold {MIN_JUDGED_COVERAGE:.0%}); judge columns are partial'
                )
            lines.append(
                f'| {model} | {level} | {len(rollouts)} | {gate_rate:.0%} '
                f'| {p_mean:.2f} [{p_lo:.2f}, {p_hi:.2f}] '
                f'| {judged_share:.0%} '
                f'| {w_mean:.2f} [{w_lo:.2f}, {w_hi:.2f}] '
                f'| {f_mean:.2f} [{f_lo:.2f}, {f_hi:.2f}] '
                f'| {words:.0f} |'
            )
            examples += _examples(model, level, rollouts, judged, reward_cfg)
    lines += ['', '## Gate failure taxonomy', '']
    for (model, level), counter in failures.items():
        top = ', '.join(f'{name} ×{count}' for name, count in counter.most_common(5))
        lines.append(f'- {model} {level}: {top or "none"}')
    if judged_errors:
        lines += ['', f'- judge errors excluded (not zeroed): {judged_errors}']
    lines += ['', '## Examples', ''] + examples
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text('\n'.join(lines) + '\n')
    logger.info('eval report written to {}', args.report)


def _examples(
    model: str,
    level: str,
    rollouts: list[dict[str, object]],
    judged: dict[Key, dict[str, object]],
    reward_cfg: RewardConfig,
) -> list[str]:
    lines = []
    scored = [
        (final_reward(_reward(r), _judged_win(judged[_key(r)]), reward_cfg), r)
        for r in rollouts
        if _key(r) in judged and not judged[_key(r)].get('error')
    ]
    if scored:
        best_score, best = max(scored, key=lambda pair: pair[0])
        lines.append(f'**{model} {level} best (final {best_score:.2f})**')
        lines.append(f'> {_str(_component(best, "message", ""))}')
        lines.append(f'— selected {_component(best, "selected", [])}')
    failed = [r for r in rollouts if _component(r, 'gate_pass') is not True]
    if failed:
        worst = failed[0]
        lines.append(f'**{model} {level} gate failure**')
        lines.append(f'> {_str(_component(worst, "message", ""))}')
        lines.append(f'— failures: {_component(worst, "gate_failures", [])}')
    return lines + ['']


def _failure_taxonomy(rollouts: list[dict[str, object]]) -> Counter[str]:
    counter: Counter[str] = Counter()
    for record in rollouts:
        if _component(record, 'gate_pass') is True:
            continue
        reason = record.get('parse_reason')
        if isinstance(reason, str):
            counter[f'parse:{reason}'] += 1
            continue
        gate_failures = _component(record, 'gate_failures', [])
        assert isinstance(gate_failures, list), 'gate_failures must be a list'
        counter[f'gate:{gate_failures[0] if gate_failures else "unknown"}'] += 1
    return counter


def _judged_by_key(path: Path) -> dict[Key, dict[str, object]]:
    judged: dict[Key, dict[str, object]] = {}
    for row in _read_jsonl(path):
        judged[_key(row)] = row
    return judged


def _key(record: dict[str, object]) -> Key:
    value = record['rollout_idx']
    assert isinstance(value, int), 'rollout_idx must be an int'
    return (str(record['instance_id']), value)


def _component(record: dict[str, object], name: str, default: object = None) -> object:
    components = record.get('components', {})
    assert isinstance(components, dict), 'components must be a dict'
    return components.get(name, default)


def _reward(record: dict[str, object]) -> float:
    value = record['reward']
    assert isinstance(value, int | float), 'reward must be numeric'
    return float(value)


def _judged_win(row: dict[str, object]) -> float:
    value = row['judge_win']
    assert isinstance(value, int | float), 'judge_win must be numeric'
    return float(value)


def _word_count(record: dict[str, object]) -> float:
    value = _component(record, 'word_count', 0)
    assert isinstance(value, int), 'word_count must be an int'
    return float(value)


def _str(value: object) -> str:
    return value if isinstance(value, str) else ''


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _read_jsonl(path: Path) -> list[dict[str, object]]:
    rows = []
    for line in path.read_text().splitlines():
        if line.strip():
            row = json.loads(line)
            assert isinstance(row, dict), f'{path}: rows must be JSON objects'
            rows.append(row)
    return rows


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Aggregate offer rollouts with judge sidecars')
    parser.add_argument('--split', default='eval_unseen')
    parser.add_argument('--levels', default='L1,L2,L3')
    parser.add_argument(
        '--models', default='', help='comma-separated rollout dir names; default all'
    )
    parser.add_argument('--reward-config', type=Path, default=Path('configs/offer/reward.yaml'))
    parser.add_argument('--rollouts-dir', type=Path, default=Path('rollouts/offer'))
    parser.add_argument('--report', type=Path, default=Path('reports/offer_eval_report.md'))
    args = parser.parse_args()
    args.levels = [level.strip() for level in args.levels.split(',')]
    args.models = [m.strip() for m in args.models.split(',') if m.strip()]
    return args


if __name__ == '__main__':
    main()
