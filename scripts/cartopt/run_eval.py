import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import anyio

from commgym.cartopt.config import RewardConfig
from commgym.cartopt.generator import record_to_instance
from commgym.cartopt.instance import Instance
from commgym.cartopt.prompts import system_prompt
from commgym.cartopt.reward import grade, parse_completion
from commgym.cartopt.rows import load_rows
from commgym.core.cli import comma_list
from commgym.core.config import load_config, load_models
from commgym.core.eval import LevelSpec, SweepPlan, run_sweep, select_models
from commgym.core.logging import setup_logging
from commgym.core.openrouter import OpenRouterClient
from commgym.core.runner import EvalItem, GradeFn, GradeOutcome

# full-sweep target the dry run extrapolates towards (§9.2)
SWEEP_PLAN = SweepPlan(full_n=100, full_k=8)


def main() -> None:
    args = _parse_args()
    setup_logging()
    anyio.run(amain, args)


async def amain(args: argparse.Namespace, client: OpenRouterClient | None = None) -> None:
    cfg = load_config(RewardConfig, args.reward_config)
    models = select_models(load_models(args.config), args.models)
    specs = {level: _level_spec(args, cfg, level) for level in args.levels}
    await run_sweep(
        models,
        args.levels,
        specs,
        env_file=args.env_file,
        plan=SWEEP_PLAN,
        split=args.split,
        rollouts_dir=args.rollouts_dir,
        k=args.k,
        concurrency=args.concurrency,
        seed=args.seed,
        success_label='exact',
        client=client,
        dry_run=args.dry_run,
    )


def _level_spec(args: argparse.Namespace, cfg: RewardConfig, level: str) -> LevelSpec:
    rows = _typed_rows(
        load_rows(level, args.split, args.n, args.seed, args.instances_dir, cfg.model_dump_json())
    )
    instances = {row.instance_id: record_to_instance(json.loads(row.record)) for row in rows}
    cents = {row.instance_id: (row.c_star_cents, row.c_ref_cents) for row in rows}
    items = [
        EvalItem(row.instance_id, row.prompt, 'trap' if row.is_trap else 'no_trap') for row in rows
    ]
    return LevelSpec(
        items=items,
        grade_fn=_make_grader(instances, cents, cfg),
        system_message=system_prompt(),
        success_key='exact_opt',
    )


def _make_grader(
    instances: dict[str, Instance], cents: dict[str, tuple[int, int]], cfg: RewardConfig
) -> GradeFn:
    def grade_fn(item: EvalItem, completion: str) -> GradeOutcome:
        c_star, c_ref = cents[item.instance_id]
        graded = grade(completion, instances[item.instance_id], c_star, c_ref, cfg)
        parsed = parse_completion(completion)
        return GradeOutcome(
            reward=graded.reward,
            parsed=None if not parsed.parse_ok else parsed.cart,
            parse_reason=parsed.reason,
            components={
                'parse_ok': graded.parse_ok,
                'feasible': graded.feasible,
                'frac_constraints': graded.frac_constraints,
                'opt': graded.opt,
                'exact_opt': graded.exact_opt,
                'price_ok': graded.price_ok,
                'violations': list(graded.violations),
                'cost_gap_cents': graded.cost_gap_cents,
                'c_star_cents': c_star,
                'c_ref_cents': c_ref,
            },
        )

    return grade_fn


@dataclass(frozen=True, slots=True)
class RolloutRow:
    """One eval instance narrowed to the typed fields the rollout path uses."""

    instance_id: str
    prompt: list[dict[str, str]]
    record: str
    c_star_cents: int
    c_ref_cents: int
    is_trap: bool


def _typed_rows(rows: list[dict[str, object]]) -> list[RolloutRow]:
    typed: list[RolloutRow] = []
    for row in rows:
        prompt = row['prompt']
        record = row['record']
        c_star = row['c_star_cents']
        c_ref = row['c_ref_cents']
        assert isinstance(prompt, list), 'row prompt must be a message list'
        assert isinstance(record, str), 'row record must be a JSON string'
        assert isinstance(c_star, int) and isinstance(c_ref, int), 'cent fields must be ints'
        messages: list[dict[str, str]] = []
        for message in prompt:
            assert isinstance(message, dict), 'prompt entries are message dicts'
            messages.append(message)
        typed.append(
            RolloutRow(
                instance_id=str(row['instance_id']),
                prompt=messages,
                record=record,
                c_star_cents=c_star,
                c_ref_cents=c_ref,
                is_trap=bool(row['is_trap']),
            )
        )
    return typed


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Zero-shot eval of models on cart-optimizer instances'
    )
    parser.add_argument(
        '--config', type=Path, default=Path('configs/cartopt/models.yaml'), help='models config'
    )
    parser.add_argument(
        '--models', type=comma_list, default=[], help='subset of configured models (default: all)'
    )
    parser.add_argument('--split', default='dev', choices=['dev', 'eval_unseen', 'eval_known'])
    parser.add_argument('--levels', type=comma_list, default=['L1', 'L2'])
    parser.add_argument('--n', type=int, default=10, help='instances per level')
    parser.add_argument('--k', type=int, default=2, help='rollouts per instance')
    parser.add_argument('--concurrency', type=int, default=4, help='max simultaneous API requests')
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='keep n<=10, k<=2 and print the full-sweep extrapolation',
    )
    parser.add_argument('--env-file', type=Path, default=Path('.env'))
    parser.add_argument('--reward-config', type=Path, default=Path('configs/cartopt/reward.yaml'))
    parser.add_argument('--instances-dir', type=Path, default=Path('instances/cartopt'))
    parser.add_argument('--rollouts-dir', type=Path, default=Path('rollouts/cartopt'))
    args = parser.parse_args()
    if args.dry_run:
        args.n, args.k = min(args.n, 10), min(args.k, 2)
    return args


if __name__ == '__main__':
    main()
