# Replenishment feasibility report

granularity commodity, history 98d, horizon 7d, min purchases 2, min history trips 6, gate 30 candidates, 12 anchors/household, seed 42

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

## Due-vs-window curve by purchase-count stratum (F3 recheck)

| stratum | bin | P(bought) | pairs |
|---|---|---|---|
| 2 | lapsed (>1 gap overdue) | 12.6% | 13805 |
| 2 | overdue | 13.6% | 8740 |
| 2 | due in window (0-6) | 14.8% | 3951 |
| 2 | due 7-14 | 14.6% | 3957 |
| 2 | due later | 13.2% | 17751 |
| 3-4 | lapsed (>1 gap overdue) | 19.1% | 8120 |
| 3-4 | overdue | 23.5% | 8465 |
| 3-4 | due in window (0-6) | 26.5% | 4821 |
| 3-4 | due 7-14 | 24.9% | 6746 |
| 3-4 | due later | 19.4% | 13515 |
| 5+ | lapsed (>1 gap overdue) | 37.5% | 3871 |
| 5+ | overdue | 45.2% | 6220 |
| 5+ | due in window (0-6) | 54.8% | 8684 |
| 5+ | due 7-14 | 39.8% | 8891 |
| 5+ | due later | 27.7% | 2802 |

## Brier and skill on dev (F4, F5)

- pairs: 481723 train / 120339 dev, of which 45886 dev pairs have >=4 purchases
- constant 0.1825, weekly rate 0.1640, logistic regression 0.1625
- F5 weekly over constant: +0.1010 [+0.0949, +0.1070]
- F4 LR over weekly: +0.0096 [+0.0073, +0.0119]

## Pre-registered pass rule (>= 4 purchases)

- R1: P(buy | due in window) 50.1% vs P(buy | due after window) 32.0% -> ratio 1.56 (need >= 1.50)
- R2: LR over weekly on the stratum +0.0205 [+0.0165, +0.0245] (need >= +0.03, CI > 0)

## Gates

- R1 P(buy | due in window) >= 1.5x P(buy | due after window): PASS
- R2 LR skill over weekly >= +0.03 with CI > 0: FAIL
