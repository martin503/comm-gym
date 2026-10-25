# Refund eval report — eval_unseen

Sampling params: `{'temperature': 1.0, 'max_tokens': 4096, 'reasoning_effort': 'low'}`

## Nested levels: measured, then dropped as a difficulty lever

L1-L3 claim prefixes were designed to ladder difficulty through cross-claim interactions (refund-cap truncation, same-line dedup, precedence). Measured mean reward by level never showed a usable gradient: v1 1.000/1.000/0.996, v2 0.950/0.975/0.979, v3 0.838/0.787/0.800, v4 dry-run 0.988/0.950/0.967 — flat or inverted at every sample size. Decision 2026-10-25: evaluate at L2 only. L1/L3 instances are still generated and retained; the level dimension is decoration, not a lever.

## openai/gpt-6-luna

| level | stratum | inst | mean reward [95% CI] | pass@1 | pass@4 | pass@8 | parse ok | zero-var | within sd |
|---|---|---|---|---|---|---|---|---|---|
| L2 | all | 100 | 0.990 [0.983, 0.996] | 97% | 100% | 100% | 100% | 85% | 0.018 |
| L2 | in_window | 89 | 0.989 [0.981, 0.996] | 97% | 100% | 100% | 100% | 83% | 0.020 |
| L2 | out_of_window | 11 | 1.000 [1.000, 1.000] | 100% | 100% | 100% | 100% | 100% | 0.000 |

## Claim-level (deepest level, every anchor exactly once)

| truth reason | claims | decision | line | reason | refund | all ok |
|---|---|---|---|---|---|---|
| OUTSIDE_WINDOW | 176 | 100% | 100% | 100% | 100% | 100% |
| NOT_ON_RECEIPT | 264 | 100% | 100% | 100% | 100% | 100% |
| NEEDS_CLARIFICATION | 176 | 100% | 100% | 100% | 100% | 100% |
| PRICE_MATCH | 360 | 98% | 100% | 98% | 96% | 96% |
| WITHIN_TOLERANCE | 240 | 100% | 100% | 100% | 100% | 100% |
| MISSED_COUPON | 200 | 98% | 100% | 98% | 96% | 96% |
| NOT_ELIGIBLE | 160 | 100% | 99% | 99% | 100% | 99% |
| ALREADY_APPLIED | 24 | 100% | 100% | 100% | 100% | 100% |

### Reason confusion (rows truth, columns predicted)

| truth | OUTSIDE_WINDOW | NOT_ON_RECEIPT | NEEDS_CLARIFICATION | PRICE_MATCH | WITHIN_TOLERANCE | MISSED_COUPON | NOT_ELIGIBLE | ALREADY_APPLIED | parse_fail |
|---|---|---|---|---|---|---|---|---|---|
| OUTSIDE_WINDOW | 176 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| NOT_ON_RECEIPT | 0 | 264 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| NEEDS_CLARIFICATION | 0 | 0 | 176 | 0 | 0 | 0 | 0 | 0 | 0 |
| PRICE_MATCH | 0 | 0 | 1 | 351 | 8 | 0 | 0 | 0 | 0 |
| WITHIN_TOLERANCE | 0 | 0 | 0 | 0 | 240 | 0 | 0 | 0 | 0 |
| MISSED_COUPON | 0 | 0 | 0 | 0 | 0 | 197 | 2 | 1 | 0 |
| NOT_ELIGIBLE | 0 | 0 | 1 | 0 | 0 | 0 | 159 | 0 | 0 |
| ALREADY_APPLIED | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 24 | 0 |

### Stated-number claims

| slice | claims | claim fully correct | line ok |
|---|---|---|---|
| stated-number=yes | 368 | 97% | 100% |
| stated-number=no | 1232 | 99% | 100% |

### Error economics

- false approves: 0 (0.0% of claims)
- false rejects: 12 (0.8% of claims)
- mean |refund error|: 1.1c over 1600 claims
- parse failures: 0 of 800 rollouts

## Failure taxonomy (claims)

- {'correct': 1577, 'wrong_decision': 12, 'arithmetic': 10, 'wrong_reason': 1}

## Examples

- wrong_decision: `eval_unseen-L2-0001` rollout 1 price claim on `L06`: predicted WITHIN_TOLERANCE on `L06`, truth PRICE_MATCH
- wrong_reason: `eval_unseen-L2-0077` rollout 0 coupon claim on `L09`: predicted NEEDS_CLARIFICATION on `None`, truth NOT_ELIGIBLE
- arithmetic: `eval_unseen-L2-0002` rollout 4 coupon claim on `L12`: predicted MISSED_COUPON on `L12`, truth MISSED_COUPON
- success: `eval_unseen-L2-0000` rollout 1 (1.0)

## Decision inputs (spec §10)

The rule parser resolves references with its own curated word map, written before and
independently of the LLM-written claim texts; the labels come from the writer/verifier
pipeline and not from the map, so this is a fair non-LLM baseline. Map lineage (hand
seed plus a two-model LLM harvest) is disclosed separately.

| reference kind | rule parser decision+reason | model decision+reason | gap |
|---|---|---|---|
| unique | 57% | 99% | +42% |
| clarify | 77% | 100% | +23% |
| absent | 97% | 100% | +3% |
| all | 66% | 99% | +33% |
- failure mix: {'correct': 1577, 'wrong_decision': 12, 'arithmetic': 10, 'wrong_reason': 1} over 1600 claims (23 failures)
- zero-variance share per level: {'L2': '85%'}
- false approves 0 vs false rejects 12
- **saturated (mean >= 0.95 at every level)**: TRIGGERED
- **failures dominated by line resolution / precedence**: not triggered
- **failures dominated by refund arithmetic**: not triggered
- **false approvals dominate error modes**: not triggered
