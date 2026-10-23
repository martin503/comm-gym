# Eval report — dev

Sampling params: `{'temperature': 1.0, 'max_tokens': 8192, 'reasoning_effort': 'low'}`

## openai/gpt-6-luna

| level | stratum | inst | mean reward [95% CI] | pass@1 | pass@4 | pass@8 | feasible | price ok | zero-var | within sd |
|---|---|---|---|---|---|---|---|---|---|---|
| L1 | all | 10 | 0.998 [0.995, 1.000] | 95% | — | — | 100% | 100% | 90% | 0.002 |
| L1 | trap | 7 | 0.998 [0.993, 1.000] | 93% | — | — | 100% | 100% | 86% | 0.003 |
| L1 | no_trap | 3 | 1.000 [1.000, 1.000] | 100% | — | — | 100% | 100% | 100% | 0.000 |
| L2 | all | 10 | 0.918 [0.829, 0.977] | 55% | — | — | 95% | 95% | 30% | 0.083 |
| L2 | trap | 5 | 0.867 [0.709, 0.971] | 50% | — | — | 90% | 90% | 20% | 0.146 |
| L2 | no_trap | 5 | 0.970 [0.937, 0.996] | 60% | — | — | 100% | 100% | 40% | 0.020 |
| L3 | all | 10 | 0.957 [0.914, 0.987] | 55% | — | — | 100% | 90% | 40% | 0.043 |
| L3 | trap | 4 | 0.970 [0.952, 0.989] | 62% | — | — | 100% | 88% | 25% | 0.036 |
| L3 | no_trap | 6 | 0.947 [0.883, 0.995] | 50% | — | — | 100% | 92% | 50% | 0.048 |
| L4 | all | 10 | 0.833 [0.625, 0.979] | 35% | — | — | 80% | 70% | 40% | 0.020 |
| L4 | trap | 4 | 0.622 [0.270, 0.974] | 25% | — | — | 50% | 50% | 75% | 0.011 |
| L4 | no_trap | 6 | 0.973 [0.952, 0.993] | 42% | — | — | 100% | 83% | 17% | 0.025 |

## Failure taxonomy

- **L1**: {'optimal': 19, 'suboptimal_feasible': 1}
- **L2**: {'optimal': 11, 'suboptimal_feasible': 8, 'infeasible:quota:National': 1}
- **L3**: {'optimal': 10, 'suboptimal_feasible': 8, 'arithmetic': 2}
- **L4**: {'optimal': 6, 'arithmetic': 2, 'suboptimal_feasible': 8, 'infeasible:quota:National': 4}

## Examples

**L1**
- suboptimal_feasible: instance `dev-L1-90` rollout 1 (reward 0.967, gap 11c, violations [])
- near-miss: instance `dev-L1-90` rollout 1 (reward 0.967, gap 11c, violations [])
- success: instance `dev-L1-103` rollout 0 (reward 1.000, gap 0c, violations [])
**L2**
- suboptimal_feasible: instance `dev-L2-112` rollout 1 (reward 0.921, gap 80c, violations [])
- near-miss: instance `dev-L2-112` rollout 1 (reward 0.921, gap 80c, violations [])
- success: instance `dev-L2-112` rollout 0 (reward 1.000, gap 0c, violations [])
**L3**
- suboptimal_feasible: instance `dev-L3-26` rollout 0 (reward 0.907, gap 114c, violations [])
- near-miss: instance `dev-L3-26` rollout 0 (reward 0.907, gap 114c, violations [])
- success: instance `dev-L3-261` rollout 0 (reward 1.000, gap 0c, violations [])
**L4**
- arithmetic: instance `dev-L4-1389` rollout 1 (reward 0.884, gap 31c, violations [])
- near-miss: instance `dev-L4-1389` rollout 1 (reward 0.884, gap 31c, violations [])
- success: instance `dev-L4-1389` rollout 0 (reward 1.000, gap 0c, violations [])
