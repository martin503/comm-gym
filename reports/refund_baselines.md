# Refund baselines — dev

Fits from train/L3: reject reason NOT_ON_RECEIPT, approve reason PRICE_MATCH, refund 100c.

| level | baseline | mean reward | false approves |
|---|---|---|---|
| L1 | always_approve | 0.158 | 68 |
| L1 | always_reject | 0.395 | 0 |
| L1 | oracle | 1.000 | 0 |
| L1 | rule_parser | 1.000 | 0 |
| L2 | always_approve | 0.110 | 156 |
| L2 | always_reject | 0.401 | 0 |
| L2 | oracle | 1.000 | 0 |
| L2 | rule_parser | 1.000 | 0 |
| L3 | always_approve | 0.077 | 254 |
| L3 | always_reject | 0.397 | 0 |
| L3 | oracle | 1.000 | 0 |
| L3 | rule_parser | 1.000 | 0 |

| pooled (all levels) |

| baseline | mean reward |
|---|---|
| always_reject | 0.398 |
| always_approve | 0.115 |
| rule_parser | 1.000 |
| oracle | 1.000 |

## Gates

- oracle is exactly 1.0: PASS
- rule_parser beats always_reject: PASS
- rule_parser beats always_approve: PASS
- always_reject in [0.15, 0.20] (got 0.398): FAIL
