import argparse
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from loguru import logger

from commgym.core.logging import setup_logging
from commgym.core.stats import (
    bootstrap_mean_ci,
    pass_at_k,
    within_instance_sd,
    zero_variance_fraction,
)
from commgym.refund.baselines import prompt_view_of, rule_parser_answers
from commgym.refund.config import RewardConfig
from commgym.refund.instance import record_to_instance
from commgym.refund.reward import grade_parsed

PASS_KS = (1, 4, 8)
REASONS = (
    'OUTSIDE_WINDOW',
    'NOT_ON_RECEIPT',
    'NEEDS_CLARIFICATION',
    'PRICE_MATCH',
    'WITHIN_TOLERANCE',
    'MISSED_COUPON',
    'NOT_ELIGIBLE',
    'ALREADY_APPLIED',
)
PRECEDENCE_TIERS = {'OUTSIDE_WINDOW': 1, 'NOT_ON_RECEIPT': 2}
LEVEL_LEVER_NOTE = (
    '## Nested levels: measured, then dropped as a difficulty lever',
    '',
    'L1-L3 claim prefixes were designed to ladder difficulty through cross-claim interactions '
    '(refund-cap truncation, same-line dedup, precedence). Measured mean reward by level never '
    'showed a usable gradient: v1 1.000/1.000/0.996, v2 0.950/0.975/0.979, '
    'v3 0.838/0.787/0.800, v4 dry-run 0.988/0.950/0.967 — flat or inverted at every sample '
    'size. Decision 2026-10-25: evaluate at L2 only. L1/L3 instances are still generated and '
    'retained; the level dimension is decoration, not a lever.',
    '',
)
RULE_PARSER_PARITY = 0.05  # |llm - rule parser| <= this counts as 'rule parser ~= LLMs'


@dataclass(frozen=True, slots=True)
class ClaimRollout:
    """One graded claim from a rollout record's components."""

    stated: str
    truth_reason: str
    truth_line: str | None
    kind: str
    stated_number: bool
    decision_ok: bool
    line_ok: bool
    reason_ok: bool
    refund_ok: bool
    false_approve: bool
    false_reject: bool
    dollar_error_cents: int
    predicted_reason: str | None
    predicted_line: str | None


@dataclass(frozen=True, slots=True)
class Rollout:
    instance_id: str
    rollout_idx: int
    stratum: str
    reward: float
    parse_ok: bool
    parse_reason: str | None
    claims: tuple[ClaimRollout, ...]


def main() -> None:
    args = _parse_args()
    setup_logging()
    params: dict[str, object] = {
        'temperature': args.temperature,
        'max_tokens': args.max_tokens,
        'reasoning_effort': args.reasoning_effort,
    }
    sections = [
        f'# Refund eval report — {args.split}',
        '',
        f'Sampling params: `{params}`',
        '',
        *LEVEL_LEVER_NOTE,
    ]
    for model in args.models:
        sections += [f'## {model}', '']
        sections += _model_sections(args, model, params)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text('\n'.join(sections) + '\n')
    logger.info('report written to {}', args.report)


def _model_sections(args: argparse.Namespace, model: str, params: dict[str, object]) -> list[str]:
    model_dir = args.rollouts_dir / model.replace('/', '__')
    per_level: dict[str, list[Rollout]] = {}
    lines = [
        '| level | stratum | inst | mean reward [95% CI] | pass@1 | pass@4 | pass@8 '
        '| parse ok | zero-var | within sd |',
        '|---|---|---|---|---|---|---|---|---|---|',
    ]
    for level in args.levels:
        records = _load_records(model_dir / f'{args.split}_{level}.jsonl', params)
        if not records:
            logger.warning('{} {}: no rollouts for {}', model, level, params)
            continue
        per_level[level] = records
        for stratum in ('all', 'in_window', 'out_of_window'):
            subset = records if stratum == 'all' else [r for r in records if r.stratum == stratum]
            if not subset:
                continue
            stats = _instance_stats(subset)
            lines.append(
                f'| {level} | {stratum} | {stats.n_instances} '
                f'| {stats.reward_mean:.3f} [{stats.reward_lo:.3f}, {stats.reward_hi:.3f}] '
                f'| {_pct(stats.pass_at[1])} | {_pct(stats.pass_at[4])} '
                f'| {_pct(stats.pass_at[8])} | {stats.parse_ok:.0%} '
                f'| {stats.zero_var:.0%} | {stats.within_sd:.3f} |'
            )
    if not per_level:
        return lines
    deepest = per_level[args.levels[-1]]
    claims = [claim for record in deepest for claim in record.claims]
    # claim-level tables use the deepest level only: nested levels would re-count anchors
    lines += ['', '## Claim-level (deepest level, every anchor exactly once)', '']
    lines += _claim_accuracy_table(claims)
    lines += ['', '### Reason confusion (rows truth, columns predicted)', '']
    lines += _confusion_table(deepest)
    lines += ['', '### Stated-number claims', '']
    lines += _stated_number_table(claims)
    lines += ['', '### Error economics', '']
    lines += _error_economics(deepest)
    lines += ['', '## Failure taxonomy (claims)', '']
    lines += [f'- {dict(_claim_taxonomy(claims))}']
    lines += ['', '## Examples', '']
    lines += _examples(deepest)
    lines += ['', '## Decision inputs (spec §10)', '']
    lines += _rule_parser_compare(args, deepest)
    lines += _decision_inputs(per_level, deepest)
    return lines


def _load_records(path: Path, params: dict[str, object]) -> list[Rollout]:
    if not path.is_file():
        return []
    rollouts: list[Rollout] = []
    for line in path.read_text().splitlines():
        record = json.loads(line)
        if record.get('sampling_params') != params:
            continue
        components = record['components']
        assert isinstance(components, dict), 'record components must be a mapping'
        raw_claims = components.get('claims', [])
        assert isinstance(raw_claims, list), 'claims component must be a list'
        parsed = record.get('parsed')
        assert parsed is None or isinstance(parsed, list), 'parsed field must be a list'

        def _predicted_line(index: int) -> str | None:
            if not isinstance(parsed, list) or index >= len(parsed):
                return None
            entry = parsed[index]
            return str(entry['line']) if isinstance(entry, dict) else None

        claims = tuple(
            ClaimRollout(
                stated=str(claim['stated']),
                truth_reason=str(claim['truth_reason']),
                truth_line=claim['truth_line'],
                kind=str(claim['kind']),
                stated_number=bool(claim.get('stated_number', False)),
                decision_ok=bool(claim['decision_ok']),
                line_ok=bool(claim['line_ok']),
                reason_ok=bool(claim['reason_ok']),
                refund_ok=bool(claim['refund_ok']),
                false_approve=bool(claim['false_approve']),
                false_reject=bool(claim['false_reject']),
                dollar_error_cents=int(claim['dollar_error_cents']),
                predicted_reason=claim['predicted_reason'],
                predicted_line=_predicted_line(index),
            )
            for index, claim in enumerate(raw_claims)
            if isinstance(claim, dict)
        )
        rollouts.append(
            Rollout(
                instance_id=str(record['instance_id']),
                rollout_idx=int(record['rollout_idx']),
                stratum=str(record['stratum']),
                reward=float(record['reward']),
                parse_ok=bool(components['parse_ok']),
                parse_reason=record['parse_reason'],
                claims=claims,
            )
        )
    return rollouts


@dataclass(frozen=True, slots=True)
class Stats:
    n_instances: int
    reward_mean: float
    reward_lo: float
    reward_hi: float
    pass_at: dict[int, float | None]
    parse_ok: float
    zero_var: float
    within_sd: float


def _instance_stats(records: list[Rollout]) -> Stats:
    by_instance: dict[str, list[Rollout]] = defaultdict(list)
    for record in records:
        by_instance[record.instance_id].append(record)
    groups = list(by_instance.values())
    reward_groups = [[r.reward for r in group] for group in groups]
    success_groups = [[r.reward == 1.0 for r in group] for group in groups]
    mean, lo, hi = bootstrap_mean_ci([float(np.mean(group)) for group in reward_groups])
    return Stats(
        n_instances=len(groups),
        reward_mean=mean,
        reward_lo=lo,
        reward_hi=hi,
        pass_at={k: pass_at_k(success_groups, k) for k in PASS_KS},
        parse_ok=sum(1 for r in records if r.parse_ok) / len(records),
        zero_var=zero_variance_fraction(reward_groups),
        within_sd=within_instance_sd(reward_groups),
    )


def _claim_accuracy_table(claims: list[ClaimRollout]) -> list[str]:
    lines = [
        '| truth reason | claims | decision | line | reason | refund | all ok |',
        '|---|---|---|---|---|---|---|',
    ]
    for reason in REASONS:
        subset = [claim for claim in claims if claim.truth_reason == reason]
        if not subset:
            continue
        n = len(subset)
        rates = {
            key: sum(1 for c in subset if getattr(c, key)) / n
            for key in ('decision_ok', 'line_ok', 'reason_ok', 'refund_ok')
        }
        all_ok = (
            sum(1 for c in subset if c.decision_ok and c.line_ok and c.reason_ok and c.refund_ok)
            / n
        )
        lines.append(
            f'| {reason} | {n} | {rates["decision_ok"]:.0%} | {rates["line_ok"]:.0%} '
            f'| {rates["reason_ok"]:.0%} | {rates["refund_ok"]:.0%} | {all_ok:.0%} |'
        )
    return lines


def _confusion_table(records: list[Rollout]) -> list[str]:
    columns = [*REASONS, 'parse_fail']
    header = '| truth | ' + ' | '.join(columns) + ' |'
    lines = [header, '|' + '---|' * (len(columns) + 1)]
    for reason in REASONS:
        cells = []
        for column in columns:
            if column == 'parse_fail':
                count = sum(
                    1
                    for r in records
                    if not r.parse_ok and any(claim.truth_reason == reason for claim in r.claims)
                )
            else:
                count = sum(
                    1
                    for r in records
                    if r.parse_ok
                    for claim in r.claims
                    if claim.truth_reason == reason and claim.predicted_reason == column
                )
            cells.append(str(count))
        lines.append(f'| {reason} | ' + ' | '.join(cells) + ' |')
    return lines


def _stated_number_table(claims: list[ClaimRollout]) -> list[str]:
    lines = [
        '| slice | claims | claim fully correct | line ok |',
        '|---|---|---|---|',
    ]
    for label, subset in (
        ('stated-number=yes', [c for c in claims if c.stated_number]),
        ('stated-number=no', [c for c in claims if not c.stated_number]),
    ):
        if not subset:
            continue
        fully = sum(
            1 for c in subset if c.decision_ok and c.line_ok and c.reason_ok and c.refund_ok
        ) / len(subset)
        line_ok = sum(1 for c in subset if c.line_ok) / len(subset)
        lines.append(f'| {label} | {len(subset)} | {fully:.0%} | {line_ok:.0%} |')
    return lines


def _error_economics(records: list[Rollout]) -> list[str]:
    claims = [claim for record in records for claim in record.claims]
    dollar_errors = [claim.dollar_error_cents for claim in claims]
    return [
        f'- false approves: {sum(1 for c in claims if c.false_approve)} '
        f'({sum(1 for c in claims if c.false_approve) / len(claims):.1%} of claims)',
        f'- false rejects: {sum(1 for c in claims if c.false_reject)} '
        f'({sum(1 for c in claims if c.false_reject) / len(claims):.1%} of claims)',
        f'- mean |refund error|: {np.mean(dollar_errors) if dollar_errors else 0:.1f}c '
        f'over {len(claims)} claims',
        f'- parse failures: {sum(1 for r in records if not r.parse_ok)} '
        f'of {len(records)} rollouts',
    ]


def _claim_taxonomy(claims: list[ClaimRollout]) -> Counter:
    counts: Counter = Counter()
    for claim in claims:
        if claim.predicted_reason is None:
            counts['parse'] += 1
        elif (
            claim.truth_reason in PRECEDENCE_TIERS and claim.predicted_reason != claim.truth_reason
        ):
            counts['precedence'] += 1
        elif not claim.decision_ok:
            counts['wrong_decision'] += 1
        elif not claim.reason_ok:
            counts['wrong_reason'] += 1
        elif not claim.line_ok:
            counts['line_resolution'] += 1
        elif not claim.refund_ok:
            counts['arithmetic'] += 1
        else:
            counts['correct'] += 1
    return counts


def _examples(records: list[Rollout]) -> list[str]:
    """First occurrence of each failure class, plus one clean success."""
    claims_with_context = [(record, claim) for record in records for claim in record.claims]
    lines = []
    for label in ('precedence', 'wrong_decision', 'wrong_reason', 'line_resolution', 'arithmetic'):
        hit = next(
            (
                (record, claim)
                for record, claim in claims_with_context
                if dict(_claim_taxonomy([claim])).get(label)
            ),
            None,
        )
        if hit is None:
            continue
        record, claim = hit
        lines.append(
            f'- {label}: `{record.instance_id}` rollout {record.rollout_idx} '
            f'{claim.stated} claim on `{claim.truth_line}`: predicted '
            f'{claim.predicted_reason} on `{claim.predicted_line}`, '
            f'truth {claim.truth_reason}'
        )
    success = next((r for r in records if r.reward == 1.0), None)
    if success is not None:
        lines.append(f'- success: `{success.instance_id}` rollout {success.rollout_idx} (1.0)')
    return lines


def _rule_parser_compare(args: argparse.Namespace, deepest: list[Rollout]) -> list[str]:
    """Rule parser vs the model on the same instances, by reference kind (spec §10 row 2)."""
    cfg = RewardConfig()
    path = args.instances_dir / f'{args.split}_{args.levels[-1]}.jsonl'
    records = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    parser_ok = Counter()
    parser_total = Counter()
    for record in records:
        payload = record['instance']
        assert isinstance(payload, dict), 'record must carry an instance mapping'
        instance = record_to_instance(payload)
        answers = rule_parser_answers(prompt_view_of(instance))
        result = grade_parsed(answers, instance, cfg)
        for claim, score in zip(instance.claims, result.claim_scores, strict=True):
            parser_total[_kind_of(claim.truth_reason.value)] += 1
            parser_ok[_kind_of(claim.truth_reason.value)] += score.reason_ok and score.decision_ok
    model_ok = Counter()
    model_total = Counter()
    for record in deepest:
        for claim in record.claims:
            model_total[claim.kind] += 1
            model_ok[claim.kind] += claim.decision_ok and claim.reason_ok
    lines = [
        'The rule parser resolves references with its own curated word map, written before and',
        'independently of the LLM-written claim texts; the labels come from the writer/verifier',
        'pipeline and not from the map, so this is a fair non-LLM baseline. Map lineage (hand',
        'seed plus a two-model LLM harvest) is disclosed separately.',
        '',
        '| reference kind | rule parser decision+reason | model decision+reason | gap |',
        '|---|---|---|---|',
    ]
    slices = [
        (
            'unique',
            parser_total['unique'],
            parser_ok['unique'],
            model_total['unique'],
            model_ok['unique'],
        ),
        (
            'clarify',
            parser_total['clarify'],
            parser_ok['clarify'],
            model_total['clarify'],
            model_ok['clarify'],
        ),
        (
            'absent',
            parser_total['absent'],
            parser_ok['absent'],
            model_total['absent'],
            model_ok['absent'],
        ),
        (
            'all',
            sum(parser_total.values()),
            sum(parser_ok.values()),
            sum(model_total.values()),
            sum(model_ok.values()),
        ),
    ]
    for kind, p_total, p_ok, m_total, m_ok in slices:
        if not p_total:
            continue
        parser_rate = p_ok / p_total
        model_rate = m_ok / m_total if m_total else 0.0
        lines.append(
            f'| {kind} | {parser_rate:.0%} | {model_rate:.0%} | {model_rate - parser_rate:+.0%} |'
        )
    return lines


def _kind_of(reason: str) -> str:
    if reason == 'NOT_ON_RECEIPT':
        return 'absent'
    if reason == 'NEEDS_CLARIFICATION':
        return 'clarify'
    return 'unique'


def _decision_inputs(per_level: dict[str, list[Rollout]], deepest: list[Rollout]) -> list[str]:
    claims = [claim for record in deepest for claim in record.claims]
    taxonomy = _claim_taxonomy(claims)
    failures = sum(count for key, count in taxonomy.items() if key != 'correct')
    saturation = all(
        _instance_stats(records).reward_mean >= 0.95 for records in per_level.values()
    )
    high_zero_var = {
        level: _instance_stats(records).zero_var for level, records in per_level.items()
    }
    false_approves = sum(1 for claim in claims if claim.false_approve)
    false_rejects = sum(1 for claim in claims if claim.false_reject)
    rows = {
        'saturated (mean >= 0.95 at every level)': saturation,
        'failures dominated by line resolution / precedence': failures > 0
        and (taxonomy['line_resolution'] + taxonomy['precedence']) / failures >= 0.5,
        'failures dominated by refund arithmetic': failures > 0
        and taxonomy['arithmetic'] / failures >= 0.5,
        'false approvals dominate error modes': false_approves > false_rejects,
    }
    lines = [
        f'- failure mix: {dict(taxonomy)} over {len(claims)} claims ({failures} failures)',
        f'- zero-variance share per level: '
        f'{ {level: f"{share:.0%}" for level, share in high_zero_var.items()} }',
        f'- false approves {false_approves} vs false rejects {false_rejects}',
    ]
    lines += [
        f'- **{row}**: {"TRIGGERED" if hit else "not triggered"}' for row, hit in rows.items()
    ]
    return lines


def _pct(value: float | None) -> str:
    return '—' if value is None else f'{value:.0%}'


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Analyze saved refund rollouts of one split')
    parser.add_argument('--models', required=True, help='comma-separated OpenRouter model ids')
    parser.add_argument('--split', default='eval_unseen')
    parser.add_argument('--levels', default='L2')
    parser.add_argument('--temperature', type=float, default=1.0)
    parser.add_argument('--max-tokens', type=int, default=4096)
    parser.add_argument('--reasoning-effort', default='low')
    parser.add_argument('--rollouts-dir', type=Path, default=Path('rollouts/refund_v4'))
    parser.add_argument('--instances-dir', type=Path, default=Path('instances/refund_v4'))
    parser.add_argument('--report', type=Path, default=Path('reports/refund_eval_report_v4.md'))
    args = parser.parse_args()
    args.models = [m.strip() for m in args.models.split(',')]
    args.levels = [level.strip() for level in args.levels.split(',')]
    return args


if __name__ == '__main__':
    main()
