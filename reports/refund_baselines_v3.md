# Refund baselines — dev

Fits from train/L3: reject reason NOT_ON_RECEIPT, approve reason PRICE_MATCH, refund 100c.

| level | baseline | mean reward | false approves |
|---|---|---|---|
| L1 | always_approve | 0.195 | 59 |
| L1 | always_reject | 0.270 | 0 |
| L1 | oracle | 1.000 | 0 |
| L1 | rule_parser | 1.000 | 0 |
| L2 | always_approve | 0.128 | 146 |
| L2 | always_reject | 0.360 | 0 |
| L2 | oracle | 1.000 | 0 |
| L2 | rule_parser | 1.000 | 0 |
| L3 | always_approve | 0.093 | 241 |
| L3 | always_reject | 0.382 | 0 |
| L3 | oracle | 1.000 | 0 |
| L3 | rule_parser | 0.998 | 0 |

| pooled (all levels) |

| baseline | mean reward |
|---|---|
| always_reject | 0.337 |
| always_approve | 0.139 |
| rule_parser | 0.999 |
| oracle | 1.000 |

## Gates

- oracle is exactly 1.0: PASS
- rule_parser beats always_reject: PASS
- rule_parser beats always_approve: PASS
- always_reject in [0.15, 0.20] (got 0.337): FAIL
