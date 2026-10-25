# Refund eval report — eval_unseen

Sampling params: `{'temperature': 1.0, 'max_tokens': 4096, 'reasoning_effort': 'low'}`

## openai/gpt-6-luna

| level | stratum | inst | mean reward [95% CI] | pass@1 | pass@4 | pass@8 | parse ok | zero-var | within sd |
|---|---|---|---|---|---|---|---|---|---|
| L1 | all | 10 | 1.000 [1.000, 1.000] | 100% | — | — | 100% | 100% | 0.000 |
| L1 | in_window | 9 | 1.000 [1.000, 1.000] | 100% | — | — | 100% | 100% | 0.000 |
| L1 | out_of_window | 1 | 1.000 [1.000, 1.000] | 100% | — | — | 100% | 100% | 0.000 |
| L2 | all | 10 | 1.000 [1.000, 1.000] | 100% | — | — | 100% | 100% | 0.000 |
| L2 | in_window | 9 | 1.000 [1.000, 1.000] | 100% | — | — | 100% | 100% | 0.000 |
| L2 | out_of_window | 1 | 1.000 [1.000, 1.000] | 100% | — | — | 100% | 100% | 0.000 |
| L3 | all | 10 | 0.996 [0.988, 1.000] | 95% | — | — | 100% | 90% | 0.006 |
| L3 | in_window | 9 | 0.995 [0.986, 1.000] | 94% | — | — | 100% | 89% | 0.007 |
| L3 | out_of_window | 1 | 1.000 [1.000, 1.000] | 100% | — | — | 100% | 100% | 0.000 |

## Claim-level (deepest level, every anchor exactly once)

| truth reason | claims | decision | line | reason | refund | all ok |
|---|---|---|---|---|---|---|
| OUTSIDE_WINDOW | 6 | 100% | 100% | 100% | 100% | 100% |
| NOT_ON_RECEIPT | 14 | 100% | 100% | 100% | 100% | 100% |
| PRICE_MATCH | 8 | 100% | 100% | 100% | 100% | 100% |
| WITHIN_TOLERANCE | 12 | 100% | 92% | 100% | 100% | 92% |
| MISSED_COUPON | 6 | 100% | 100% | 100% | 100% | 100% |
| NOT_ELIGIBLE | 12 | 100% | 100% | 100% | 100% | 100% |
| ALREADY_APPLIED | 2 | 100% | 100% | 100% | 100% | 100% |

### Reason confusion (rows truth, columns predicted)

| truth | OUTSIDE_WINDOW | NOT_ON_RECEIPT | PRICE_MATCH | WITHIN_TOLERANCE | MISSED_COUPON | NOT_ELIGIBLE | ALREADY_APPLIED | parse_fail |
|---|---|---|---|---|---|---|---|---|
| OUTSIDE_WINDOW | 6 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| NOT_ON_RECEIPT | 0 | 14 | 0 | 0 | 0 | 0 | 0 | 0 |
| PRICE_MATCH | 0 | 0 | 8 | 0 | 0 | 0 | 0 | 0 |
| WITHIN_TOLERANCE | 0 | 0 | 0 | 12 | 0 | 0 | 0 | 0 |
| MISSED_COUPON | 0 | 0 | 0 | 0 | 6 | 0 | 0 | 0 |
| NOT_ELIGIBLE | 0 | 0 | 0 | 0 | 0 | 12 | 0 | 0 |
| ALREADY_APPLIED | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 |

### Phrasing pool and reference style

| slice | claims | claim fully correct | line ok |
|---|---|---|---|
| pool=seen | 32 | 97% | 97% |
| pool=heldout | 28 | 100% | 100% |
| style=brand_tier | 2 | 100% | 100% |
| style=noun | 38 | 100% | 100% |
| style=null_item | 14 | 100% | 100% |
| style=size | 6 | 83% | 83% |

### Error economics

- false approves: 0 (0.0% of claims)
- false rejects: 0 (0.0% of claims)
- mean |refund error|: 0.0c over 60 claims
- parse failures: 0 of 20 rollouts

## Failure taxonomy (claims)

- {'correct': 59, 'line_resolution': 1}

## Examples

- line_resolution: `eval_unseen-L3-0033` rollout 1 price claim on `L02`: predicted WITHIN_TOLERANCE on `L21`, truth WITHIN_TOLERANCE
- success: `eval_unseen-L3-0059` rollout 1 (1.0)

## Decision inputs (spec §10)

| pool | rule parser decision+reason | model decision+reason | gap |
|---|---|---|---|
| seen | 100% | 100% | +0% |
| heldout | 100% | 100% | +0% |
- failure mix: {'correct': 59, 'line_resolution': 1} over 60 claims (1 failures)
- zero-variance share per level: {'L1': '100%', 'L2': '100%', 'L3': '90%'}
- false approves 0 vs false rejects 0
- **saturated (mean >= 0.95 at every level)**: TRIGGERED
- **failures dominated by line resolution / precedence**: TRIGGERED
- **failures dominated by refund arithmetic**: not triggered
- **false approvals dominate error modes**: not triggered
