# Baselines — dev

| level | baseline | mean reward | reward (traps) | feasible | exact-opt | mean overpay |
|---|---|---|---|---|---|---|
| L1 | always_coupon_sku | 0.918 | 0.954 | 100% | 47% | 0.71 |
| L1 | always_lowest_shelf | 0.909 | 0.874 | 100% | 30% | 0.65 |
| L1 | always_private | 0.862 | 0.851 | 100% | 10% | 1.15 |
| L1 | constraint_aware_greedy | 0.939 | 0.914 | 100% | 30% | 0.45 |
| L1 | greedy_cheapest | 0.939 | 0.914 | 100% | 30% | 0.45 |
| L1 | greedy_max_discount | 0.702 | 0.686 | 100% | 0% | 3.92 |
| L1 | oracle | 1.000 | 1.000 | 100% | 100% | 0.00 |
| L1 | random | 0.671 | 0.666 | 100% | 3% | 4.77 |
| L1 | real_shopper | 0.677 | 0.657 | 100% | 0% | 3.47 |
| L2 | always_coupon_sku | 0.533 | 0.390 | 40% | 23% | 0.92 |
| L2 | always_lowest_shelf | 0.510 | 0.344 | 37% | 20% | 0.37 |
| L2 | always_private | 0.376 | 0.321 | 17% | 10% | 1.11 |
| L2 | constraint_aware_greedy | 0.950 | 0.929 | 100% | 47% | 0.54 |
| L2 | greedy_cheapest | 0.542 | 0.346 | 40% | 30% | 0.22 |
| L2 | greedy_max_discount | 0.521 | 0.483 | 53% | 0% | 5.19 |
| L2 | oracle | 1.000 | 1.000 | 100% | 100% | 0.00 |
| L2 | random | 0.490 | 0.447 | 57% | 0% | 6.00 |
| L2 | real_shopper | 0.546 | 0.535 | 70% | 0% | 6.08 |

## Shortcut gate (each must sit below constraint-aware greedy)

- L1 / always_private: PASS
- L1 / always_coupon_sku: PASS
- L1 / always_lowest_shelf: PASS
- L2 / always_private: PASS
- L2 / always_coupon_sku: PASS
- L2 / always_lowest_shelf: PASS
