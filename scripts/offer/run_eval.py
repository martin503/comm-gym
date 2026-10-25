import argparse
from pathlib import Path

import anyio

from commgym.core.cli import comma_list
from commgym.core.config import load_config, load_models
from commgym.core.eval import LevelSpec, SweepPlan, run_sweep, select_models
from commgym.core.logging import setup_logging
from commgym.core.openrouter import OpenRouterClient
from commgym.core.rollouts import read_jsonl
from commgym.core.runner import EvalItem, GradeFn, GradeOutcome
from commgym.offer.config import GateConfig, RewardConfig
from commgym.offer.generator import InstanceRecord, record_to_instance
from commgym.offer.instance import OfferInstance
from commgym.offer.lexicon import Lexicon, build_lexicon, load_commodity_names
from commgym.offer.prompts import system_prompt, user_prompt
from commgym.offer.reward import components_of, grade, parse_completion

SWEEP_PLAN = SweepPlan(full_n=50, full_k=8)


def main() -> None:
    args = _parse_args()
    setup_logging()
    anyio.run(amain, args)


async def amain(args: argparse.Namespace, client: OpenRouterClient | None = None) -> None:
    gate_cfg = load_config(GateConfig, args.gate_config)
    reward_cfg = load_config(RewardConfig, args.reward_config)
    lexicon = build_lexicon(load_commodity_names(args.commodities))
    instances = _load_instances(args.instances_dir / f'{args.split}.jsonl')
    models = select_models(load_models(args.config), args.models)
    specs = {
        level: _level_spec(args, level, instances, lexicon, gate_cfg, reward_cfg)
        for level in args.levels
    }
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
        success_label='gate_pass',
        client=client,
        dry_run=args.dry_run,
    )


def _level_spec(
    args: argparse.Namespace,
    level: str,
    instances: list[OfferInstance],
    lexicon: Lexicon,
    gate_cfg: GateConfig,
    reward_cfg: RewardConfig,
) -> LevelSpec:
    subset = instances[: args.n]
    items = [
        EvalItem(
            instance.instance_id,
            [{'role': 'user', 'content': user_prompt(instance, level, lexicon)}],
            'anchor',
        )
        for instance in subset
    ]
    return LevelSpec(
        items=items,
        grade_fn=_make_grader(subset, level, lexicon, gate_cfg, reward_cfg),
        system_message=system_prompt(gate_cfg.max_words),
        success_key='gate_pass',
    )


def _make_grader(
    instances: list[OfferInstance],
    level: str,
    lexicon: Lexicon,
    gate_cfg: GateConfig,
    reward_cfg: RewardConfig,
) -> GradeFn:
    by_id = {instance.instance_id: instance for instance in instances}

    def grade_fn(item: EvalItem, completion: str) -> GradeOutcome:
        instance = by_id[item.instance_id]
        graded = grade(completion, instance, level, lexicon, gate_cfg, reward_cfg)
        parsed = parse_completion(completion)
        parsed_selection = parsed.selected if parsed.parse_ok else None
        return GradeOutcome(
            reward=graded.reward,
            parsed=None if parsed_selection is None else list(parsed_selection),
            parse_reason=parsed.reason,
            components=components_of(graded, instance, level),
        )

    return grade_fn


def _load_instances(path: Path) -> list[OfferInstance]:
    instances = [
        record_to_instance(InstanceRecord.model_validate(record)) for record in read_jsonl(path)
    ]
    assert instances, f'{path} has no instances; run scripts/offer/generate.py first'
    return instances


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Zero-shot eval of models on offer-message instances (gate-only reward)'
    )
    parser.add_argument(
        '--config', type=Path, default=Path('configs/offer/models.yaml'), help='models config'
    )
    parser.add_argument(
        '--models', type=comma_list, default=[], help='subset of configured models (default: all)'
    )
    parser.add_argument(
        '--split', default='eval_unseen', choices=['dev', 'eval_unseen', 'eval_known']
    )
    parser.add_argument('--levels', type=comma_list, default=['L1', 'L2', 'L3'])
    parser.add_argument('--n', type=int, default=50, help='instances per level (max pool size)')
    parser.add_argument('--k', type=int, default=8, help='rollouts per instance')
    parser.add_argument('--concurrency', type=int, default=4)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--dry-run', action='store_true', help='cap n<=10, k<=2, extrapolate cost')
    parser.add_argument('--env-file', type=Path, default=Path('.env'))
    parser.add_argument('--gate-config', type=Path, default=Path('configs/offer/gate.yaml'))
    parser.add_argument('--reward-config', type=Path, default=Path('configs/offer/reward.yaml'))
    parser.add_argument('--commodities', type=Path, default=Path('configs/offer/commodities.txt'))
    parser.add_argument('--instances-dir', type=Path, default=Path('instances/offer'))
    parser.add_argument('--rollouts-dir', type=Path, default=Path('rollouts/offer'))
    args = parser.parse_args()
    if args.dry_run:
        args.n, args.k = min(args.n, 10), min(args.k, 2)
    return args


if __name__ == '__main__':
    main()
