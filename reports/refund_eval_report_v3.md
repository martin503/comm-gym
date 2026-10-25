# Refund eval report — eval_unseen

Sampling params: `{'temperature': 1.0, 'max_tokens': 4096, 'reasoning_effort': 'low'}`

## openai/gpt-6-luna

| level | stratum | inst | mean reward [95% CI] | pass@1 | pass@4 | pass@8 | parse ok | zero-var | within sd |
|---|---|---|---|---|---|---|---|---|---|
| L1 | all | 10 | 0.838 [0.662, 1.000] | 75% | — | — | 100% | 80% | 0.088 |
| L1 | in_window | 9 | 0.819 [0.625, 1.000] | 72% | — | — | 100% | 78% | 0.098 |
| L1 | out_of_window | 1 | 1.000 [1.000, 1.000] | 100% | — | — | 100% | 100% | 0.000 |
| L2 | all | 10 | 0.787 [0.675, 0.887] | 20% | — | — | 100% | 100% | 0.000 |
| L2 | in_window | 9 | 0.778 [0.653, 0.889] | 22% | — | — | 100% | 100% | 0.000 |
| L2 | out_of_window | 1 | 0.875 [0.875, 0.875] | 0% | — | — | 100% | 100% | 0.000 |
| L3 | all | 10 | 0.800 [0.725, 0.883] | 20% | — | — | 100% | 90% | 0.012 |
| L3 | in_window | 9 | 0.796 [0.713, 0.889] | 22% | — | — | 100% | 89% | 0.013 |
| L3 | out_of_window | 1 | 0.833 [0.833, 0.833] | 0% | — | — | 100% | 100% | 0.000 |

## Claim-level (deepest level, every anchor exactly once)

| truth reason | claims | decision | line | reason | refund | all ok |
|---|---|---|---|---|---|---|
| OUTSIDE_WINDOW | 6 | 100% | 33% | 100% | 100% | 33% |
| NOT_ON_RECEIPT | 12 | 100% | 83% | 67% | 100% | 67% |
| NEEDS_CLARIFICATION | 10 | 100% | 100% | 80% | 100% | 80% |
| PRICE_MATCH | 10 | 60% | 60% | 60% | 80% | 60% |
| WITHIN_TOLERANCE | 8 | 100% | 50% | 88% | 100% | 50% |
| MISSED_COUPON | 4 | 100% | 100% | 100% | 100% | 100% |
| NOT_ELIGIBLE | 10 | 100% | 60% | 80% | 100% | 60% |

### Reason confusion (rows truth, columns predicted)

| truth | OUTSIDE_WINDOW | NOT_ON_RECEIPT | NEEDS_CLARIFICATION | PRICE_MATCH | WITHIN_TOLERANCE | MISSED_COUPON | NOT_ELIGIBLE | ALREADY_APPLIED | parse_fail |
|---|---|---|---|---|---|---|---|---|---|
| OUTSIDE_WINDOW | 6 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| NOT_ON_RECEIPT | 0 | 8 | 2 | 0 | 0 | 0 | 2 | 0 | 0 |
| NEEDS_CLARIFICATION | 0 | 2 | 8 | 0 | 0 | 0 | 0 | 0 | 0 |
| PRICE_MATCH | 0 | 0 | 2 | 6 | 2 | 0 | 0 | 0 | 0 |
| WITHIN_TOLERANCE | 0 | 1 | 0 | 0 | 7 | 0 | 0 | 0 | 0 |
| MISSED_COUPON | 0 | 0 | 0 | 0 | 0 | 4 | 0 | 0 | 0 |
| NOT_ELIGIBLE | 0 | 2 | 0 | 0 | 0 | 0 | 8 | 0 | 0 |
| ALREADY_APPLIED | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

### Phrasing pool and reference style

| slice | claims | claim fully correct | line ok |
|---|---|---|---|
| pool=seen | 28 | 50% | 64% |
| pool=heldout | 32 | 75% | 75% |
| style=ambiguous | 10 | 80% | 100% |
| style=brand_tier | 6 | 67% | 67% |
| style=null_item | 12 | 67% | 83% |
| style=size | 6 | 0% | 0% |
| style=word | 26 | 69% | 69% |
| stated-number=yes | 8 | 100% | 100% |
| stated-number=no | 52 | 58% | 65% |

### Error economics

- false approves: 0 (0.0% of claims)
- false rejects: 4 (6.7% of claims)
- mean |refund error|: 1.7c over 60 claims
- parse failures: 0 of 20 rollouts

## Failure taxonomy (claims)

- {'wrong_reason': 5, 'correct': 38, 'wrong_decision': 4, 'precedence': 4, 'line_resolution': 9}

## Examples

- precedence: `eval_unseen-L3-0056` rollout 1 missing_item claim on `None`: predicted NEEDS_CLARIFICATION on `None`, truth NOT_ON_RECEIPT
- wrong_decision: `eval_unseen-L3-0021` rollout 1 price claim on `L19`: predicted WITHIN_TOLERANCE on `L09`, truth PRICE_MATCH
- wrong_reason: `eval_unseen-L3-0059` rollout 1 coupon claim on `L04`: predicted NOT_ON_RECEIPT on `None`, truth NOT_ELIGIBLE
- line_resolution: `eval_unseen-L3-0042` rollout 1 price claim on `L07`: predicted WITHIN_TOLERANCE on `L03`, truth WITHIN_TOLERANCE
- success: `eval_unseen-L3-0033` rollout 1 (1.0)

## Decision inputs (spec §10)

| pool | rule parser decision+reason | model decision+reason | gap |
|---|---|---|---|
| seen | 99% | 64% | -35% |
| heldout | 99% | 91% | -8% |
- failure mix: {'wrong_reason': 5, 'correct': 38, 'wrong_decision': 4, 'precedence': 4, 'line_resolution': 9} over 60 claims (22 failures)
- zero-variance share per level: {'L1': '80%', 'L2': '100%', 'L3': '90%'}
- false approves 0 vs false rejects 4
- **saturated (mean >= 0.95 at every level)**: not triggered
- **failures dominated by line resolution / precedence**: TRIGGERED
- **failures dominated by refund arithmetic**: not triggered
- **false approvals dominate error modes**: not triggered
