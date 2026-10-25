# Refund baselines — dev

Fits from train/L3: reject reason NOT_ON_RECEIPT, approve reason PRICE_MATCH, refund 100c.

| level | baseline | mean reward | false approves |
|---|---|---|---|
| L1 | always_approve | 0.217 | 56 |
| L1 | always_reject | 0.275 | 0 |
| L1 | oracle | 1.000 | 0 |
| L1 | rule_parser | 1.000 | 0 |
| L2 | always_approve | 0.144 | 141 |
| L2 | always_reject | 0.330 | 0 |
| L2 | oracle | 1.000 | 0 |
| L2 | rule_parser | 1.000 | 0 |
| L3 | always_approve | 0.100 | 238 |
| L3 | always_reject | 0.363 | 0 |
| L3 | oracle | 1.000 | 0 |
| L3 | rule_parser | 1.000 | 0 |

| pooled (all levels) |

| baseline | mean reward |
|---|---|
| always_reject | 0.323 |
| always_approve | 0.154 |
| rule_parser | 1.000 |
| oracle | 1.000 |

## Gates

- oracle is exactly 1.0: PASS
- rule_parser beats always_reject: PASS
- rule_parser beats always_approve: PASS
- always_reject in [0.15, 0.20] (got 0.323): FAIL
