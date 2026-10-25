import argparse
import json
from pathlib import Path

from loguru import logger
from tqdm import tqdm

from commgym.core.config import load_config
from commgym.core.logging import setup_logging
from commgym.refund.baselines import (
    ConstantFits,
    always_approve_answers,
    always_reject_answers,
    fit_constants,
    oracle_answers,
    prompt_view_of,
    rule_parser_answers,
)
from commgym.refund.config import RewardConfig
from commgym.refund.instance import record_to_instance
from commgym.refund.reward import grade_parsed

BASELINES = ('always_reject', 'always_approve', 'rule_parser', 'oracle')


def main() -> None:
    args = _parse_args()
    setup_logging()
    cfg = load_config(RewardConfig, args.reward_config)
    train = [
        record_to_instance(_instance_payload(record))
        for record in _load(args.instances_dir, args.train_split, args.train_level)
    ]
    logger.info('fitting constants on {} {} instances', len(train), args.train_level)
    fits = fit_constants(train)
    logger.info(
        'fits: reject reason {}, approve reason {}, refund {}c',
        fits.reject_reason.value,
        fits.approve_reason.value,
        fits.refund_cents,
    )
    summaries: dict[tuple[str, str], dict[str, float]] = {}
    for level in args.levels:
        records = _load(args.instances_dir, args.split, level)
        for record in tqdm(records, desc=f'{args.split}/{level}', unit='inst'):
            instance = record_to_instance(_instance_payload(record))
            view = prompt_view_of(instance)
            answers = {
                'always_reject': always_reject_answers(len(instance.claims), fits.reject_reason),
                'always_approve': always_approve_answers(
                    len(instance.claims), fits.approve_reason, fits.refund_cents
                ),
                'rule_parser': rule_parser_answers(view),
                'oracle': oracle_answers(instance),
            }
            for name, parsed in answers.items():
                result = grade_parsed(parsed, instance, cfg)
                summary = summaries.setdefault(
                    (level, name), {'reward': 0.0, 'false_approve': 0.0, 'n': 0.0}
                )
                summary['reward'] += result.reward
                summary['false_approve'] += sum(
                    score.false_approve for score in result.claim_scores
                )
                summary['n'] += 1
    pooled = {name: _pooled(summaries, name, args.levels) for name in BASELINES}
    gates = [
        ('oracle is exactly 1.0', pooled['oracle'] == 1.0),
        ('rule_parser beats always_reject', pooled['rule_parser'] > pooled['always_reject']),
        ('rule_parser beats always_approve', pooled['rule_parser'] > pooled['always_approve']),
        (
            f'always_reject in [0.15, 0.20] (got {pooled["always_reject"]:.3f})',
            0.15 <= pooled['always_reject'] <= 0.20,
        ),
    ]
    _write_report(args, summaries, pooled, fits, gates)
    failed = False
    for name, ok in gates:
        (logger.success if ok else logger.error)('gate {}: {}', name, 'PASS' if ok else 'FAIL')
        failed |= not ok
    if failed:
        raise SystemExit(1)


def _load(instances_dir: Path, split: str, level: str) -> list[dict[str, object]]:
    path = instances_dir / f'{split}_{level}.jsonl'
    records = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    logger.info('{}: {} instances', path, len(records))
    return records


def _instance_payload(record: dict[str, object]) -> dict[str, object]:
    payload = record['instance']
    assert isinstance(payload, dict), 'record must carry an instance mapping'
    return payload


def _pooled(
    summaries: dict[tuple[str, str], dict[str, float]], name: str, levels: list[str]
) -> float:
    total = sum(summaries[(level, name)]['reward'] for level in levels)
    count = sum(summaries[(level, name)]['n'] for level in levels)
    return total / count


def _write_report(
    args: argparse.Namespace,
    summaries: dict[tuple[str, str], dict[str, float]],
    pooled: dict[str, float],
    fits: ConstantFits,
    gates: list[tuple[str, bool]],
) -> None:
    lines = [
        f'# Refund baselines — {args.split}',
        '',
        f'Fits from {args.train_split}/{args.train_level}: reject reason '
        f'{fits.reject_reason.value}, approve reason {fits.approve_reason.value}, '
        f'refund {fits.refund_cents}c.',
        '',
        '| level | baseline | mean reward | false approves |',
        '|---|---|---|---|',
    ]
    for (level, name), summary in sorted(summaries.items()):
        n = int(summary['n'])
        lines.append(
            f'| {level} | {name} | {summary["reward"] / n:.3f} | {int(summary["false_approve"])} |'
        )
    lines += ['', '| pooled (all levels) |', '', '| baseline | mean reward |', '|---|---|']
    lines += [f'| {name} | {reward:.3f} |' for name, reward in pooled.items()]
    lines += ['', '## Gates', ''] + [f'- {name}: {"PASS" if ok else "FAIL"}' for name, ok in gates]
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text('\n'.join(lines) + '\n')
    logger.info('baseline report written to {}', args.report)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Run refund baselines on saved instances')
    parser.add_argument(
        '--split', default='dev', choices=['train', 'dev', 'eval_unseen', 'eval_known']
    )
    parser.add_argument('--levels', default='L1,L2,L3', help='comma-separated level names')
    parser.add_argument('--train-split', default='train')
    parser.add_argument('--train-level', default='L3')
    parser.add_argument('--reward-config', type=Path, default=Path('configs/refund/reward.yaml'))
    parser.add_argument('--instances-dir', type=Path, default=Path('instances/refund_v4'))
    parser.add_argument('--report', type=Path, default=Path('reports/refund_baselines_v4.md'))
    args = parser.parse_args()
    args.levels = [level.strip() for level in args.levels.split(',')]
    return args


if __name__ == '__main__':
    main()
