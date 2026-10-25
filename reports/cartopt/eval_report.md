# Eval report — eval_unseen

## openai/gpt-6-luna

Sampling params: `{'temperature': 1.0, 'max_tokens': 8192, 'reasoning_effort': 'low'}`

| level | stratum | inst | mean reward [95% CI] | pass@1 | pass@4 | pass@8 | feasible | price ok | zero-var | within sd |
|---|---|---|---|---|---|---|---|---|---|---|
| L1 | all | 100 | 0.996 [0.994, 0.998] | 97% | 100% | 100% | 100% | 98% | 77% | 0.008 |
| L1 | trap | 70 | 0.996 [0.994, 0.998] | 97% | 100% | 100% | 100% | 98% | 80% | 0.007 |
| L1 | no_trap | 30 | 0.996 [0.992, 0.998] | 98% | 100% | 100% | 100% | 99% | 70% | 0.012 |
| L2 | all | 100 | 0.943 [0.929, 0.955] | 69% | 97% | 100% | 97% | 90% | 7% | 0.093 |
| L2 | trap | 70 | 0.937 [0.920, 0.952] | 69% | 97% | 100% | 96% | 89% | 7% | 0.103 |
| L2 | no_trap | 30 | 0.955 [0.936, 0.971] | 68% | 97% | 100% | 99% | 93% | 7% | 0.069 |
| L3 | all | 100 | 0.945 [0.934, 0.955] | 64% | 95% | 98% | 97% | 87% | 7% | 0.089 |
| L3 | trap | 70 | 0.937 [0.923, 0.950] | 63% | 94% | 97% | 96% | 84% | 6% | 0.104 |
| L3 | no_trap | 30 | 0.965 [0.952, 0.976] | 66% | 98% | 100% | 100% | 92% | 10% | 0.056 |
| L4 | all | 100 | 0.915 [0.898, 0.930] | 47% | 80% | 86% | 94% | 78% | 3% | 0.123 |
| L4 | trap | 70 | 0.891 [0.871, 0.910] | 38% | 72% | 80% | 91% | 72% | 1% | 0.155 |
| L4 | no_trap | 30 | 0.970 [0.956, 0.982] | 68% | 98% | 100% | 100% | 90% | 7% | 0.049 |

## Failure taxonomy

- **L1**: {'optimal': 764, 'suboptimal_feasible': 24, 'arithmetic': 12}
- **L2**: {'optimal': 520, 'suboptimal_feasible': 201, 'arithmetic': 55, 'infeasible:quota:National': 22, 'infeasible:quota:Private': 2}
- **L3**: {'optimal': 469, 'arithmetic': 84, 'suboptimal_feasible': 225, 'infeasible:quota:National': 22}
- **L4**: {'arithmetic': 130, 'suboptimal_feasible': 301, 'infeasible:quota:National': 50, 'optimal': 319}

## Examples

**L1**
- suboptimal_feasible: instance `eval_unseen-L1-3` rollout 2 (reward 0.808, gap 150c, violations [])
- near-miss: instance `eval_unseen-L1-11` rollout 0 (reward 0.900, gap 70c, violations [])
- success: instance `eval_unseen-L1-2` rollout 2 (reward 1.000, gap 0c, violations [])
**L2**
- suboptimal_feasible: instance `eval_unseen-L2-0` rollout 2 (reward 0.926, gap 50c, violations [])
- near-miss: instance `eval_unseen-L2-0` rollout 2 (reward 0.926, gap 50c, violations [])
- success: instance `eval_unseen-L2-0` rollout 1 (reward 1.000, gap 0c, violations [])
**L3**
- arithmetic: instance `eval_unseen-L3-0` rollout 2 (reward 0.848, gap 61c, violations [])
- near-miss: instance `eval_unseen-L3-0` rollout 2 (reward 0.848, gap 61c, violations [])
- success: instance `eval_unseen-L3-0` rollout 1 (reward 1.000, gap 0c, violations [])
**L4**
- arithmetic: instance `eval_unseen-L4-0` rollout 3 (reward 0.844, gap 158c, violations [])
- near-miss: instance `eval_unseen-L4-0` rollout 3 (reward 0.844, gap 158c, violations [])
- success: instance `eval_unseen-L4-3` rollout 2 (reward 1.000, gap 0c, violations [])
## qwen/qwen3.8-27b

Sampling params: `{'temperature': 1.0, 'max_tokens': 8192, 'reasoning_effort': 'low'}`

| level | stratum | inst | mean reward [95% CI] | pass@1 | pass@4 | pass@8 | feasible | price ok | zero-var | within sd |
|---|---|---|---|---|---|---|---|---|---|---|
| L1 | all | 10 | 1.000 [1.000, 1.000] | 100% | 100% | 100% | 100% | 100% | 100% | 0.000 |
| L1 | trap | 9 | 1.000 [1.000, 1.000] | 100% | 100% | 100% | 100% | 100% | 100% | 0.000 |
| L1 | no_trap | 1 | 1.000 [1.000, 1.000] | 100% | 100% | 100% | 100% | 100% | 100% | 0.000 |
| L2 | all | 10 | 0.852 [0.718, 0.959] | 71% | 88% | 90% | 88% | 82% | 50% | 0.144 |
| L2 | trap | 7 | 0.937 [0.847, 1.000] | 84% | 86% | 86% | 96% | 93% | 71% | 0.079 |
| L2 | no_trap | 3 | 0.653 [0.366, 0.836] | 42% | 92% | 100% | 67% | 58% | 0% | 0.294 |

## Failure taxonomy

- **L1**: {'optimal': 80}
- **L2**: {'optimal': 56, 'arithmetic': 4, 'suboptimal_feasible': 10, 'infeasible:missing:CHRISTMAS  SEASONAL': 6, 'parse:no_answer_block': 1, 'infeasible:quota:National': 3}

## Examples

**L1**
- success: instance `eval_unseen-L1-28` rollout 1 (reward 1.000, gap 0c, violations [])
**L2**
- arithmetic: instance `eval_unseen-L2-70` rollout 1 (reward 0.740, gap 82c, violations [])
- near-miss: instance `eval_unseen-L2-43` rollout 3 (reward 0.803, gap 80c, violations [])
- success: instance `eval_unseen-L2-83` rollout 0 (reward 1.000, gap 0c, violations [])
