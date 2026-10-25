import argparse
import json
import math
import os
import zlib
from collections import Counter
from pathlib import Path

import anyio
import pandas as pd
from anyio import Semaphore, create_task_group
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
from commgym.dunnhumby.clean import prepare_transactions
from commgym.dunnhumby.config import CleaningConfig, PricingConfig, SplitsConfig
from commgym.dunnhumby.load import (
    load_campaign_targeting,
    load_campaigns,
    load_coupon_eligibility,
    load_coupon_redemptions,
    load_demographics,
    load_products,
    load_transactions,
)
from commgym.dunnhumby.prices import PricePoint, build_price_table
from commgym.dunnhumby.splits import Splits, build_splits
from commgym.refund.config import TaskConfig
from commgym.refund.coupons import CouponIndex, build_coupon_index
from commgym.refund.generator import (
    AnchorPlan,
    build_refund_context,
    claim_spec,
    finalize_anchor,
    plan_batch,
)
from commgym.refund.instance import RefundInstance, instance_to_record
from commgym.refund.policy import Decision
from commgym.refund.prompts import messages
from commgym.refund.renderer import (
    PROMPT_REVISION,
    RenderOutcome,
    render_anchor,
    split_sentences,
)

# plan surplus anchors so render discards still leave n usable ones (smoke ok-rate ~75%)
PLAN_SURPLUS = 1.5
LOG_DIR = Path('experiments/261024_llm_text_gen')


class CostedTextModel:
    """TextModel over OpenRouter with a running spend estimate for the budget guard."""

    def __init__(
        self, client: OpenRouterClient, prices: dict[str, dict[str, str]], cap_usd: float
    ) -> None:
        self._client = client
        self._prices = prices
        self.cap_usd = cap_usd
        self.spent_usd = 0.0
        self.calls = 0

    @property
    def over_budget(self) -> bool:
        return self.spent_usd > self.cap_usd

    async def complete(
        self, model: str, prompt: str, *, temperature: float, max_tokens: int
    ) -> str:
        result = await self._client.chat(
            model,
            [{'role': 'user', 'content': prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        self.calls += 1
        self.spent_usd += estimate_cost_usd(
            self._prices, model, result.prompt_tokens, result.completion_tokens
        )
        return result.text


async def amain(args: argparse.Namespace) -> None:
    cfg = load_config(TaskConfig, args.task_config)
    txc, prices, coupons, splits, campaigns = _load(args, cfg)
    ctx = build_refund_context(txc, prices, coupons, splits, campaigns, cfg)
    seed = zlib.crc32(f'{args.seed}-{args.split}'.encode())
    verifiers = [v.strip() for v in args.verifier_models.split(',')]
    for model in (args.writer_model, *verifiers):
        assert model != args.models_excluded, (
            f'{model} is the eval model; keep it out of writing and verifying'
        )
    market = fetch_model_prices()
    for model in (args.writer_model, *verifiers):
        assert model in market, f'no pricing for {model}; cost logging needs the models endpoint'
    batch = plan_batch(ctx, args.split, math.ceil(args.n * PLAN_SURPLUS), seed)
    client = OpenRouterClient(load_api_key(os.environ, args.env_file))
    text = CostedTextModel(client, market, args.max_cost)
    cache_path = LOG_DIR / f'{args.split}_cache_v{PROMPT_REVISION}.jsonl'
    cache = _load_cache(cache_path)
    outcomes: dict[str, RenderOutcome] = dict(cache)
    discards: Counter[tuple[str, str]] = Counter()
    skipped_for_budget = 0
    lock = anyio.Lock()
    semaphore = Semaphore(args.concurrency)
    bar = tqdm(total=len(batch.plans), desc=f'{args.split} anchors', unit='anchor')

    async def one(plan: AnchorPlan) -> None:
        nonlocal skipped_for_budget
        if text.over_budget:
            skipped_for_budget += 1
            bar.update(1)
            return
        cached = cache.get(plan.cache_key)
        if cached is not None:
            outcome = cached
        else:
            async with semaphore:
                outcome = await render_anchor(
                    plan.lines,
                    [claim_spec(claim) for claim in plan.claims],
                    text,
                    args.writer_model,
                    verifiers,
                )
            async with lock:
                _append_cache(cache_path, plan.cache_key, outcome)
        async with lock:
            outcomes[plan.cache_key] = outcome
            for entry in outcome.discards:
                discards[entry] += 1
        bar.update(1)

    async with create_task_group() as tasks:
        for plan in batch.plans:
            tasks.start_soon(one, plan)
    bar.close()
    passed = [
        plan for plan in batch.plans if plan.cache_key in outcomes and outcomes[plan.cache_key].ok
    ]
    rendered = [
        finalize_anchor(
            plan,
            index,
            outcomes[plan.cache_key].references,
            outcomes[plan.cache_key].sentences,
        )
        for index, plan in enumerate(passed)
    ][: args.n]
    logger.info(
        '{}: {} plans, {} rendered ok, {} kept; discards {}; spent ${:.2f} over {} calls',
        args.split,
        len(batch.plans),
        sum(1 for o in outcomes.values() if o.ok),
        len(rendered),
        dict(discards),
        text.spent_usd,
        text.calls,
    )
    _write_discard_report(args.split, discards)
    if len(rendered) < args.n:
        logger.error(
            '{}: only {}/{} anchors survived rendering (budget-skipped {}); nothing written,'
            ' cache preserved for resume',
            args.split,
            len(rendered),
            args.n,
            skipped_for_budget,
        )
        raise SystemExit(1)
    _write_instances(args, cfg, rendered)


def _write_instances(
    args: argparse.Namespace, cfg: TaskConfig, rendered: list[tuple[RefundInstance, ...]]
) -> None:
    args.out_dir.mkdir(parents=True, exist_ok=True)
    levels = [f'L{k + 1}' for k in range(cfg.claims_per_anchor)]
    previews: list[str] = []
    for level_index, level in enumerate(levels):
        out_path = args.out_dir / f'{args.split}_{level}.jsonl'
        with out_path.open('w') as f:
            for anchor in rendered:
                instance = anchor[level_index]
                info = {
                    'instance_id': instance.instance_id,
                    'anchor_id': instance.anchor_id,
                    'household': instance.household,
                    'basket': instance.basket,
                    'purchase_day': instance.purchase_day,
                    'claim_day': instance.claim_day,
                    'is_out_of_window': instance.is_out_of_window,
                    'n_lines': len(instance.lines),
                    'n_coupons': len(instance.coupons),
                    'claim_reasons': [c.truth_reason.value for c in instance.claims],
                    'claim_kinds': [c.reference_kind for c in instance.claims],
                    'writer_model': args.writer_model,
                }
                f.write(
                    json.dumps({'info': info, 'instance': instance_to_record(instance)}) + '\n'
                )
        previews += [_render_preview(anchor[level_index]) for anchor in rendered]
        logger.info('{}: {} instances written to {}', level, len(rendered), out_path)
    kept = previews[: args.preview_n]
    args.preview.parent.mkdir(parents=True, exist_ok=True)
    args.preview.write_text('# Refund instance preview\n\n' + '\n\n---\n\n'.join(kept))
    logger.info('preview of {} instances written to {}', len(kept), args.preview)
    _log_v2_stats(rendered, args)


def _log_v2_stats(anchors: list[tuple[RefundInstance, ...]], args: argparse.Namespace) -> None:
    """Supply check for the v2 hardeners: policy mix and how often the new rules bind."""
    policies = Counter(
        (
            anchor[-1].policy.claim_window_days,
            anchor[-1].policy.price_tolerance_cents,
            anchor[-1].policy.refund_cap_cents,
            anchor[-1].policy.price_match_national_only,
        )
        for anchor in anchors
    )
    zero_paid = 0
    approved = 0
    same_line_pairs = 0
    stated_numbers = 0
    claims_total = 0
    for anchor in anchors:
        claims = anchor[-1].claims
        claims_total += len(claims)
        zero_paid += sum(
            1 for c in claims if c.truth_decision is Decision.APPROVE and c.truth_refund_cents == 0
        )
        approved += sum(1 for c in claims if c.truth_decision is Decision.APPROVE)
        stated_numbers += sum(1 for c in claims if c.stated_number)
        if len(claims) >= 2 and claims[0].truth_line == claims[1].truth_line:
            same_line_pairs += 1
    logger.info(
        'v2 stats: writer {}, {} distinct policies (top {}), '
        '{}/{} approved claims paid 0c (dedup/cap), {}/{} anchors pair claims on one line, '
        '{}/{} claims carry a stated number',
        args.writer_model,
        len(policies),
        policies.most_common(1)[0][0],
        zero_paid,
        approved,
        same_line_pairs,
        len(anchors),
        stated_numbers,
        claims_total,
    )


def _load_cache(path: Path) -> dict[str, RenderOutcome]:
    if not path.is_file():
        return {}
    cache: dict[str, RenderOutcome] = {}
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        cache[str(record['key'])] = RenderOutcome(
            ok=bool(record['ok']),
            references=tuple(str(r) for r in record['references']),
            sentences=tuple(str(s) for s in record['sentences']),
            discards=tuple((str(a), str(b)) for a, b in record['discards']),
            detail=record['detail'],
        )
    return cache


def _append_cache(path: Path, key: str, outcome: RenderOutcome) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a') as f:
        f.write(
            json.dumps(
                {
                    'key': key,
                    'ok': outcome.ok,
                    'references': list(outcome.references),
                    'sentences': list(outcome.sentences),
                    'discards': [list(d) for d in outcome.discards],
                    'detail': outcome.detail,
                }
            )
            + '\n'
        )


def _write_discard_report(split: str, discards: Counter[tuple[str, str]]) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    path = LOG_DIR / f'{split}_discards.json'
    path.write_text(
        json.dumps({f'{a}|{b}': n for (a, b), n in sorted(discards.items())}, indent=2)
    )
    logger.info('discard log written to {}', path)


def _load(
    args: argparse.Namespace, cfg: TaskConfig
) -> tuple[pd.DataFrame, dict[tuple[int, int], PricePoint], CouponIndex, Splits, tuple]:
    products = load_products(args.data_dir)
    tx = load_transactions(args.data_dir)
    txc, _ = prepare_transactions(tx, products, load_config(CleaningConfig, args.cleaning_config))
    product_sizes = pd.DataFrame(
        {'product_id': [p.product_id for p in products], 'size': [p.size for p in products]}
    )
    txc = txc.merge(product_sizes, left_on='PRODUCT_ID', right_on='product_id').drop(
        columns='product_id'
    )
    prices = build_price_table(txc, load_config(PricingConfig, args.pricing_config))
    campaigns = tuple(load_campaigns(args.data_dir))
    coupons = build_coupon_index(
        load_coupon_eligibility(args.data_dir),
        list(campaigns),
        load_campaign_targeting(args.data_dir),
        load_coupon_redemptions(args.data_dir),
        txc,
        min_redemptions=cfg.min_redemptions,
    )
    demographics = {d.household_key for d in load_demographics(args.data_dir)}
    coverage = (
        txc.groupby(['commodity', 'WEEK_NO']).agg(n_skus=('PRODUCT_ID', 'nunique')).reset_index()
    )
    splits = build_splits(
        txc, demographics, coverage, load_config(SplitsConfig, args.splits_config)
    )
    return txc, prices, coupons, splits, campaigns


def _render_preview(instance: RefundInstance) -> str:
    prompt = messages(instance)
    policy = instance.policy
    rows = [
        f'| {sentence} | {claim.stated_type.value} | {claim.truth_line} |'
        f' {claim.truth_decision.value} | {claim.truth_reason.value}'
        f' | {claim.truth_refund_cents}c |'
        for claim, sentence in zip(instance.claims, split_sentences(instance.message), strict=True)
    ]
    return (
        f'## {instance.instance_id} (anchor {instance.anchor_id},'
        f' out-of-window: {instance.is_out_of_window})\n\n'
        f'Policy: window {policy.claim_window_days}d, tolerance'
        f' {policy.price_tolerance_cents}c, cap {policy.refund_cap_cents}c,'
        f' national-only {policy.price_match_national_only}\n\n'
        f'### System\n\n{prompt[0]["content"]}\n\n### User\n\n{prompt[1]["content"]}\n\n'
        '### Truth\n\n| message | stated | line | decision | reason | refund |\n'
        '|---|---|---|---|---|---|\n' + '\n'.join(rows)
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Plan, LLM-render, and verify nested refund instances for one split'
    )
    parser.add_argument(
        '--split', default='dev', choices=['train', 'dev', 'eval_unseen', 'eval_known']
    )
    parser.add_argument('--n', type=int, default=10, help='anchors kept (each yields L1-L3)')
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument(
        '--writer-model', default='anthropic/claude-haiku-5.5', help='model that writes the texts'
    )
    parser.add_argument(
        '--verifier-models',
        default='anthropic/claude-haiku-5.5,deepseek/deepseek-v4.1-flash-1017',
        help='comma-separated models that independently resolve and extract',
    )
    parser.add_argument(
        '--models-excluded',
        default='openai/gpt-6-luna',
        help='the eval model, barred from writing and verifying (circularity guard)',
    )
    parser.add_argument('--concurrency', type=int, default=4)
    parser.add_argument(
        '--max-cost',
        type=float,
        default=1.5,
        help='per-run spend cap; stop rendering new anchors past it (cache preserved)',
    )
    parser.add_argument('--env-file', type=Path, default=Path('.env'))
    parser.add_argument('--data-dir', type=Path, default=None)
    parser.add_argument('--task-config', type=Path, default=Path('configs/refund/task.yaml'))
    parser.add_argument('--cleaning-config', type=Path, default=Path('configs/data.yaml'))
    parser.add_argument('--pricing-config', type=Path, default=Path('configs/pricing.yaml'))
    parser.add_argument('--splits-config', type=Path, default=Path('configs/splits.yaml'))
    parser.add_argument('--out-dir', type=Path, default=Path('instances/refund_v4'))
    parser.add_argument(
        '--preview', type=Path, default=Path('reports/refund_instances_preview_v4.md')
    )
    parser.add_argument('--preview-n', type=int, default=10)
    return parser.parse_args()


if __name__ == '__main__':
    args = _parse_args()
    setup_logging()
    anyio.run(amain, args)
