# Refund eval report — eval_unseen

Sampling params: `{'temperature': 1.0, 'max_tokens': 4096, 'reasoning_effort': 'low'}`

## openai/gpt-6-luna

| level | stratum | inst | mean reward [95% CI] | pass@1 | pass@4 | pass@8 | parse ok | zero-var | within sd |
|---|---|---|---|---|---|---|---|---|---|
| L1 | all | 10 | 0.950 [0.850, 1.000] | 95% | — | — | 100% | 90% | 0.071 |
| L1 | in_window | 9 | 0.944 [0.833, 1.000] | 94% | — | — | 100% | 89% | 0.079 |
| L1 | out_of_window | 1 | 1.000 [1.000, 1.000] | 100% | — | — | 100% | 100% | 0.000 |
| L2 | all | 10 | 0.975 [0.925, 1.000] | 95% | — | — | 100% | 90% | 0.035 |
| L2 | in_window | 9 | 0.972 [0.917, 1.000] | 94% | — | — | 100% | 89% | 0.039 |
| L2 | out_of_window | 1 | 1.000 [1.000, 1.000] | 100% | — | — | 100% | 100% | 0.000 |
| L3 | all | 10 | 0.979 [0.937, 1.000] | 90% | — | — | 100% | 90% | 0.018 |
| L3 | in_window | 9 | 0.977 [0.931, 1.000] | 89% | — | — | 100% | 89% | 0.020 |
| L3 | out_of_window | 1 | 1.000 [1.000, 1.000] | 100% | — | — | 100% | 100% | 0.000 |

## Claim-level (deepest level, every anchor exactly once)

| truth reason | claims | decision | line | reason | refund | all ok |
|---|---|---|---|---|---|---|
| OUTSIDE_WINDOW | 6 | 100% | 100% | 100% | 100% | 100% |
| NOT_ON_RECEIPT | 10 | 90% | 80% | 100% | 90% | 80% |
| PRICE_MATCH | 10 | 100% | 100% | 100% | 100% | 100% |
| WITHIN_TOLERANCE | 12 | 100% | 100% | 100% | 100% | 100% |
| MISSED_COUPON | 8 | 100% | 100% | 100% | 100% | 100% |
| NOT_ELIGIBLE | 10 | 100% | 100% | 100% | 100% | 100% |
| ALREADY_APPLIED | 4 | 100% | 100% | 100% | 100% | 100% |

### Reason confusion (rows truth, columns predicted)

| truth | OUTSIDE_WINDOW | NOT_ON_RECEIPT | PRICE_MATCH | WITHIN_TOLERANCE | MISSED_COUPON | NOT_ELIGIBLE | ALREADY_APPLIED | parse_fail |
|---|---|---|---|---|---|---|---|---|
| OUTSIDE_WINDOW | 6 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| NOT_ON_RECEIPT | 0 | 10 | 0 | 0 | 0 | 0 | 0 | 0 |
| PRICE_MATCH | 0 | 0 | 10 | 0 | 0 | 0 | 0 | 0 |
| WITHIN_TOLERANCE | 0 | 0 | 0 | 12 | 0 | 0 | 0 | 0 |
| MISSED_COUPON | 0 | 0 | 0 | 0 | 8 | 0 | 0 | 0 |
| NOT_ELIGIBLE | 0 | 0 | 0 | 0 | 0 | 10 | 0 | 0 |
| ALREADY_APPLIED | 0 | 0 | 0 | 0 | 0 | 0 | 4 | 0 |

### Phrasing pool and reference style

| slice | claims | claim fully correct | line ok |
|---|---|---|---|
| pool=seen | 26 | 92% | 92% |
| pool=heldout | 34 | 100% | 100% |
| style=brand_tier | 6 | 100% | 100% |
| style=noun | 40 | 100% | 100% |
| style=null_item | 10 | 80% | 80% |
| style=size | 4 | 100% | 100% |
| stated-number=yes | 14 | 100% | 100% |
| stated-number=no | 46 | 96% | 96% |

### Error economics

- false approves: 1 (1.7% of claims)
- false rejects: 0 (0.0% of claims)
- mean |refund error|: 0.8c over 60 claims
- parse failures: 0 of 20 rollouts

## Failure taxonomy (claims)

- {'correct': 58, 'wrong_decision': 1, 'line_resolution': 1}

## Examples

- wrong_decision: `eval_unseen-L3-0027` rollout 1 missing_item claim on `None`: predicted NOT_ON_RECEIPT on `L23`, truth NOT_ON_RECEIPT
- line_resolution: `eval_unseen-L3-0027` rollout 0 missing_item claim on `None`: predicted NOT_ON_RECEIPT on `L23`, truth NOT_ON_RECEIPT
- success: `eval_unseen-L3-0059` rollout 1 (1.0)

## Decision inputs (spec §10)

| pool | rule parser decision+reason | model decision+reason | gap |
|---|---|---|---|
| seen | 99% | 96% | -3% |
| heldout | 99% | 100% | +1% |
- failure mix: {'correct': 58, 'wrong_decision': 1, 'line_resolution': 1} over 60 claims (2 failures)
- zero-variance share per level: {'L1': '90%', 'L2': '90%', 'L3': '90%'}
- false approves 1 vs false rejects 0
- **saturated (mean >= 0.95 at every level)**: TRIGGERED
- **failures dominated by line resolution / precedence**: TRIGGERED
- **failures dominated by refund arithmetic**: not triggered
- **false approvals dominate error modes**: TRIGGERED
