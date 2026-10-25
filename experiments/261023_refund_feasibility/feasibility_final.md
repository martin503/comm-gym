# Refund-claim feasibility report

max receipt lines 40, min redemptions 2, seed 42, last day 711, ladder sample 2000 baskets/side (500 token-estimated), tokens = chars/4

## Per-side supply

| side | lines | baskets | lexicon | has ref | coup-cov | missed | applied | fit |
|---|---|---|---|---|---|---|---|---|
| train | 799424 | 79156 | 86.9% | 100.0% | 5.7% | 41045 (9422b) | 746 (459b) | 96.3% |
| dev | 191996 | 17796 | 86.6% | 100.0% | 5.6% | 9702 (2281b) | 165 (97b) | 95.9% |
| eval_known | 751468 | 72641 | 87.0% | 100.0% | 15.9% | 102352 (17952b) | 2235 (1133b) | 96.0% |
| eval_unseen | 188326 | 17668 | 86.5% | 100.0% | 15.8% | 25554 (4482b) | 473 (242b) | 95.8% |

## F1: overcharge share among price-eligible lines by tolerance

| side | 5c | 10c | 15c | 25c | 50c |
|---|---|---|---|---|---|
| train | 5.2% | 4.6% | 4.2% | 3.4% | 2.3% |
| dev | 5.1% | 4.5% | 4.1% | 3.4% | 2.3% |
| eval_known | 5.4% | 4.6% | 4.1% | 3.3% | 2.2% |
| eval_unseen | 5.7% | 4.9% | 4.4% | 3.6% | 2.4% |

Chosen tolerance (smallest grid value with share <= 45% on both eval sides): **5c** — frozen as the task `price_tolerance_cents`. Overcharge supply (lines/baskets): train 35785/20206; dev 8301/4792; eval_known 34557/19671; eval_unseen 9101/5040.

## F4: typical-value provenance of live covering coupons

- train: campaign 440 (82.2%), coupon 95 (17.8%)
- dev: campaign 314 (78.3%), coupon 87 (21.7%)
- eval_known: campaign 367 (69.4%), coupon 162 (30.6%)
- eval_unseen: campaign 302 (65.7%), coupon 158 (34.3%)

## F5/F6: reference ladder and prompt size (sampled baskets)

| side | resolvable | ready >= 3 | noun | tier | size | qty | unres. | tok mean | p95 |
|---|---|---|---|---|---|---|---|---|---|
| train | 75.7% | 59.4% | 8577 | 713 | 1634 | 501 | 3674 | 640 | 1224 |
| dev | 76.1% | 62.1% | 8720 | 688 | 1730 | 469 | 3644 | 619 | 1113 |
| eval_known | 76.6% | 61.3% | 8716 | 644 | 1672 | 468 | 3508 | 618 | 1144 |
| eval_unseen | 76.0% | 60.1% | 8315 | 697 | 1728 | 418 | 3531 | 610 | 1031 |

Note: QUANTITY is int32 in the raw data, so all lines carry unit counts; quantity-outlier (weight-priced) lines are dropped by cleaning.

## Selection effect: anchors = baskets with >= 3 resolvable targets

G5R (90% breadth) failed at ~60%; per the 2026-10-23 decision it is documented as a selection effect rather than a gate. Anchors are drawn from the selected pool only.

| side | pool | baskets | lines mean/med | missed/b | applied/b | cov | overcharge |
|---|---|---|---|---|---|---|---|
| train | all | 2000 | 8.8/5 | 0.42 | 0.01 | 5.4% | 5.1% |
| train | selected | 1188 | 13.2/10 | 0.64 | 0.02 | 5.5% | 5.2% |
| dev | all | 2000 | 8.8/6 | 0.44 | 0.01 | 5.6% | 5.0% |
| dev | selected | 1241 | 12.7/10 | 0.64 | 0.01 | 5.6% | 5.1% |
| eval_known | all | 2000 | 8.7/5 | 1.23 | 0.02 | 16.4% | 5.3% |
| eval_known | selected | 1226 | 12.7/10 | 1.86 | 0.03 | 16.7% | 5.5% |
| eval_unseen | all | 2000 | 8.5/5 | 1.12 | 0.01 | 15.4% | 5.8% |
| eval_unseen | selected | 1201 | 12.6/10 | 1.76 | 0.02 | 16.0% | 6.0% |

## Gates

- G1R overcharge supply at 5c: >= 500 lines in >= 250 baskets: PASS — eval_known: 34557/19671; eval_unseen: 9101/5040 (shares 5.4%; 5.7%)
- G2 missed-coupon lines >= 2000 in >= 800 baskets: PASS — eval_known: 102352/17952; eval_unseen: 25554/4482
- G3 already-applied lines >= 120 in >= 80 baskets: PASS — eval_known: 2235/1133; eval_unseen: 473/242
- G4 coupon-level >= 25% and coupon-or-campaign >= 60% of live covering coupons: PASS — eval_known: {'campaign': 367, 'coupon': 162}; eval_unseen: {'campaign': 302, 'coupon': 158}
- G6 basket fit >= 90%, mean tokens <= 2800, p95 <= 4200: PASS — eval_known: fit 96.0%, tok 618/1144; eval_unseen: fit 95.8%, tok 610/1031
- G7 lexicon covers >= 80% of lines, >= 85% of missed-coupon lines: PASS — eval_known: 87.0%/87.6%; eval_unseen: 86.5%/87.5%
