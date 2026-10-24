import argparse
import json
import os
from pathlib import Path

import anyio
import numpy as np
from loguru import logger
from tqdm import tqdm

from commgym.core.config import load_config
from commgym.core.logging import setup_logging
from commgym.core.openrouter import OpenRouterClient, fetch_model_prices, load_api_key
from commgym.offer.baselines import baseline_completions
from commgym.offer.config import GateConfig, RewardConfig
from commgym.offer.generator import InstanceRecord, record_to_instance
from commgym.offer.instance import OfferInstance
from commgym.offer.lexicon import Lexicon, build_lexicon, load_commodity_names
from commgym.offer.prompts import system_prompt, user_prompt
from commgym.offer.reward import grade, parse_completion


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
    assert args.model in prices, f'no pricing for {args.model}'
    if client is None:
        client = OpenRouterClient(load_api_key(os.environ, args.env_file))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    done = _done_keys(args.out)
    rows: list[dict[str, object]] = []
    with (
        args.out.open('a') as f,
        tqdm(total=len(instances) * len(args.levels), desc='references', unit='ref') as bar,
    ):
        for instance in instances:
            for level in args.levels:
                key = (instance.instance_id, level)
                if key in done:
                    bar.update()
                    continue
                row = await _one_reference(
                    client,
                    args.model,
                    instance,
                    level,
                    lexicon,
                    gate_cfg,
                    reward_cfg,
                    args.temperature,
                    args.max_attempts,
                )
                if row is None:
                    # fallback: the affine template as a gate-clean stand-in
                    template = baseline_completions(
                        instance, level, lexicon, np.random.default_rng(args.seed)
                    )['template_top_affinity']
                    parsed = parse_completion(template)
                    assert parsed.parse_ok and parsed.selected and parsed.message, (
                        'template must parse'
                    )
                    row = {
                        'instance_id': instance.instance_id,
                        'level': level,
                        'model': f'{args.model}+template_fallback',
                        'selection': list(parsed.selected),
                        'message': parsed.message,
                        'gate_pass': True,
                        'attempts': args.max_attempts,
                    }
                    logger.warning('{} {}: model failed the gate; template fallback stored', *key)
                f.write(json.dumps(row) + '\n')
                f.flush()
                rows.append(row)
                bar.update()
    passed = sum(1 for row in rows if row['gate_pass'])
    logger.info('references: {} written, {} gate-clean', len(rows), passed)


async def _one_reference(
    client: OpenRouterClient,
    model: str,
    instance: OfferInstance,
    level: str,
    lexicon: Lexicon,
    gate_cfg: GateConfig,
    reward_cfg: RewardConfig,
    temperature: float,
    max_attempts: int,
) -> dict[str, object] | None:
    messages = [
        {'role': 'system', 'content': system_prompt(gate_cfg.max_words)},
        {'role': 'user', 'content': user_prompt(instance, level, lexicon)},
    ]
    last_failures: tuple[str, ...] = ()
    for attempt in range(1, max_attempts + 1):
        result = await client.chat(model, messages, temperature=temperature, max_tokens=4096)
        parsed = parse_completion(result.text)
        if not parsed.parse_ok:
            last_failures = (f'parse:{parsed.reason}',)
            continue
        assert parsed.selected is not None and parsed.message is not None, 'parser contract broken'
        completion = (
            '<answer>'
            + json.dumps({'selected': list(parsed.selected), 'message': parsed.message})
            + '</answer>'
        )
        graded = grade(
            completion,
            instance,
            level,
            lexicon,
            gate_cfg,
            reward_cfg,
        )
        if graded.gate_passed:
            return {
                'instance_id': instance.instance_id,
                'level': level,
                'model': model,
                'selection': list(parsed.selected),
                'message': parsed.message,
                'gate_pass': True,
                'attempts': attempt,
            }
        last_failures = graded.failures
    logger.warning(
        '{} {}: {} attempts failed the gate: {}',
        instance.instance_id,
        level,
        max_attempts,
        ', '.join(last_failures),
    )
    return None


def _done_keys(path: Path) -> set[tuple[str, str]]:
    if not path.is_file():
        return set()
    keys = set()
    for line in path.read_text().splitlines():
        if line.strip():
            row = json.loads(line)
            keys.add((str(row['instance_id']), str(row['level'])))
    return keys


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
        description='Generate one gate-clean reference per (instance, level)'
    )
    parser.add_argument('--split', default='eval_unseen')
    parser.add_argument('--model', default='anthropic/claude-haiku-5.5')
    parser.add_argument('--levels', default='L1,L2,L3')
    parser.add_argument('--temperature', type=float, default=0.7)
    parser.add_argument('--max-attempts', type=int, default=3)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--env-file', type=Path, default=Path('.env'))
    parser.add_argument('--gate-config', type=Path, default=Path('configs/offer/gate.yaml'))
    parser.add_argument('--reward-config', type=Path, default=Path('configs/offer/reward.yaml'))
    parser.add_argument('--commodities', type=Path, default=Path('configs/offer/commodities.txt'))
    parser.add_argument('--instances-dir', type=Path, default=Path('instances/offer'))
    parser.add_argument(
        '--out', type=Path, default=None, help='defaults to instances/offer/<split>.refs.jsonl'
    )
    args = parser.parse_args()
    args.levels = [level.strip() for level in args.levels.split(',')]
    if args.out is None:
        args.out = Path('instances/offer') / f'{args.split}.refs.jsonl'
    return args


if __name__ == '__main__':
    main()
