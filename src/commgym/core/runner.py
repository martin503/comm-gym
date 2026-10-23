import json
import subprocess
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import TextIO

from anyio import Lock, Semaphore, create_task_group
from loguru import logger
from tqdm import tqdm

from commgym.core.openrouter import ChatResult, OpenRouterClient, estimate_cost_usd

RECORD_KEYS = (
    'instance_id',
    'level',
    'stratum',
    'model',
    'sampling_params',
    'rollout_idx',
    'prompt',
    'completion',
    'parsed',
    'parse_reason',
    'reward',
    'components',
    'tokens',
    'cost_usd',
    'latency_s',
    'seed',
    'git_sha',
    'timestamp',
)


@dataclass(frozen=True, slots=True)
class EvalItem:
    """One eval instance as the runner sees it: prompt, id, and stratum tag."""

    instance_id: str
    prompt: list[dict[str, str]]
    stratum: str


@dataclass(frozen=True, slots=True)
class GradeOutcome:
    """Grader verdict for one completion; fields land verbatim in the rollout record."""

    reward: float
    parsed: object | None
    parse_reason: str | None
    components: dict[str, object]


type GradeFn = Callable[[EvalItem, str], GradeOutcome]


@dataclass(slots=True)
class RunState:
    """Shared counters for the running cost display; single event loop, no races."""

    spent_usd: float = 0.0
    rewards: list[float] = field(default_factory=list)
    successes: list[bool] = field(default_factory=list)
    failures: int = 0


@dataclass(frozen=True, slots=True)
class LevelSummary:
    """One level's rollouts: newly scored plus already-saved (fully-resumed) ones."""

    rewards: list[float]
    successes: list[bool]


async def run_level(
    items: Sequence[EvalItem],
    grade_fn: GradeFn,
    client: OpenRouterClient,
    model: str,
    level: str,
    out_path: Path,
    prices: dict[str, dict[str, str]],
    system_message: str,
    success_key: str,
    state: RunState,
    *,
    k: int,
    temperature: float = 1.0,
    max_tokens: int = 2048,
    reasoning_effort: str | None = None,
    concurrency: int = 4,
    seed: int = 42,
) -> LevelSummary:
    """Score k rollouts per item against the model, appending JSONL records to out_path."""
    params = _sampling_params(temperature, max_tokens, reasoning_effort)
    done = resume_keys(out_path, params)
    if done:
        logger.info(
            '{} {}: resuming, {} rollouts already saved for {}', model, level, len(done), params
        )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pending = [
        (item, kth) for item in items for kth in range(k) if (item.instance_id, kth) not in done
    ]
    bar = tqdm(total=len(pending), desc=f'{model}/{level}', unit='roll')
    run = _LevelRun(
        grade_fn=grade_fn,
        client=client,
        model=model,
        level=level,
        prices=prices,
        system_message=system_message,
        success_key=success_key,
        state=state,
        temperature=temperature,
        max_tokens=max_tokens,
        reasoning_effort=reasoning_effort,
        seed=seed,
        bar=bar,
        lock=Lock(),
        semaphore=Semaphore(concurrency),
        out=out_path.open('a'),
        rewards=[],
        successes=[],
    )
    try:
        async with create_task_group() as tasks:
            for item, kth in pending:
                tasks.start_soon(_rollout, run, item, kth)
    finally:
        bar.close()
        run.out.close()
    if not run.rewards:
        run.rewards, run.successes = existing_results(out_path, params, success_key)
    return LevelSummary(rewards=run.rewards, successes=run.successes)


def _sampling_params(
    temperature: float, max_tokens: int, reasoning_effort: str | None
) -> dict[str, object]:
    return {
        'temperature': temperature,
        'max_tokens': max_tokens,
        'reasoning_effort': reasoning_effort,
    }


@dataclass(slots=True)
class _LevelRun:
    """Everything one rollout task needs; built once per model x level."""

    grade_fn: GradeFn
    client: OpenRouterClient
    model: str
    level: str
    prices: dict[str, dict[str, str]]
    system_message: str
    success_key: str
    state: RunState
    temperature: float
    max_tokens: int
    reasoning_effort: str | None
    seed: int
    bar: tqdm
    lock: Lock
    semaphore: Semaphore
    out: TextIO
    rewards: list[float]
    successes: list[bool]


async def _rollout(run: _LevelRun, item: EvalItem, k: int) -> None:
    async with run.semaphore:
        messages = [{'role': 'system', 'content': run.system_message}, *item.prompt]
        try:
            result = await run.client.chat(
                run.model,
                messages,
                temperature=run.temperature,
                max_tokens=run.max_tokens,
                reasoning_effort=run.reasoning_effort,
            )
        except Exception as exc:
            # §9.2: API failures are logged and excluded, never scored as 0; leaving no
            # record means a resumed run re-fetches exactly these rollouts
            run.state.failures += 1
            run.bar.update(1)
            logger.error(
                '{} {} #{} rollout {}: {}', run.model, run.level, item.instance_id, k, exc
            )
            return
        cost = _cost_of(result, run.prices, run.model)
        run.state.spent_usd += cost
        outcome = run.grade_fn(item, result.text)
        record = _record(run, item, k, result, outcome, cost, messages)
        async with run.lock:
            run.out.write(json.dumps(record) + '\n')
            run.out.flush()
        run.rewards.append(outcome.reward)
        run.successes.append(bool(outcome.components[run.success_key]))
        run.state.rewards.append(outcome.reward)
        run.state.successes.append(bool(outcome.components[run.success_key]))
        run.bar.update(1)
        run.bar.set_postfix(cost=f'${run.state.spent_usd:.4f}')


def _record(
    run: _LevelRun,
    item: EvalItem,
    k: int,
    result: ChatResult,
    outcome: GradeOutcome,
    cost: float,
    messages: list[dict[str, str]],
) -> dict[str, object]:
    return {
        'instance_id': item.instance_id,
        'level': run.level,
        'stratum': item.stratum,
        'model': run.model,
        'sampling_params': _sampling_params(run.temperature, run.max_tokens, run.reasoning_effort),
        'rollout_idx': k,
        'prompt': messages,
        'completion': result.text,
        'parsed': outcome.parsed,
        'parse_reason': outcome.parse_reason,
        'reward': outcome.reward,
        'components': outcome.components,
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
        'seed': run.seed,
        'git_sha': git_sha(),
        'timestamp': datetime.now(UTC).isoformat(timespec='seconds'),
    }


def _cost_of(result: ChatResult, prices: dict[str, dict[str, str]], model: str) -> float:
    reported = result.usage.get('cost')
    if isinstance(reported, int | float) and reported > 0:
        return float(reported)
    return estimate_cost_usd(prices, model, result.prompt_tokens, result.completion_tokens)


def existing_results(
    out_path: Path, params: dict[str, object], success_key: str
) -> tuple[list[float], list[bool]]:
    """Rewards of already-saved rollouts under the same params (fully-resumed levels)."""
    rewards: list[float] = []
    successes: list[bool] = []
    if not out_path.is_file():
        return rewards, successes
    for line in out_path.read_text().splitlines():
        record = json.loads(line)
        if record.get('sampling_params') == params:
            rewards.append(float(record['reward']))
            successes.append(bool(record['components'][success_key]))
    return rewards, successes


def resume_keys(out_path: Path, params: dict[str, object]) -> set[tuple[str, int]]:
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


def git_sha() -> str:
    try:
        return subprocess.run(
            ['git', 'rev-parse', '--short', 'HEAD'], capture_output=True, text=True, check=True
        ).stdout.strip()
    except subprocess.CalledProcessError:
        return 'uncommitted'
