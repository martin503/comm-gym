# Replenishment feasibility report

granularity sub_commodity, history 98d, horizon 7d, min purchases 2, min history trips 6, gate 30 candidates, 12 anchors/household, seed 42

## Day-level supply (F6, F7)

| side | hhs | qual. days | >=10 | >=20 | >=25 | >=30 | gate days | gate hhs | cond. |
|---|---|---|---|---|---|---|---|---|---|
| train | 1999 | 466309 | 79.2% | 58.9% | 50.8% | 43.9% | 204534 | 1047 | 18.2% |
| dev | 501 | 116282 | 80.2% | 60.8% | 51.9% | 44.4% | 51588 | 268 | 20.4% |
| eval_known | 1999 | 309401 | 80.3% | 61.0% | 52.9% | 45.8% | 141695 | 969 | 18.0% |
| eval_unseen | 501 | 77698 | 80.7% | 63.3% | 55.5% | 47.7% | 37027 | 264 | 20.9% |

## Pair-level on dev (F1, F2, F5, F8)

- pairs: 535839 train / 133249 dev
- F1 positive rate: 17.8% (target 10-60%)
- F2 near-deterministic share: 2.1% (target < 50%); staples 1.4%
- F8 zero-positive instances: 5.6%, all-positive: 0.0%; mean candidates 53.0, mean positives 9.4

## Due-date curve (F3), ratio clamped at 7-day intervals

| bin | P(bought) | pairs |
|---|---|---|
| <0.5 | 17.6% | 47515 |
| 0.5-1.0 | 21.6% | 27045 |
| 1.0-1.5 | 20.6% | 16213 |
| >=1.5 | 14.7% | 42476 |

## Brier and skill on dev (F4, F5)

- constant 0.1466, weekly rate 0.1342, logistic regression 0.1325
- F5 weekly over constant: +0.0847 [+0.0786, +0.0910]
- F4 LR over weekly: +0.0128 [+0.0100, +0.0156]

## Gates

- F1 positive rate 10-60%: PASS
- F2 near-deterministic < 50%: PASS
- F3 overdue >= 1.5x just-bought: FAIL
- F4 LR skill over weekly (CI > 0): PASS
- F5 weekly skill over constant: PASS
- F6 eval_unseen gate-day supply >= 100: PASS
