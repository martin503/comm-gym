import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
from loguru import logger

from commgym.core.cli import comma_list, write_report
from commgym.core.config import load_config
from commgym.core.logging import setup_logging
from commgym.core.rollouts import read_jsonl
from commgym.offer.baselines import baseline_completions
from commgym.offer.config import GateConfig, RewardConfig
from commgym.offer.generator import InstanceRecord, record_to_instance
from commgym.offer.instance import OfferInstance
from commgym.offer.lexicon import build_lexicon, load_commodity_names
from commgym.offer.prompts import user_prompt
from commgym.offer.reward import components_of, grade, parse_completion


def main() -> None:
    args = _parse_args()
    setup_logging()
    gate_cfg = load_config(GateConfig, args.gate_config)
    reward_cfg = load_config(RewardConfig, args.reward_config)
    lexicon = build_lexicon(load_commodity_names(args.commodities))
    instances = _load_instances(args.instances_dir / f'{args.split}.jsonl')
    rng = np.random.default_rng(args.seed)
    names = ('template_top_affinity', 'random_template', 'generic')
    summaries = {name: {'n': 0, 'passed': 0, 'affinity': 0.0} for name in names}
    for level in args.levels:
        for name in names:
            out_dir = args.rollouts_dir / f'baseline_{name}'
            out_dir.mkdir(parents=True, exist_ok=True)
            out_path = out_dir / f'{args.split}_{level}.jsonl'
            with out_path.open('w') as f:
                for instance in instances:
                    completion = baseline_completions(instance, level, lexicon, rng)[name]
                    graded = grade(completion, instance, level, lexicon, gate_cfg, reward_cfg)
                    parsed = parse_completion(completion)
                    parsed_selection = parsed.selected if parsed.parse_ok else None
                    components = components_of(graded, instance, level)
                    f.write(
                        json.dumps(
                            {
                                'instance_id': instance.instance_id,
                                'level': level,
                                'stratum': 'anchor',
                                'model': f'baseline/{name}',
                                'sampling_params': {
                                    'temperature': 0.0,
                                    'max_tokens': 0,
                                    'reasoning_effort': None,
                                },
                                'rollout_idx': 0,
                                'prompt': [
                                    {
                                        'role': 'user',
                                        'content': user_prompt(instance, level, lexicon),
                                    }
                                ],
                                'completion': completion,
                                'parsed': None
                                if parsed_selection is None
                                else list(parsed_selection),
                                'parse_reason': parsed.reason,
                                'reward': graded.reward,
                                'components': components,
                                'tokens': [0, 0],
                                'cost_usd': 0.0,
                                'latency_s': 0.0,
                                'seed': args.seed,
                                'git_sha': '',
                                'timestamp': datetime.now(UTC).isoformat(),
                            }
                        )
                        + '\n'
                    )
                    summary = summaries[name]
                    summary['n'] += 1
                    summary['passed'] += int(graded.gate_passed)
                    summary['affinity'] += graded.affinity
            logger.info('{} {}: written to {}', name, level, out_path)
    lines = ['# Offer baselines', '']
    for name, summary in summaries.items():
        lines.append(
            f'- {name}: n={summary["n"]}, gate_pass={summary["passed"] / summary["n"]:.0%}, '
            f'mean affinity={summary["affinity"] / summary["n"]:.3f}'
        )
    lines.append('')
    lines.append('sanity: generic must be gated to 0;')
    lines.append('template_top_affinity affinity must beat random_template')
    write_report(args.report, lines)


def _load_instances(path: Path) -> list[OfferInstance]:
    instances = [
        record_to_instance(InstanceRecord.model_validate(record)) for record in read_jsonl(path)
    ]
    assert instances, f'{path} has no instances; run scripts/offer/generate.py first'
    return instances


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Grade and store offer baselines as rollouts')
    parser.add_argument('--split', default='eval_unseen')
    parser.add_argument('--levels', type=comma_list, default=['L1', 'L2', 'L3'])
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--gate-config', type=Path, default=Path('configs/offer/gate.yaml'))
    parser.add_argument('--reward-config', type=Path, default=Path('configs/offer/reward.yaml'))
    parser.add_argument('--commodities', type=Path, default=Path('configs/offer/commodities.txt'))
    parser.add_argument('--instances-dir', type=Path, default=Path('instances/offer'))
    parser.add_argument('--rollouts-dir', type=Path, default=Path('rollouts/offer'))
    parser.add_argument('--report', type=Path, default=Path('reports/offer/offer_baselines.md'))
    return parser.parse_args()


if __name__ == '__main__':
    main()
