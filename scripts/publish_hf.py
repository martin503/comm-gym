import argparse
import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from huggingface_hub import HfApi
from loguru import logger
from tqdm import tqdm

from commgym.core.logging import setup_logging

ROOT = Path(__file__).resolve().parents[1]
DATASET_NAME = 'comm-gym'
TASKS = ('offer', 'cartopt')
# final eval models only; qwen3.7-flash dev fragments and offer baselines stay local
MODELS = ('openai__gpt-6-luna', 'qwen__qwen3.8-27b')


@dataclass(frozen=True, slots=True)
class Entry:
    local: Path
    repo_path: str
    rows: int
    sha256: str


def main() -> None:
    args = _parse_args()
    setup_logging()
    manifest = build_manifest()
    if args.dry_run:
        _print_manifest(manifest)
        return
    api = HfApi()
    repo_id = args.repo or f'{_whoami(api)}/{DATASET_NAME}'
    _publish(api, repo_id, manifest, public=args.public)
    if args.verify:
        _verify(api, repo_id, manifest)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Publish offer/cartopt instances and final rollouts to a HF dataset repo'
    )
    parser.add_argument('--repo', default=None, help='dataset repo id (default: <user>/comm-gym)')
    parser.add_argument(
        '--public', action='store_true', help='make the repo public (default: private)'
    )
    parser.add_argument('--dry-run', action='store_true', help='print the manifest, no network')
    parser.add_argument(
        '--verify', action='store_true', help='after upload, re-download and compare sha256'
    )
    return parser.parse_args()


def build_manifest() -> list[Entry]:
    entries: list[Entry] = []
    for task in TASKS:
        entries += _entries_for(
            sorted((ROOT / 'instances' / task).glob('*.jsonl')), f'{task}/instances'
        )
        for model in MODELS:
            model_dir = ROOT / 'rollouts' / task / model
            entries += _entries_for(
                sorted(model_dir.glob('eval_unseen*.jsonl')), f'{task}/rollouts/{model}'
            )
    return entries


def _entries_for(files: list[Path], repo_dir: str) -> list[Entry]:
    if not files:
        raise FileNotFoundError(f'no source files for {repo_dir}; expected under {ROOT}')
    return [Entry(f, f'{repo_dir}/{f.name}', _count_rows(f), _sha256(f)) for f in files]


def _count_rows(path: Path) -> int:
    with path.open('rb') as fh:
        return sum(1 for _ in fh)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b''):
            digest.update(chunk)
    return digest.hexdigest()


def render_card(manifest: list[Entry]) -> str:
    today = datetime.now(UTC).strftime('%Y-%m-%d')
    inventory = '\n'.join(
        f'| {e.repo_path} | {e.rows} | {e.local.stat().st_size / 1e6:.2f} |' for e in manifest
    )
    return f"""---
license: other
pretty_name: comm-gym offer & cartopt instances and final rollouts
---

# comm-gym: offer & cartopt — instances and final rollouts

Evaluation artifacts from the comm-gym project: synthetic grocery-communication
tasks derived from the Dunnhumby Complete Journey dataset. JSONL throughout;
each line is one self-contained JSON object.

## Contents

| file | rows | size (MB) |
|---|---:|---:|
{inventory}

## Tasks

### offer

Write a grocery push notification grounded in a household's live coupons.
`eval_unseen` = 50 late-window anchor instances; levels L1-L3 vary the number of
relevant coupons. Scoring: policy gate (groundedness), then pairwise LLM judge
on gate passers. `eval_unseen.refs.jsonl` holds judge-side reference messages
(written by the judge model family). `dev` = 10 development instances.

### cartopt

Cart optimization: given a menu of products, coupons, and constraints, assemble
the cheapest feasible cart. Levels L1-L4; graded programmatically against
solver ground truth (`info.c_star_cents`), no judge. Each instance file carries
solver metadata in `info` and the full environment in `instance`. `dev` splits
are 30 instances, `eval_unseen` are 100 per level.

## Rollout records

Fields: `instance_id`, `level`, `stratum`, `model`, `sampling_params`,
`rollout_idx`, `prompt` (message list), `completion`, `parsed`, `parse_reason`,
`components`, `reward`, `tokens`, `cost_usd`, `latency_s`, `seed`, `git_sha`,
`timestamp`. Offer rollouts have `*.judged.jsonl` sidecars (`judge_win`,
`order_scores`, `judge_model`, `completion_sha256`, `tokens`, `cost_usd`).

## Provenance

- Sampling: temperature 1.0 everywhere; offer max_tokens 4096, cartopt 8192;
  reasoning effort low, except luna's offer run (reasoning off, historical).
- k = 8 rollouts per instance; split `eval_unseen`.
- Runs 2026-10-23 (cartopt luna) through 2026-10-25 (both qwen sweeps); each
  record embeds its own `git_sha` and `timestamp`.
- Judge (offer only): `anthropic/claude-haiku-5.5` via OpenRouter.

## Caveats

- cartopt qwen3.8-27b covers L1/L2 only (10 instances x k=8 per level): the
  API-key budget was exhausted mid-sweep and L3/L4 completions truncated at
  max_tokens 8192 (`parse:no_answer_block`), so those rollouts were discarded
  rather than published. The L3/L4 absence is a budget artifact, not a
  capability result.
- Offer judged sidecars cover only messages that passed the policy gate;
  scores computed over passers are a selection effect.
- Offer judge and reference-message author are the same model family
  (Haiku-5.5); a self-preference caveat applies.
- Dev splits are included for reference; headline numbers use `eval_unseen`.

License: research/evaluation use only. Generated {today} by `scripts/publish_hf.py`.
"""


def _publish(api: HfApi, repo_id: str, manifest: list[Entry], public: bool) -> None:
    logger.info('ensuring dataset repo {} exists ({})', repo_id, 'public' if public else 'private')
    # exist_ok=True leaves an existing repo's visibility untouched; flip it on the Hub if needed
    api.create_repo(repo_id, repo_type='dataset', private=not public, exist_ok=True)
    card = render_card(manifest)
    api.upload_file(
        path_or_fileobj=card.encode(),
        path_in_repo='README.md',
        repo_id=repo_id,
        repo_type='dataset',
    )
    for entry in tqdm(manifest, desc='upload', unit='file'):
        api.upload_file(
            path_or_fileobj=entry.local,
            path_in_repo=entry.repo_path,
            repo_id=repo_id,
            repo_type='dataset',
        )
    logger.success(
        'uploaded {} files to https://huggingface.co/datasets/{}', len(manifest), repo_id
    )


def _verify(api: HfApi, repo_id: str, manifest: list[Entry]) -> None:
    mismatches: list[str] = []
    for entry in tqdm(manifest, desc='verify', unit='file'):
        downloaded = Path(api.hf_hub_download(repo_id, entry.repo_path, repo_type='dataset'))
        if _sha256(downloaded) != entry.sha256:
            mismatches.append(entry.repo_path)
            logger.error('sha256 mismatch for {}', entry.repo_path)
    if mismatches:
        raise RuntimeError(f'{len(mismatches)} uploaded files differ: {", ".join(mismatches)}')
    logger.success('verified: all {} files sha256-match the local copies', len(manifest))


def _whoami(api: HfApi) -> str:
    name = api.whoami()['name']
    assert isinstance(name, str) and name, f'whoami returned no username: {name!r}'
    return name


def _print_manifest(manifest: list[Entry]) -> None:
    total = sum(e.local.stat().st_size for e in manifest)
    logger.info(
        'dry run: {} files, {:.1f} MB total — nothing uploaded', len(manifest), total / 1e6
    )
    for e in manifest:
        logger.info(
            '{:>6} rows  {:>7.2f} MB  {}', e.rows, e.local.stat().st_size / 1e6, e.repo_path
        )


if __name__ == '__main__':
    main()
