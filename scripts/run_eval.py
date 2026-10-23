import argparse
import json
import os
import subprocess
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import TextIO

import anyio
from anyio import Lock, Semaphore, create_task_group
from loguru import logger
from tqdm import tqdm

from cartgym.config import RewardConfig, load_config
from cartgym.env import _load_rows
from cartgym.generator import record_to_instance
from cartgym.instance import Instance
from cartgym.logging import setup_logging
from cartgym.openrouter import (
    ChatResult,
    OpenRouterClient,
    estimate_cost_usd,
    fetch_model_prices,
    load_api_key,
)
from cartgym.prompts import system_prompt
from cartgym.reward import GradeResult, ParsedAnswer, grade, parse_completion

# full-sweep target the dry run extrapolates towards (§9.2)
FULL_N, FULL_K = 100, 8


@dataclass(slots=True)
class RunState:
    """Shared counters for the running cost display; single event loop, no races."""

    spent_usd: float = 0.0
    rewards: list[float] = field(default_factory=list)
    exact: list[bool] = field(default_factory=list)
    failures: int = 0


@dataclass(slots=True)
class LevelRun:
    """Everything one rollout task needs; built once per model x level."""

    args: argparse.Namespace
    model: str
    level: str
    client: OpenRouterClient
    prices: dict[str, dict[str, str]]
    cfg: RewardConfig
    state: RunState
    instances: dict[str, Instance]
    bar: tqdm
    lock: Lock
    semaphore: Semaphore
    out: TextIO
    rewards: list[float] = field(default_factory=list)
    exact: list[bool] = field(default_factory=list)


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
            await run_level(args, model, level, client, prices, cfg, state)
    logger.info(
        'run complete: {} rollouts scored, {} api failures, total spend ${:.4f}',
        len(state.rewards),
        state.failures,
        state.spent_usd,
    )


async def run_level(
    args: argparse.Namespace,
    model: str,
    level: str,
    client: OpenRouterClient,
    prices: dict[str, dict[str, str]],
    cfg: RewardConfig,
    state: RunState,
) -> None:
    rows = _typed_rows(
        _load_rows(level, args.split, args.n, args.seed, args.instances_dir, cfg.model_dump_json())
    )
    params: dict[str, object] = {
        'temperature': args.temperature,
        'max_tokens': args.max_tokens,
        'reasoning_effort': args.reasoning_effort,
    }
    out_path = args.rollouts_dir / model.replace('/', '__') / f'{args.split}_{level}.jsonl'
    done = _resume_keys(out_path, params)
    if done:
        logger.info(
            '{} {}: resuming, {} rollouts already saved for {}', model, level, len(done), params
        )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    instances = {row.instance_id: record_to_instance(json.loads(row.record)) for row in rows}
    pending = [(row, k) for row in rows for k in range(args.k) if (row.instance_id, k) not in done]
    level_rewards: list[float] = []
    level_exact: list[bool] = []
    bar = tqdm(total=len(pending), desc=f'{model}/{level}', unit='roll')
    lock = Lock()
    semaphore = Semaphore(args.concurrency)
    out = out_path.open('a')
    run = LevelRun(
        args,
        model,
        level,
        client,
        prices,
        cfg,
        state,
        instances,
        bar,
        lock,
        semaphore,
        out,
        level_rewards,
        level_exact,
    )
    try:
        async with create_task_group() as tasks:
            for row, k in pending:
                tasks.start_soon(_rollout, run, row, k)
    finally:
        bar.close()
        out.close()
    if not run.rewards:
        run.rewards, run.exact = _existing_results(out_path, params)
    _summarize(model, level, run.rewards, run.exact, state)
    if args.dry_run and run.rewards:
        per_rollout = state.spent_usd / max(len(state.rewards), 1)
        logger.info(
            'dry run: this level at {}x{} ~${:.2f} per model at ${:.5f}/rollout',
            FULL_N,
            FULL_K,
            FULL_N * FULL_K * per_rollout,
            per_rollout,
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


async def _rollout(run: LevelRun, row: RolloutRow, k: int) -> None:
    async with run.semaphore:
        messages = [{'role': 'system', 'content': system_prompt()}, *row.prompt]
        try:
            result = await run.client.chat(
                run.model,
                messages,
                temperature=run.args.temperature,
                max_tokens=run.args.max_tokens,
                reasoning_effort=run.args.reasoning_effort,
            )
        except Exception as exc:
            # §9.2: API failures are logged and excluded, never scored as 0; leaving no
            # record means a resumed run re-fetches exactly these rollouts
            run.state.failures += 1
            run.bar.update(1)
            logger.error('{} {} #{} rollout {}: {}', run.model, run.level, row.instance_id, k, exc)
            return
        cost = _cost_of(result, run.prices, run.model)
        run.state.spent_usd += cost
        graded = grade(
            result.text, run.instances[row.instance_id], row.c_star_cents, row.c_ref_cents, run.cfg
        )
        parsed = parse_completion(result.text)
        record = _record(run, row, k, result, graded, parsed, cost, messages)
        async with run.lock:
            run.out.write(json.dumps(record) + '\n')
            run.out.flush()
        run.rewards.append(graded.reward)
        run.exact.append(graded.exact_opt)
        run.state.rewards.append(graded.reward)
        run.state.exact.append(graded.exact_opt)
        run.bar.update(1)
        run.bar.set_postfix(cost=f'${run.state.spent_usd:.4f}')


def _record(
    run: LevelRun,
    row: RolloutRow,
    k: int,
    result: ChatResult,
    graded: GradeResult,
    parsed: ParsedAnswer,
    cost: float,
    messages: list[dict[str, str]],
) -> dict[str, object]:
    return {
        'instance_id': row.instance_id,
        'level': run.level,
        'stratum': 'trap' if row.is_trap else 'no_trap',
        'model': run.model,
        'sampling_params': {
            'temperature': run.args.temperature,
            'max_tokens': run.args.max_tokens,
            'reasoning_effort': run.args.reasoning_effort,
        },
        'rollout_idx': k,
        'prompt': messages,
        'completion': result.text,
        'parsed': None if not parsed.parse_ok else parsed.cart,
        'parse_reason': parsed.reason,
        'reward': graded.reward,
        'components': {
            'parse_ok': graded.parse_ok,
            'feasible': graded.feasible,
            'frac_constraints': graded.frac_constraints,
            'opt': graded.opt,
            'exact_opt': graded.exact_opt,
            'price_ok': graded.price_ok,
            'violations': list(graded.violations),
            'cost_gap_cents': graded.cost_gap_cents,
            'c_star_cents': row.c_star_cents,
            'c_ref_cents': row.c_ref_cents,
        },
        'tokens': {
            'in': result.prompt_tokens,
            'out': result.completion_tokens,
            **{
                f'usage_{key}': value
                for key, value in result.usage.items()
                if key not in {'prompt_tokens', 'completion_tokens'}
            },
        },
        'cost_usd': cost,
        'latency_s': round(result.latency_s, 3),
        'seed': run.args.seed,
        'git_sha': _git_sha(),
        'timestamp': datetime.now(UTC).isoformat(timespec='seconds'),
    }


def _cost_of(result, prices: dict[str, dict[str, str]], model: str) -> float:
    reported = result.usage.get('cost')
    if isinstance(reported, int | float) and reported > 0:
        return float(reported)
    return estimate_cost_usd(prices, model, result.prompt_tokens, result.completion_tokens)


def _existing_results(out_path: Path, params: dict[str, object]) -> tuple[list[float], list[bool]]:
    """Rewards of already-saved rollouts under the same params (fully-resumed levels)."""
    rewards: list[float] = []
    exact: list[bool] = []
    if not out_path.is_file():
        return rewards, exact
    for line in out_path.read_text().splitlines():
        record = json.loads(line)
        if record.get('sampling_params') == params:
            rewards.append(float(record['reward']))
            exact.append(bool(record['components']['exact_opt']))
    return rewards, exact


def _resume_keys(out_path: Path, params: dict[str, object]) -> set[tuple[str, int]]:
    """Rollouts already saved under THIS run's sampling params; other configs are re-fetched."""
    if not out_path.is_file():
        return set()
    keys = set()
    lines = out_path.read_text().splitlines()
    valid = []
    for line in lines:
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            logger.warning('{}: dropping a truncated line (interrupted write?)', out_path)
            continue
        valid.append(line)
        if record.get('sampling_params') == params:
            keys.add((str(record['instance_id']), int(record['rollout_idx'])))
    if len(valid) != len(lines):
        out_path.write_text('\n'.join(valid) + '\n')
    return keys


def _summarize(model: str, level: str, rewards: list[float], exact: list[bool], state: RunState):
    if not rewards:
        logger.warning('{} {}: no rollouts scored', model, level)
        return
    n = len(rewards)
    logger.info(
        '{} {}: n={} mean_reward={:.3f} exact={:.0%} run_spend=${:.4f}',
        model,
        level,
        n,
        sum(rewards) / n,
        sum(exact) / n,
        state.spent_usd,
    )


def _git_sha() -> str:
    try:
        return subprocess.run(
            ['git', 'rev-parse', '--short', 'HEAD'], capture_output=True, text=True, check=True
        ).stdout.strip()
    except subprocess.CalledProcessError:
        return 'uncommitted'


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
    parser.add_argument('--reward-config', type=Path, default=Path('configs/reward.yaml'))
    parser.add_argument('--instances-dir', type=Path, default=Path('instances'))
    parser.add_argument('--rollouts-dir', type=Path, default=Path('rollouts'))
    args = parser.parse_args()
    args.models = [m.strip() for m in args.models.split(',')]
    args.levels = [level.strip() for level in args.levels.split(',')]
    if args.dry_run:
        args.n, args.k = min(args.n, 10), min(args.k, 2)
    return args


if __name__ == '__main__':
    main()
