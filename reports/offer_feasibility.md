# Offer Task Feasibility

- generated: 2026-10-23T21:24:10

## F1 instance supply — GO

| split | threshold | households | (hh, day) pairs | anchor supply (gap+cap) |
|---|---|---|---|---|
| train | 5 | 1038 | 84987 | 3100 |
| train | 10 | 1033 | 83181 | 3079 |
| train | 20 | 994 | 73321 | 2979 |
| dev | 5 | 268 | 21378 | 800 |
| dev | 10 | 263 | 20735 | 785 |
| dev | 20 | 255 | 18303 | 765 |
| eval_unseen | 5 | 290 | 33735 | 870 |
| eval_unseen | 10 | 290 | 33735 | 870 |
| eval_unseen | 20 | 285 | 29256 | 853 |
| eval_known | 5 | 1111 | 130224 | 3332 |
| eval_known | 10 | 1111 | 130224 | 3332 |
| eval_known | 20 | 1079 | 111892 | 3232 |

## F2 coupon breadth — REPORT

- coupons: 1397
- commodities per coupon: median 1, p90 2, max 86
- products per coupon: median 13, p90 75, max 14477

## F3 affinity spread — GO

| split | anchors | median relevant share | within 20-80% |
|---|---|---|---|
| train | 100 | 49.0% | yes |
| dev | 100 | 48.3% | yes |
| eval_unseen | 100 | 45.0% | yes |
| eval_known | 100 | 46.9% | yes |

## F4 redemption signal — REPORT

| split | anchors | with later redemption | share |
|---|---|---|---|
| train | 100 | 14 | 14.0% |
| dev | 100 | 9 | 9.0% |
| eval_unseen | 100 | 11 | 11.0% |
| eval_known | 100 | 11 | 11.0% |

mean 11.2%; dense enough for the metric

## F5 brand-tier mix — REPORT

coupon tiers: National 1103 (79%), Private 284 (20%), Mixed 10 (1%)
- train: 100/100 anchors with a non-Mixed live coupon
- dev: 100/100 anchors with a non-Mixed live coupon
- eval_unseen: 100/100 anchors with a non-Mixed live coupon
- eval_known: 100/100 anchors with a non-Mixed live coupon

## F6 lexicon collisions — REPORT

- coupon-eligible commodities: 266
- keywords: 770, collision rate 15.8%
- synonym phrases: 5, unmatched targets: 0

## F8 gate feature availability — REPORT

| split | anchors | with ends-soon coupon |
|---|---|---|
| train | 100 | 21 |
| dev | 100 | 19 |
| eval_unseen | 100 | 22 |
| eval_known | 100 | 21 |
