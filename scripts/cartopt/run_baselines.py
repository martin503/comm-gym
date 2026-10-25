import argparse
from pathlib import Path

import numpy as np
from loguru import logger
from tqdm import tqdm

from commgym.cartopt.baselines import SHORTCUT_BASELINES, baseline_carts
from commgym.cartopt.config import RewardConfig
from commgym.cartopt.generator import record_to_instance
from commgym.cartopt.pricing import cost
from commgym.cartopt.reward import grade_cart
from commgym.cartopt.solver import solve
from commgym.core.cli import comma_list, write_report
from commgym.core.config import load_config
from commgym.core.logging import setup_logging
from commgym.core.rollouts import read_jsonl

SUMMARY_FIELDS = ('reward', 'reward_trap', 'n_trap', 'feasible', 'exact', 'overpay', 'n')


def main() -> None:
    args = _parse_args()
    setup_logging()
    cfg = load_config(RewardConfig, args.reward_config)
    summaries: dict[tuple[str, str], dict[str, float]] = {}
    gates: list[tuple[str, str, bool]] = []
    for level in args.levels:
        path = args.instances_dir / f'{args.split}_{level}.jsonl'
        records = read_jsonl(path)
        logger.info('{}: {} instances from {}', level, len(records), path)
        rng = np.random.default_rng(args.seed)
        for record in tqdm(records, desc=level, unit='inst'):
            info = record['info']
            assert isinstance(info, dict), f'{path}: record info must be a mapping'
            instance = record_to_instance(record)
            solution = solve(instance)
            for name, cart in baseline_carts(instance, info, rng).items():
                total = cost(cart, instance).total_cents / 100
                result = grade_cart(
                    cart,
                    total,
                    instance,
                    solution.c_star_cents(),
                    solution.c_ref_cents(),
                    cfg,
                )
                summary = summaries.setdefault((level, name), dict.fromkeys(SUMMARY_FIELDS, 0.0))
                summary['reward'] += result.reward
                if bool(info['is_trap']):
                    summary['reward_trap'] += result.reward
                    summary['n_trap'] += 1
                summary['feasible'] += result.feasible
                summary['exact'] += result.exact_opt
                summary['overpay'] += max(result.cost_gap_cents or 0, 0)
                summary['n'] += 1
        for name in SHORTCUT_BASELINES:
            shortcut = summaries[(level, name)]['reward']
            aware = summaries[(level, 'constraint_aware_greedy')]['reward']
            gates.append((level, name, shortcut < aware))
    _write_report(args, summaries, gates)
    for level, name, ok in gates:
        (logger.success if ok else logger.error)(
            'gate {} / {}: {}', level, name, 'PASS' if ok else 'FAIL'
        )


def _write_report(
    args: argparse.Namespace,
    summaries: dict[tuple[str, str], dict[str, float]],
    gates: list[tuple[str, str, bool]],
) -> None:
    header = (
        '| level | baseline | mean reward | reward (traps) | feasible | exact-opt | mean overpay |'
    )
    lines = [
        f'# Baselines — {args.split}',
        '',
        header,
        '|---|---|---|---|---|---|---|',
    ]
    for (level, name), summary in sorted(summaries.items()):
        n = int(summary['n'])
        trap_mean = summary['reward_trap'] / summary['n_trap'] if summary['n_trap'] else 0.0
        lines.append(
            f'| {level} | {name} | {summary["reward"] / n:.3f} '
            f'| {trap_mean:.3f} '
            f'| {summary["feasible"] / n:.0%} | {summary["exact"] / n:.0%} '
            f'| {summary["overpay"] / n / 100:.2f} |'
        )
    lines += ['', '## Shortcut gate (each must sit below constraint-aware greedy)', '']
    lines += [f'- {level} / {name}: {"PASS" if ok else "FAIL"}' for level, name, ok in gates]
    write_report(args.report, lines)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Run all baselines on saved instances')
    parser.add_argument(
        '--split', default='dev', choices=['train', 'dev', 'eval_unseen', 'eval_known']
    )
    parser.add_argument('--levels', type=comma_list, default=['L1', 'L2'])
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--reward-config', type=Path, default=Path('configs/cartopt/reward.yaml'))
    parser.add_argument('--instances-dir', type=Path, default=Path('instances/cartopt'))
    parser.add_argument('--report', type=Path, default=Path('reports/cartopt/baselines.md'))
    return parser.parse_args()


if __name__ == '__main__':
    main()
