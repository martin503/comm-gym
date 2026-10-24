import argparse
import json
import os
from pathlib import Path

import anyio
from loguru import logger

from commgym.core.config import load_config
from commgym.core.logging import setup_logging
from commgym.core.openrouter import OpenRouterClient, fetch_model_prices, load_api_key
from commgym.core.runner import EvalItem, GradeFn, GradeOutcome, RunState, run_level
from commgym.offer.config import GateConfig, RewardConfig
from commgym.offer.generator import InstanceRecord, record_to_instance
from commgym.offer.instance import OfferInstance
from commgym.offer.lexicon import Lexicon, build_lexicon, load_commodity_names
from commgym.offer.prompts import system_prompt, user_prompt
from commgym.offer.reward import grade, parse_completion

FULL_N, FULL_K = 50, 8


def main() -> None:
    args = _parse_args()
    setup_logging()
    anyio.run(amain, args)


async def amain(args: argparse.Namespace, client: OpenRouterClient | None = None) -> None:
    gate_cfg = load_config(GateConfig, args.gate_config)
    reward_cfg = load_config(RewardConfig, args.reward_config)
    lexicon = build_lexicon(load_commodity_names(args.commodities))
    instances = _load_instances(args.instances_dir / f'{args.split}.jsonl')
    prices = fetch_model_prices()
    missing = [m for m in args.models if m not in prices]
    assert not missing, f'no pricing for {missing}; cost logging needs the models endpoint'
    if client is None:
        client = OpenRouterClient(load_api_key(os.environ, args.env_file))
    state = RunState()
    for model in args.models:
        for level in args.levels:
            await _run_level(
                args, model, level, instances, lexicon, gate_cfg, reward_cfg, client, prices, state
            )
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
    instances: list[OfferInstance],
    lexicon: Lexicon,
    gate_cfg: GateConfig,
    reward_cfg: RewardConfig,
    client: OpenRouterClient,
    prices: dict[str, dict[str, str]],
    state: RunState,
) -> None:
    subset = instances[: args.n]
    items = [
        EvalItem(
            instance.instance_id,
            [{'role': 'user', 'content': user_prompt(instance, level, lexicon)}],
            'anchor',
        )
        for instance in subset
    ]
    out_path = args.rollouts_dir / model.replace('/', '__') / f'{args.split}_{level}.jsonl'
    summary = await run_level(
        items,
        _make_grader(subset, level, lexicon, gate_cfg, reward_cfg),
        client,
        model,
        level,
        out_path,
        prices,
        system_prompt(gate_cfg.max_words),
        'gate_pass',
        state,
        k=args.k,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        reasoning_effort=args.reasoning_effort,
        concurrency=args.concurrency,
        seed=args.seed,
    )
    if summary.rewards:
        n = len(summary.rewards)
        logger.info(
            '{} {}: n={} judge-free mean={:.3f} gate_pass={:.0%} run_spend=${:.4f}',
            model,
            level,
            n,
            sum(summary.rewards) / n,
            sum(summary.successes) / n,
            state.spent_usd,
        )
    if args.dry_run and state.rewards:
        per_rollout = state.spent_usd / len(state.rewards)
        logger.info(
            'dry run: full sweep {} levels x {}x{} ~${:.2f} per model',
            len(args.levels),
            FULL_N,
            FULL_K,
            len(args.levels) * FULL_N * FULL_K * per_rollout,
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
        shown = {coupon.code: coupon for coupon in instance.slice_for(level)}
        return GradeOutcome(
            reward=graded.reward,
            parsed=None if parsed_selection is None else list(parsed_selection),
            parse_reason=parsed.reason,
            components={
                'gate_pass': graded.gate_passed,
                'parse_ok': graded.parse_ok,
                'gate_failures': list(graded.failures),
                'affinity': graded.affinity,
                'word_count': graded.word_count,
                'n_selected': len(graded.selected),
                'selected': list(graded.selected),
                'message': graded.message,
                'coupon_keys': {
                    code: [coupon.campaign, coupon.coupon_upc]
                    for code, coupon in shown.items()
                    if code in graded.selected
                },
            },
        )

    return grade_fn


def _load_instances(path: Path) -> list[OfferInstance]:
    instances = [
        record_to_instance(InstanceRecord.model_validate(json.loads(line)))
        for line in path.read_text().splitlines()
        if line.strip()
    ]
    assert instances, f'{path} has no instances; run scripts/offer/generate.py first'
    return instances


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Zero-shot eval of models on offer-message instances (gate-only reward)'
    )
    parser.add_argument('--models', required=True, help='comma-separated OpenRouter model ids')
    parser.add_argument(
        '--split', default='eval_unseen', choices=['dev', 'eval_unseen', 'eval_known']
    )
    parser.add_argument('--levels', default='L1,L2,L3')
    parser.add_argument('--n', type=int, default=50, help='instances per level (max pool size)')
    parser.add_argument('--k', type=int, default=8, help='rollouts per instance')
    parser.add_argument('--temperature', type=float, default=1.0)
    parser.add_argument('--max-tokens', type=int, default=4096)
    parser.add_argument(
        '--reasoning-effort', choices=['minimal', 'low', 'medium', 'high'], default=None
    )
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
    args.models = [m.strip() for m in args.models.split(',')]
    args.levels = [level.strip() for level in args.levels.split(',')]
    if args.dry_run:
        args.n, args.k = min(args.n, 10), min(args.k, 2)
    return args


if __name__ == '__main__':
    main()
