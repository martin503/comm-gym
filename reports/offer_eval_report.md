# Offer Eval Report

- split: eval_unseen; judged term weight 0.6

| model | level | rollouts | gate pass | judge-free mean [CI] | judged | judge win [CI] | final [CI] | words |
|---|---|---|---|---|---|---|---|---|
| baseline_generic | L1 | 50 | 0% | 0.00 [0.00, 0.00] | 100% | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 7 |
| baseline_generic | L2 | 50 | 0% | 0.00 [0.00, 0.00] | 100% | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 7 |
| baseline_generic | L3 | 50 | 0% | 0.00 [0.00, 0.00] | 100% | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 7 |
| baseline_random_template | L1 | 50 | 100% | 0.24 [0.23, 0.25] | 100% | 0.00 [0.00, 0.00] | 0.24 [0.23, 0.25] | 9 |
| baseline_random_template | L2 | 50 | 100% | 0.22 [0.21, 0.23] | 100% | 0.00 [0.00, 0.00] | 0.22 [0.21, 0.23] | 10 |
| baseline_random_template | L3 | 50 | 100% | 0.21 [0.21, 0.22] | 100% | 0.01 [0.00, 0.04] | 0.22 [0.21, 0.24] | 9 |
| baseline_template_top_affinity | L1 | 50 | 100% | 0.28 [0.28, 0.29] | 100% | 0.02 [0.00, 0.05] | 0.29 [0.28, 0.31] | 9 |
| baseline_template_top_affinity | L2 | 50 | 100% | 0.28 [0.28, 0.29] | 100% | 0.04 [0.00, 0.09] | 0.31 [0.28, 0.34] | 9 |
| baseline_template_top_affinity | L3 | 50 | 100% | 0.28 [0.27, 0.28] | 100% | 0.07 [0.03, 0.12] | 0.32 [0.30, 0.35] | 9 |
| openai__gpt-6-luna | L1 | 400 | 88% | 0.28 [0.27, 0.29] | 100% | 0.51 [0.47, 0.56] | 0.62 [0.59, 0.65] | 12 |
| openai__gpt-6-luna | L2 | 400 | 86% | 0.27 [0.26, 0.28] | 100% | 0.54 [0.50, 0.59] | 0.64 [0.61, 0.67] | 13 |
| openai__gpt-6-luna | L3 | 400 | 77% | 0.25 [0.23, 0.26] | 100% | 0.63 [0.58, 0.67] | 0.70 [0.67, 0.73] | 13 |

## Gate failure taxonomy

- baseline_generic L1: gate:not_specific ×50
- baseline_generic L2: gate:not_specific ×50
- baseline_generic L3: gate:not_specific ×50
- baseline_random_template L1: none
- baseline_random_template L2: none
- baseline_random_template L3: none
- baseline_template_top_affinity L1: none
- baseline_template_top_affinity L2: none
- baseline_template_top_affinity L3: none
- openai__gpt-6-luna L1: gate:ungrounded_category:shop ×11, gate:ungrounded_category:foods ×8, gate:ungrounded_category:beans ×6, gate:ungrounded_category:meals ×5, gate:ungrounded_category:drinks ×5
- openai__gpt-6-luna L2: gate:ungrounded_category:shop ×13, gate:ungrounded_category:foods ×7, gate:ungrounded_category:beans ×6, gate:ungrounded_category:fruits ×5, gate:ungrounded_category:frozen meat ×5
- openai__gpt-6-luna L3: gate:ungrounded_category:shop ×13, gate:ungrounded_category:drinks ×13, gate:ungrounded_category:snacks ×11, gate:ungrounded_category:foods ×8, gate:ungrounded_category:fruits ×7

## Examples

**baseline_generic L1 gate failure**
> Great offers this week, come and see!
— failures: ['not_specific']

**baseline_generic L2 gate failure**
> Great offers this week, come and see!
— failures: ['not_specific']

**baseline_generic L3 gate failure**
> Great offers this week, come and see!
— failures: ['not_specific']

**baseline_random_template L1 best (final 0.29)**
> Your usual makeup and treatment has an offer this week.
— selected ['k01']

**baseline_random_template L2 best (final 0.30)**
> Your usual processed has an offer this week.
— selected ['k01']

**baseline_random_template L3 best (final 0.57)**
> Your usual cheese has an offer this week.
— selected ['k01']

**baseline_template_top_affinity L1 best (final 0.59)**
> Your usual dry sauces gravy has an offer this week.
— selected ['k01']

**baseline_template_top_affinity L2 best (final 0.87)**
> Your usual processed has an offer this week.
— selected ['k01']

**baseline_template_top_affinity L3 best (final 0.59)**
> Your usual dry sauces gravy has an offer this week.
— selected ['k01']

**openai__gpt-6-luna L1 best (final 1.00)**
> Enjoy offers on oral hygiene, cheese, and fruit and vegetables—these deals end soon!
— selected ['k02', 'k03', 'k01']
**openai__gpt-6-luna L1 gate failure**
> Enjoy offers on cheese, yogurt, milk, and ice cream—plus frozen meals and pizza!
— failures: ['ungrounded_category:meals']

**openai__gpt-6-luna L2 best (final 1.00)**
> Check out coupons on fluid milk, frozen pizza, and hair care, picked for your household.
— selected ['k02', 'k01', 'k03']
**openai__gpt-6-luna L2 gate failure**
> Check out offers on beef and pork, fruits and vegetables, and frozen meat—picked for your cart.
— failures: ['ungrounded_category:fruits']

**openai__gpt-6-luna L3 best (final 1.00)**
> Save on national-brand soft drinks, beef, and lunchmeat with your coupons this week!
— selected ['k03', 'k02', 'k01']
**openai__gpt-6-luna L3 gate failure**
> Find offers on beef and pork, fresh fruits and vegetables, and wholesome snacks.
— failures: ['ungrounded_category:fruits']

