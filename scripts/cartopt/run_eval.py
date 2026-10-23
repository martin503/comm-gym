import argparse
import json
import os
from dataclasses import dataclass
from pathlib import Path

import anyio
from loguru import logger

from commgym.cartopt.config import RewardConfig
from commgym.cartopt.env import load_rows
from commgym.cartopt.generator import record_to_instance
from commgym.cartopt.instance import Instance
from commgym.cartopt.prompts import system_prompt
from commgym.cartopt.reward import grade, parse_completion
from commgym.core.config import load_config
from commgym.core.logging import setup_logging
from commgym.core.openrouter import OpenRouterClient, fetch_model_prices, load_api_key
from commgym.core.runner import (
    EvalItem,
    GradeFn,
    GradeOutcome,
    LevelSummary,
    RunState,
    run_level,
)

# full-sweep target the dry run extrapolates towards (§9.2)
FULL_N, FULL_K = 100, 8


def main() -> None:
    args = _parse_args()
    setup_logging()
    anyio.run(amain, args)


async def amain(args: argparse.Namespace, client: OpenRouterClient | None = None) -> None:
    cfg = load_config(RewardConfig, args.reward_config)
    prices = fetch_model_prices()
    missing = [m for m in args.models if m not in prices]
    assert not missing, f'no pricing for {missing}; cost logging needs the models endpoint'
    if client is None:
        client = OpenRouterClient(load_api_key(os.environ, args.env_file))
    state = RunState()
    for model in args.models:
        for level in args.levels:
            await _run_level(args, model, level, client, prices, cfg, state)
    logger.info(
        'run complete: {} rollouts scored, {} api failures, total spend ${:.4f}',
        len(state.rewards),
        state.failures,
        state.spent_usd,
    )


async def _run_level(
    args: argparse.Namespace,
    model: str,
    level: str,
    client: OpenRouterClient,
    prices: dict[str, dict[str, str]],
    cfg: RewardConfig,
    state: RunState,
) -> None:
    rows = _typed_rows(
        load_rows(level, args.split, args.n, args.seed, args.instances_dir, cfg.model_dump_json())
    )
    items = [
        EvalItem(row.instance_id, row.prompt, 'trap' if row.is_trap else 'no_trap') for row in rows
    ]
    instances = {row.instance_id: record_to_instance(json.loads(row.record)) for row in rows}
    cents = {row.instance_id: (row.c_star_cents, row.c_ref_cents) for row in rows}
    out_path = args.rollouts_dir / model.replace('/', '__') / f'{args.split}_{level}.jsonl'
    summary = await run_level(
        items,
        _make_grader(instances, cents, cfg),
        client,
        model,
        level,
        out_path,
        prices,
        system_prompt(),
        'exact_opt',
        state,
        k=args.k,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        reasoning_effort=args.reasoning_effort,
        concurrency=args.concurrency,
        seed=args.seed,
    )
    _summarize(model, level, summary, state)
    if args.dry_run and summary.rewards:
        per_rollout = state.spent_usd / max(len(state.rewards), 1)
        logger.info(
            'dry run: this level at {}x{} ~${:.2f} per model at ${:.5f}/rollout',
            FULL_N,
            FULL_K,
            FULL_N * FULL_K * per_rollout,
            per_rollout,
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


def _summarize(model: str, level: str, summary: LevelSummary, state: RunState) -> None:
    if not summary.rewards:
        logger.warning('{} {}: no rollouts scored', model, level)
        return
    n = len(summary.rewards)
    logger.info(
        '{} {}: n={} mean_reward={:.3f} exact={:.0%} run_spend=${:.4f}',
        model,
        level,
        n,
        sum(summary.rewards) / n,
        sum(summary.successes) / n,
        state.spent_usd,
    )


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
    parser.add_argument('--models', required=True, help='comma-separated OpenRouter model ids')
    parser.add_argument('--split', default='dev', choices=['dev', 'eval_unseen', 'eval_known'])
    parser.add_argument('--levels', default='L1,L2', help='comma-separated level names')
    parser.add_argument('--n', type=int, default=10, help='instances per level')
    parser.add_argument('--k', type=int, default=2, help='rollouts per instance')
    parser.add_argument('--temperature', type=float, default=1.0)
    parser.add_argument('--max-tokens', type=int, default=2048)
    parser.add_argument(
        '--reasoning-effort',
        choices=['minimal', 'low', 'medium', 'high'],
        default=None,
        help='fixed reasoning effort for reasoning models (§9.1)',
    )
    parser.add_argument('--concurrency', type=int, default=4, help='max simultaneous API requests')
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='keep n<=10, k<=2 and print full-sweep extrapolation',
    )
    parser.add_argument('--env-file', type=Path, default=Path('.env'))
    parser.add_argument('--reward-config', type=Path, default=Path('configs/cartopt/reward.yaml'))
    parser.add_argument('--instances-dir', type=Path, default=Path('instances/cartopt'))
    parser.add_argument('--rollouts-dir', type=Path, default=Path('rollouts/cartopt'))
    args = parser.parse_args()
    args.models = [m.strip() for m in args.models.split(',')]
    args.levels = [level.strip() for level in args.levels.split(',')]
    if args.dry_run:
        args.n, args.k = min(args.n, 10), min(args.k, 2)
    return args


if __name__ == '__main__':
    main()
