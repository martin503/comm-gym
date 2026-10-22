# Data Checks — Dunnhumby Complete Journey

- generated: 2026-10-22T18:09:30
- data dir: `/Users/marcin.mazur/repos/comm-gym/data`

## Schema and ranges

| metric | value | expected |
|---|---|---|
| rows | 2595732 | — |
| households | 2500 | 2500 |
| baskets | 276484 | — |
| DAY range | 1–711 | 1–711 |
| WEEK_NO range | 1–102 | 1–102 |
| stores | 582 | — |

**Verdict: ✅ GO**

## Discount signs and price derivation

| metric | value | expected |
|---|---|---|
| share regular ≥ loyalty > 0 | 99.9999% | ≥ 99% |
| median regular unit price | $2.25 | — |
| median loyalty unit price | $1.99 | — |
| share of lines with loyalty discount | 50.20% | — |

**Verdict: ✅ GO**

## Exclusions

| rule | rows dropped |
|---|---|
| unknown_product | 0 |
| nonpositive_quantity | 14466 |
| nonpositive_sales_value | 4451 |
| excluded_department | 22429 |
| excluded_commodity | 2288 |
| quantity_outlier | 4008 |
| **kept** | 2548090 |
| kept share | 98.16% |

**Verdict: — report-only**

## Price coverage

| metric | value | expected |
|---|---|---|
| commodity-week pairs observed | 27159 | — |
| pairs with ≥ 4 priced SKUs (chain) | 84.45% | ≥ 50% |
| median priced SKUs per pair | 19.0 | — |
| store-commodity-week pairs with ≥ 4 SKUs | 18.81% | feeds store- vs chain-level pricing decision |
| commodities ever reaching the minimum | 276 | — |

**Verdict: ✅ GO**

## Within-category price spread

| metric | value | expected |
|---|---|---|
| median within-pair CV of unit price | 0.4779 | ≥ 0.05 |
| p90 within-pair CV | 0.8655 | — |
| commodities with both tiers priced | 220 | — |
| median National vs Private premium | 36.61% | — |
| share of commodities where National is pricier | 72.73% | — |

**Verdict: ✅ GO**

## Menu scope: commodity vs sub-commodity

| metric | commodity scope | sub-commodity scope |
|---|---|---|
| pairs observed | 27159 | 134153 |
| share of pairs with ≥ 4 priced SKUs | 84.45% | 50.07% |
| median priced SKUs per pair | 19.0 | 4.0 |
| share of lines in a feasible group | 99.48% | 89.03% |
| share of baskets with ≥ 4 feasible categories | 56.41% | 52.52% |
| share of baskets with ≥ 8 feasible categories | 32.59% | 28.89% |
| median within-pair price CV | 0.4779 | 0.3023 |
| p90 within-pair price CV | 0.8655 | 0.6440 |
| groups with both tiers priced | 220 | 899 |
| median National vs Private premium | 36.61% | 33.52% |

**Verdict: — report-only**

## Coupon coverage over time

| metric | value | expected |
|---|---|---|
| first campaign week | 32 | — |
| last campaign week | 103 | — |
| commodities with any live coupon eligibility | 266 | — |
| window weeks with ≥ 1 live campaign | 71 | — |
| mean share of eligible commodities covered per window week | 43.82% | — |
| median eligible commodities per week, early (≤ w68) | 90 | — |
| median eligible commodities per week, late (> w68) | 157 | — |

**Verdict: — report-only**

## Empirical coupon amounts

| metric | value | expected |
|---|---|---|
| lines with COUPON_DISC | 36422 | ≥ 1000 |
| lines with COUPON_MATCH_DISC | 17449 | — |
| COUPON_DISC q0.05 | $0.30 | — |
| COUPON_DISC q0.25 | $0.50 | — |
| COUPON_DISC q0.50 | $1.00 | — |
| COUPON_DISC q0.75 | $1.00 | — |
| COUPON_DISC q0.95 | $3.00 | — |

**Verdict: ✅ GO**

## Household brand-tier share

| metric | value | expected |
|---|---|---|
| private share mean (all weeks) | 0.284 | — |
| private share std across households (all weeks) | 0.108 | — |
| private share p10 / p90 (all weeks) | 0.150 / 0.432 | — |
| households with zero private lines (all weeks) | 0.20% | — |
| private share mean (weeks ≤ 52 (early period)) | 0.281 | — |
| private share std across households (weeks ≤ 52 (early period)) | 0.119 | — |
| private share p10 / p90 (weeks ≤ 52 (early period)) | 0.138 / 0.432 | — |
| households with zero private lines (weeks ≤ 52 (early period)) | 1.16% | — |

**Verdict: — report-only**

## Basket category counts

| metric | value | expected |
|---|---|---|
| baskets | 251462 | — |
| median commodities per basket | 4.0 | — |
| p90 commodities per basket | 19.0 | — |
| share of baskets with ≥ 4 commodities | 56.69% | ≥ 5% at C=8 |
| share of baskets with ≥ 5 commodities | 48.63% | ≥ 5% at C=8 |
| share of baskets with ≥ 6 commodities | 42.35% | ≥ 5% at C=8 |
| share of baskets with ≥ 8 commodities | 32.78% | ≥ 5% at C=8 |

**Verdict: ✅ GO**

## Entry ramp and campaign-window cutoff

| metric | value | expected |
|---|---|---|
| max active households in a week | 1428 | — |
| first week at steady state | 15 | — |
| campaign window start week | 32 | — |
| suggested cutoff week (window midpoint) | 68 | — |
| window weeks early/late at cutoff 68 | 37 / 34 | — |

**Verdict: ✅ GO**

## Held-out commodity feasibility

| metric | value | expected |
|---|---|---|
| eligible commodities (≥ min SKUs in ≥ 10 weeks) | 261 | — |
| held-out commodities | 52 | — |
| share of baskets with ≥ 1 held-out commodity | 53.96% | — |
| share of baskets with ≥ C=8 held-out (all-held-out rule) | 1.18% | — |
| median held-out commodities per basket | 1.0 | — |

**Verdict: — report-only**

## Split balance (campaign window only)

| metric | early (w32–68) | late (w69–102) |
|---|---|---|
| weeks in split | 37 | 34 |
| baskets | 99976 | 90309 |
| households | 2429 | 2450 |
| lines | 1019566 | 939794 |
| median commodities/basket | 4.0 | 4.0 |
| median basket spend | 15.98 | 16.55 |
| private line share | 0.282 | 0.284 |
| coupon line share | 0.0126 | 0.0134 |
| distinct commodities | 299 | 300 |

**Verdict: — report-only**
