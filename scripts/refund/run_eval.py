import argparse
import json
import os
from dataclasses import dataclass
from pathlib import Path

import anyio
import numpy as np
from loguru import logger

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
from commgym.refund.config import RewardConfig
from commgym.refund.instance import RefundInstance, record_to_instance
from commgym.refund.prompts import system_prompt, user_prompt
from commgym.refund.reward import grade, parse_completion

# full-sweep target the dry run extrapolates towards: 100 anchors x k rollouts x 3 levels
FULL_N, FULL_K = 100, 8
BUDGET_USD = 5.0


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
    if args.dry_run and state.rewards:
        per_rollout = state.spent_usd / len(state.rewards)
        projected = per_rollout * FULL_N * FULL_K * len(args.levels)
        if projected <= BUDGET_USD:
            logger.success(
                'dry run: full sweep {}x{}x{} projects to ${:.2f}, within the ${:.2f} budget'
                ' ({} per rollout)',
                FULL_N,
                FULL_K,
                len(args.levels),
                projected,
                BUDGET_USD,
                f'${per_rollout:.5f}',
            )
        else:
            logger.error(
                'dry run: full sweep {}x{}x{} projects to ${:.2f}, over the ${:.2f} budget;'
                ' pre-agreed fallback: live sweep with --k 4 projects ${:.2f}',
                FULL_N,
                FULL_K,
                len(args.levels),
                projected,
                BUDGET_USD,
                projected / 2,
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
    rows = _load_rows(args.instances_dir, args.split, level, args.n, args.seed)
    system = system_prompt()
    items = [
        EvalItem(
            row.instance_id,
            [{'role': 'user', 'content': user_prompt(row.instance)}],
            'out_of_window' if row.is_out_of_window else 'in_window',
        )
        for row in rows
    ]
    instances = {row.instance_id: row.instance for row in rows}
    out_path = args.rollouts_dir / model.replace('/', '__') / f'{args.split}_{level}.jsonl'
    summary = await run_level(
        items,
        _make_grader(instances, cfg),
        client,
        model,
        level,
        out_path,
        prices,
        system,
        'parse_ok',
        state,
        k=args.k,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        reasoning_effort=args.reasoning_effort,
        concurrency=args.concurrency,
        seed=args.seed,
    )
    _summarize(model, level, summary, state)


def _make_grader(instances: dict[str, RefundInstance], cfg: RewardConfig) -> GradeFn:
    def grade_fn(item: EvalItem, completion: str) -> GradeOutcome:
        instance = instances[item.instance_id]
        result = grade(completion, instance, cfg)
        parsed = parse_completion(
            completion,
            len(instance.claims),
            frozenset(line.code for line in instance.lines),
        )
        claims = [
            {
                'stated': claim.stated_type.value,
                'truth_reason': claim.truth_reason.value,
                'truth_line': claim.truth_line,
                'truth_refund_cents': claim.truth_refund_cents,
                'kind': claim.reference_kind,
                'stated_number': claim.stated_number,
                'decision_ok': score.decision_ok,
                'line_ok': score.line_ok,
                'reason_ok': score.reason_ok,
                'refund_ok': score.refund_ok,
                'false_approve': score.false_approve,
                'false_reject': score.false_reject,
                'dollar_error_cents': score.dollar_error_cents,
                'predicted_reason': answer.reason.value if parsed.parse_ok else None,
                'predicted_refund_cents': answer.refund_cents if parsed.parse_ok else None,
            }
            for claim, score, answer in zip(
                instance.claims, result.claim_scores, parsed.claims or (), strict=False
            )
        ]
        return GradeOutcome(
            reward=result.reward,
            parsed=None
            if not parsed.parse_ok or parsed.claims is None
            else [
                {
                    'line': answer.line,
                    'decision': answer.decision.value,
                    'reason': answer.reason.value,
                    'refund_cents': answer.refund_cents,
                }
                for answer in parsed.claims
            ],
            parse_reason=parsed.reason,
            components={
                'parse_ok': result.parse_ok,
                'reward': result.reward,
                'n_claims': len(instance.claims),
                'scored_claims': len(result.claim_scores),
                'false_approves': sum(s.false_approve for s in result.claim_scores),
                'false_rejects': sum(s.false_reject for s in result.claim_scores),
                'mean_dollar_error_cents': (
                    sum(s.dollar_error_cents for s in result.claim_scores)
                    / len(result.claim_scores)
                    if result.claim_scores
                    else 0
                ),
                'claims': claims,
            },
        )

    return grade_fn


def _summarize(model: str, level: str, summary: LevelSummary, state: RunState) -> None:
    if not summary.rewards:
        logger.warning('{} {}: no rollouts scored', model, level)
        return
    n = len(summary.rewards)
    logger.info(
        '{} {}: n={} mean_reward={:.3f} parse_ok={:.0%} run_spend=${:.4f}',
        model,
        level,
        n,
        sum(summary.rewards) / n,
        sum(summary.successes) / n,
        state.spent_usd,
    )


@dataclass(frozen=True, slots=True)
class EvalRow:
    """One eval instance narrowed to what the rollout path needs."""

    instance_id: str
    instance: RefundInstance
    is_out_of_window: bool


def _load_rows(instances_dir: Path, split: str, level: str, n: int, seed: int) -> list[EvalRow]:
    path = instances_dir / f'{split}_{level}.jsonl'
    records = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    assert records, f'no instances in {path}'
    rng = np.random.default_rng(seed)
    chosen = rng.permutation(len(records))[:n] if n < len(records) else range(len(records))
    rows: list[EvalRow] = []
    for i in chosen:
        record = records[int(i)]
        info = record['info']
        assert isinstance(info, dict), f'{path}: record info must be a mapping'
        rows.append(
            EvalRow(
                instance_id=str(info['instance_id']),
                instance=record_to_instance(_instance_payload(record)),
                is_out_of_window=bool(info['is_out_of_window']),
            )
        )
    return rows


def _instance_payload(record: dict[str, object]) -> dict[str, object]:
    payload = record['instance']
    assert isinstance(payload, dict), 'record must carry an instance mapping'
    return payload


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Zero-shot eval of models on refund-claim instances'
    )
    parser.add_argument('--models', required=True, help='comma-separated OpenRouter model ids')
    parser.add_argument(
        '--split', default='eval_unseen', choices=['dev', 'eval_unseen', 'eval_known']
    )
    parser.add_argument(
        '--levels',
        default='L2',
        help='comma-separated level names (L2 only: the level lever never materialized)',
    )
    parser.add_argument('--n', type=int, default=100, help='instances per level')
    parser.add_argument('--k', type=int, default=8, help='rollouts per instance')
    parser.add_argument('--temperature', type=float, default=1.0)
    parser.add_argument('--max-tokens', type=int, default=4096)
    parser.add_argument(
        '--reasoning-effort',
        choices=['minimal', 'low', 'medium', 'high'],
        default='low',
        help='fixed reasoning effort for reasoning models',
    )
    parser.add_argument('--concurrency', type=int, default=4, help='max simultaneous API requests')
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='clamp n<=10, k<=2 and print the full-sweep cost projection',
    )
    parser.add_argument('--env-file', type=Path, default=Path('.env'))
    parser.add_argument('--reward-config', type=Path, default=Path('configs/refund/reward.yaml'))
    parser.add_argument('--instances-dir', type=Path, default=Path('instances/refund_v4'))
    parser.add_argument('--rollouts-dir', type=Path, default=Path('rollouts/refund_v4'))
    args = parser.parse_args()
    args.models = [m.strip() for m in args.models.split(',')]
    args.levels = [level.strip() for level in args.levels.split(',')]
    if args.dry_run:
        args.n, args.k = min(args.n, 10), min(args.k, 2)
    return args


if __name__ == '__main__':
    main()
