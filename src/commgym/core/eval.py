import os
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from loguru import logger

from commgym.core.config import ModelParams
from commgym.core.openrouter import (
    OpenRouterClient,
    Prices,
    fetch_model_prices,
    load_api_key,
)
from commgym.core.rollouts import rollouts_path
from commgym.core.runner import EvalItem, GradeFn, LevelSummary, RunState, run_level


@dataclass(frozen=True, slots=True)
class LevelSpec:
    """Task inputs for one level: everything the shared sweep needs to score it."""

    items: Sequence[EvalItem]
    grade_fn: GradeFn
    system_message: str
    success_key: str


@dataclass(frozen=True, slots=True)
class SweepPlan:
    """Full-sweep target a dry run extrapolates towards, plus an optional budget gate."""

    full_n: int
    full_k: int
    budget_usd: float | None = None


async def run_sweep(
    models: dict[str, ModelParams],
    levels: Sequence[str],
    specs: Mapping[str, LevelSpec],
    *,
    env_file: Path,
    plan: SweepPlan,
    split: str,
    rollouts_dir: Path,
    k: int,
    concurrency: int = 4,
    seed: int = 42,
    success_label: str = 'success',
    client: OpenRouterClient | None = None,
    prices: Prices | None = None,
    dry_run: bool = False,
) -> RunState:
    """Score every configured model x level, each model with its own sampling params."""
    if prices is None:
        prices = fetch_model_prices()
    unpriced = [model for model in models if model not in prices]
    assert not unpriced, f'no pricing for {unpriced}; cost logging needs the models endpoint'
    missing_specs = [level for level in levels if level not in specs]
    assert not missing_specs, f'no level spec for {missing_specs}'
    if client is None:
        client = OpenRouterClient(load_api_key(os.environ, env_file))
    state = RunState()
    for model, params in models.items():
        for level in levels:
            spec = specs[level]
            summary = await run_level(
                spec.items,
                spec.grade_fn,
                client,
                model,
                level,
                rollouts_path(rollouts_dir, model, split, level),
                prices,
                spec.system_message,
                spec.success_key,
                state,
                k=k,
                temperature=params.temperature,
                max_tokens=params.max_tokens,
                reasoning_effort=params.reasoning_effort,
                concurrency=concurrency,
                seed=seed,
            )
            _summarize(model, level, summary, state, success_label)
    logger.info(
        'run complete: {} rollouts scored, {} api failures, total spend ${:.4f}',
        len(state.rewards),
        state.failures,
        state.spent_usd,
    )
    if dry_run and state.rewards:
        _project(state, len(models), len(levels), plan)
    return state


def select_models(models: dict[str, ModelParams], names: Sequence[str]) -> dict[str, ModelParams]:
    """Configured models restricted to names; empty names keeps the full config."""
    missing = [name for name in names if name not in models]
    assert not missing, f'{missing} are not in the models config'
    return {name: models[name] for name in names} if names else dict(models)


def _summarize(
    model: str, level: str, summary: LevelSummary, state: RunState, success_label: str
) -> None:
    if not summary.rewards:
        logger.warning('{} {}: no rollouts scored', model, level)
        return
    n = len(summary.rewards)
    logger.info(
        '{} {}: n={} mean_reward={:.3f} {}={:.0%} run_spend=${:.4f}',
        model,
        level,
        n,
        sum(summary.rewards) / n,
        success_label,
        sum(summary.successes) / n,
        state.spent_usd,
    )


def _project(state: RunState, n_models: int, n_levels: int, plan: SweepPlan) -> None:
    per_rollout = state.spent_usd / len(state.rewards)
    projected = per_rollout * n_models * n_levels * plan.full_n * plan.full_k
    if plan.budget_usd is None or projected <= plan.budget_usd:
        logger.success(
            'dry run: full sweep {} models x {} levels x {}x{} projects to ${:.2f} '
            '(${:.5f} per rollout)',
            n_models,
            n_levels,
            plan.full_n,
            plan.full_k,
            projected,
            per_rollout,
        )
    else:
        assert plan.budget_usd is not None, 'budget branch is reachable only with a budget gate'
        logger.error(
            'dry run: full sweep {} models x {} levels x {}x{} projects to ${:.2f}, '
            'over the ${:.2f} budget gate',
            n_models,
            n_levels,
            plan.full_n,
            plan.full_k,
            projected,
            plan.budget_usd,
        )
