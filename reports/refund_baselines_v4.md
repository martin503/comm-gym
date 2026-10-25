# Refund baselines — eval_unseen

Fits from train/L3: reject reason NOT_ON_RECEIPT, approve reason PRICE_MATCH, refund 100c.

| level | baseline | mean reward | false approves |
|---|---|---|---|
| L1 | always_approve | 0.215 | 51 |
| L1 | always_reject | 0.263 | 0 |
| L1 | oracle | 1.000 | 0 |
| L1 | rule_parser | 0.693 | 0 |
| L2 | always_approve | 0.154 | 130 |
| L2 | always_reject | 0.314 | 0 |
| L2 | oracle | 1.000 | 0 |
| L2 | rule_parser | 0.694 | 0 |
| L3 | always_approve | 0.119 | 218 |
| L3 | always_reject | 0.355 | 0 |
| L3 | oracle | 1.000 | 0 |
| L3 | rule_parser | 0.719 | 0 |

| pooled (all levels) |

| baseline | mean reward |
|---|---|
| always_reject | 0.310 |
| always_approve | 0.163 |
| rule_parser | 0.702 |
| oracle | 1.000 |

## Gates

- oracle is exactly 1.0: PASS
- rule_parser beats always_reject: PASS
- rule_parser beats always_approve: PASS
- always_reject in [0.15, 0.20] (got 0.310): FAIL
