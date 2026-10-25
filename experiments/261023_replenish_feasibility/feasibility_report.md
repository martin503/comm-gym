# Replenishment feasibility report

history 98d, horizon 7d, min purchases 2, min history trips 6, gate 30 candidates, 12 anchors/household, seed 42

## Day-level supply (F6, F7)

| side | hhs | qual. days | >=10 | >=20 | >=25 | >=30 | gate days | gate hhs | cond. |
|---|---|---|---|---|---|---|---|---|---|
| train | 1999 | 466309 | 83.2% | 62.3% | 53.3% | 45.0% | 209723 | 1048 | 18.9% |
| dev | 501 | 116282 | 84.6% | 64.8% | 54.8% | 45.5% | 52867 | 280 | 21.1% |
| eval_known | 1999 | 309401 | 84.2% | 64.1% | 55.1% | 46.8% | 144786 | 983 | 18.6% |
| eval_unseen | 501 | 77698 | 84.3% | 66.6% | 58.0% | 49.1% | 38171 | 267 | 21.1% |

## Pair-level on dev (F1, F2, F5, F8)

- pairs: 481723 train / 120339 dev
- F1 positive rate: 24.0% (target 10-60%)
- F2 near-deterministic share: 1.8% (target < 50%); staples 2.6%
- F8 zero-positive instances: 3.1%, all-positive: 0.0%; mean candidates 47.0, mean positives 11.3

## Due-date curve (F3), ratio clamped at 7-day intervals

| bin | P(bought) | pairs |
|---|---|---|
| <0.5 | 23.7% | 44335 |
| 0.5-1.0 | 28.5% | 25601 |
| 1.0-1.5 | 26.7% | 15021 |
| >=1.5 | 20.0% | 35382 |

## Brier and skill on dev (F4, F5)

- constant 0.1825, weekly rate 0.1640, logistic regression 0.1625
- F5 weekly over constant: +0.1010 [+0.0949, +0.1070]
- F4 LR over weekly: +0.0096 [+0.0073, +0.0119]

## Gates

- F1 positive rate 10-60%: PASS
- F2 near-deterministic < 50%: PASS
- F3 overdue >= 1.5x just-bought: FAIL
- F4 LR skill over weekly (CI > 0): PASS
- F5 weekly skill over constant: PASS
- F6 eval_unseen gate-day supply >= 100: PASS
