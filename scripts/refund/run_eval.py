import argparse
from dataclasses import dataclass
from pathlib import Path

import anyio
import numpy as np

from commgym.core.cli import comma_list
from commgym.core.config import load_config, load_models
from commgym.core.eval import LevelSpec, SweepPlan, run_sweep, select_models
from commgym.core.logging import setup_logging
from commgym.core.openrouter import OpenRouterClient
from commgym.core.rollouts import read_jsonl
from commgym.core.runner import EvalItem, GradeFn, GradeOutcome
from commgym.refund.config import RewardConfig
from commgym.refund.instance import RefundInstance, record_to_instance
from commgym.refund.prompts import system_prompt, user_prompt
from commgym.refund.reward import grade, parse_completion

# full-sweep target the dry run extrapolates towards, and the pre-agreed budget gate
SWEEP_PLAN = SweepPlan(full_n=100, full_k=8, budget_usd=5.0)


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
        success_label='parse_ok',
        client=client,
        dry_run=args.dry_run,
    )


def _level_spec(args: argparse.Namespace, cfg: RewardConfig, level: str) -> LevelSpec:
    rows = _load_rows(args.instances_dir, args.split, level, args.n, args.seed)
    items = [
        EvalItem(
            row.instance_id,
            [{'role': 'user', 'content': user_prompt(row.instance)}],
            'out_of_window' if row.is_out_of_window else 'in_window',
        )
        for row in rows
    ]
    instances = {row.instance_id: row.instance for row in rows}
    return LevelSpec(
        items=items,
        grade_fn=_make_grader(instances, cfg),
        system_message=system_prompt(),
        success_key='parse_ok',
    )


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


@dataclass(frozen=True, slots=True)
class EvalRow:
    """One eval instance narrowed to what the rollout path needs."""

    instance_id: str
    instance: RefundInstance
    is_out_of_window: bool


def _load_rows(instances_dir: Path, split: str, level: str, n: int, seed: int) -> list[EvalRow]:
    path = instances_dir / f'{split}_{level}.jsonl'
    records = read_jsonl(path)
    assert records, f'no instances in {path}'
    rng = np.random.default_rng(seed)
    chosen = rng.permutation(len(records))[:n] if n < len(records) else range(len(records))
    rows: list[EvalRow] = []
    for i in chosen:
        record = records[int(i)]
        info = record['info']
        assert isinstance(info, dict), f'{path}: record info must be a mapping'
        payload = record['instance']
        assert isinstance(payload, dict), 'record must carry an instance mapping'
        rows.append(
            EvalRow(
                instance_id=str(info['instance_id']),
                instance=record_to_instance(payload),
                is_out_of_window=bool(info['is_out_of_window']),
            )
        )
    return rows


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Zero-shot eval of models on refund-claim instances'
    )
    parser.add_argument(
        '--config', type=Path, default=Path('configs/refund/models.yaml'), help='models config'
    )
    parser.add_argument(
        '--models', type=comma_list, default=[], help='subset of configured models (default: all)'
    )
    parser.add_argument(
        '--split', default='eval_unseen', choices=['dev', 'eval_unseen', 'eval_known']
    )
    parser.add_argument(
        '--levels',
        type=comma_list,
        default=['L2'],
        help='level names (L2 only: the level lever never materialized)',
    )
    parser.add_argument('--n', type=int, default=100, help='instances per level')
    parser.add_argument('--k', type=int, default=8, help='rollouts per instance')
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
    if args.dry_run:
        args.n, args.k = min(args.n, 10), min(args.k, 2)
    return args


if __name__ == '__main__':
    main()
