import argparse
import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path

import anyio
from anyio import Semaphore
from loguru import logger
from tqdm import tqdm

from commgym.core.config import load_config
from commgym.core.logging import setup_logging
from commgym.core.openrouter import (
    OpenRouterClient,
    estimate_cost_usd,
    fetch_model_prices,
    load_api_key,
)
from commgym.core.rollouts import read_jsonl
from commgym.offer.config import JudgeConfig
from commgym.offer.judge import JUDGE_PROMPT_VERSION, judge_pair

JUDGE_TAG = 'judged'


@dataclass(frozen=True, slots=True)
class Pending:
    instance_id: str
    level: str
    rollout_idx: int
    sampling_params: dict[str, object]
    completion_sha256: str
    context_prompt: str
    selection: tuple[str, ...]
    message: str


def main() -> None:
    args = _parse_args()
    setup_logging()
    anyio.run(amain, args)


async def amain(args: argparse.Namespace, client: OpenRouterClient | None = None) -> None:
    cfg = load_config(JudgeConfig, args.judge_config)
    refs = _load_refs(args.refs)
    prices = fetch_model_prices()
    assert cfg.model in prices, f'no pricing for {cfg.model}; cost logging needs it'
    if client is None:
        client = OpenRouterClient(load_api_key(os.environ, args.env_file))
    rollout_files = sorted(args.rollouts_dir.glob(f'*/{args.split}_*.jsonl'))
    rollout_files = [f for f in rollout_files if f'.{JUDGE_TAG}.' not in f.name]
    assert rollout_files, f'no rollout files under {args.rollouts_dir} for split {args.split}'
    for path in rollout_files:
        await _judge_file(path, refs, cfg, client, prices, args)


async def _judge_file(
    path: Path,
    refs: dict[tuple[str, str], tuple[tuple[str, ...], str]],
    cfg: JudgeConfig,
    client: OpenRouterClient,
    prices: dict[str, dict[str, str]],
    args: argparse.Namespace,
) -> None:
    level = path.stem.rsplit('_', 1)[1]
    sidecar = path.with_name(f'{path.stem}.{JUDGE_TAG}.jsonl')
    done = _resume_keys(sidecar)
    pending: list[Pending] = []
    for record in read_jsonl(path):
        components = record['components']
        assert isinstance(components, dict), 'components must be a dict'
        if not components.get('gate_pass'):
            continue
        key = (str(record['instance_id']), level)
        reference = refs.get(key)
        if reference is None:
            logger.warning('{}: no reference for {} at {}; skipping', path.name, *key)
            continue
        digest = hashlib.sha256(str(record['completion']).encode()).hexdigest()
        resume_key = (
            str(record['instance_id']),
            _idx(record),
            str(record['sampling_params']),
            digest,
        )
        if resume_key in done:
            continue
        prompt = record['prompt']
        assert isinstance(prompt, list), 'prompt must be a message list'
        message = components['message']
        selected = components['selected']
        assert isinstance(message, str) and isinstance(selected, list), 'component contract broken'
        pending.append(
            Pending(
                instance_id=str(record['instance_id']),
                level=level,
                rollout_idx=_idx(record),
                sampling_params=_params(record),
                completion_sha256=digest,
                context_prompt=str(prompt[-1]['content']),
                selection=tuple(str(code) for code in selected),
                message=message,
            )
        )
    if args.limit:
        pending = pending[: args.limit]
    logger.info('{}: judging {} gate-passed rollouts', path.name, len(pending))
    semaphore = Semaphore(args.concurrency)
    write_lock = anyio.Lock()
    out = sidecar.open('a')
    judged = 0
    try:
        with tqdm(total=len(pending), desc=path.name, unit='pair') as bar:
            async with anyio.create_task_group() as group:

                async def run_one(item: Pending) -> None:
                    nonlocal judged
                    async with semaphore:
                        outcome = await judge_pair(
                            client,
                            cfg,
                            context_prompt=item.context_prompt,
                            candidate_selection=item.selection,
                            candidate_message=item.message,
                            reference_selection=refs[(item.instance_id, item.level)][0],
                            reference_message=refs[(item.instance_id, item.level)][1],
                        )
                    row = {
                        'instance_id': item.instance_id,
                        'level': item.level,
                        'rollout_idx': item.rollout_idx,
                        'sampling_params': item.sampling_params,
                        'completion_sha256': item.completion_sha256,
                        'judge_win': outcome.judge_win,
                        'order_scores': list(outcome.order_scores),
                        'judge_model': cfg.model,
                        'judge_prompt_version': JUDGE_PROMPT_VERSION,
                        'tokens': [outcome.prompt_tokens, outcome.completion_tokens],
                        'cost_usd': estimate_cost_usd(
                            prices, cfg.model, outcome.prompt_tokens, outcome.completion_tokens
                        ),
                        'error': outcome.error,
                    }
                    async with write_lock:
                        out.write(json.dumps(row) + '\n')
                        out.flush()
                    judged += 1
                    bar.update()

                for item in pending:
                    group.start_soon(run_one, item)
    finally:
        out.close()
    logger.info('{}: wrote {} judgments to {}', path.name, judged, sidecar)


def _resume_keys(sidecar: Path) -> set[tuple[str, int, str, str]]:
    if not sidecar.is_file():
        return set()
    keys = set()
    for row in read_jsonl(sidecar):
        keys.add(
            (
                str(row['instance_id']),
                _idx(row),
                str(row['sampling_params']),
                str(row['completion_sha256']),
            )
        )
    return keys


def _idx(record: dict[str, object]) -> int:
    value = record['rollout_idx']
    assert isinstance(value, int), 'rollout_idx must be an int'
    return value


def _params(record: dict[str, object]) -> dict[str, object]:
    value = record['sampling_params']
    assert isinstance(value, dict), 'sampling_params must be a dict'
    return dict(value)


def _load_refs(path: Path) -> dict[tuple[str, str], tuple[tuple[str, ...], str]]:
    refs: dict[tuple[str, str], tuple[tuple[str, ...], str]] = {}
    for row in read_jsonl(path):
        key = (str(row['instance_id']), str(row['level']))
        selection = row['selection']
        assert isinstance(selection, list), 'reference selection must be a list'
        refs[key] = (tuple(str(code) for code in selection), str(row['message']))
    assert refs, f'{path} has no references; run scripts/offer/generate_references.py first'
    return refs


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Judge gate-passed rollouts vs stored references')
    parser.add_argument('--split', default='eval_unseen')
    parser.add_argument('--judge-config', type=Path, default=Path('configs/offer/judge.yaml'))
    parser.add_argument(
        '--refs', type=Path, default=None, help='defaults to instances/offer/<split>.refs.jsonl'
    )
    parser.add_argument('--rollouts-dir', type=Path, default=Path('rollouts/offer'))
    parser.add_argument('--concurrency', type=int, default=4)
    parser.add_argument('--limit', type=int, default=0, help='judge at most N pairs (dry run)')
    parser.add_argument('--env-file', type=Path, default=Path('.env'))
    args = parser.parse_args()
    if args.refs is None:
        args.refs = Path('instances/offer') / f'{args.split}.refs.jsonl'
    return args


if __name__ == '__main__':
    main()
