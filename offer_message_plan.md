# Task Plan: Grounded Offer Message Drafter

## 0. Summary

**Use case.** Personalized push notifications in grocery CRM: "pick this household's best offers this week and write the message."

**Task.** For a household on day `d`, the model sees:
- a profile built from its real purchase history
- the real coupons live for that household that day (campaign targeting + coupon eligibility + campaign dates)

It selects 1–3 coupons and writes a push message of at most 40 words.

**Reward, in two layers:**
1. **Programmatic grounding gate.** No invented facts: no numbers, no categories outside the selected offers, no false urgency, no wrong brand-tier claims.
2. **Quality score:** a small programmatic relevance term, plus a pairwise LLM judge against a fixed reference message.

**Where this sits in the gym.** The cart optimizer is graded by an exact solver, and replenishment by a real outcome. This task has **no gold answer at all**, only a scorer, which makes it the most RL-native of the three and the one most exposed to reward hacking. The design is mostly about making the judge hard to game and measuring how noisy it is.

**Reuse.** Data loading and cleaning, the household × time split (cutoff week 68), the eval runner, the rollout format, the analysis, and the environment-adapter pattern. New: generator, prompt, gate, judge, baselines.

**Data limits that shape the task.**
- No product names, so messages stay at category and brand-tier level ("your usual store-brand coffee").
- No coupon face values (only redeemed amounts exist), so the message may contain **no amounts or numbers at all**.

---

## 1. Feasibility Checks (one script)

| # | Check | What would break the task | Threshold / action |
|---|---|---|---|
| F1 | **Instance supply**: (household, day) pairs with ≥5 / ≥10 / ≥20 live targeted coupons, per split | Too few anchors for L3 | Enough for N = 50 per level on the primary eval split. If not, lower the L3 count |
| F2 | **Coupon breadth**: number of commodities covered per coupon | Coupons covering dozens of commodities can't be described meaningfully | Report the distribution. Each coupon is described by its top-3 commodities by product count |
| F3 | **Affinity spread**: per instance, the share of live coupons whose commodities the household bought in history | 0 almost everywhere (nothing to personalize) or 1 almost everywhere (selection trivial) | A spread between the two, e.g. the median instance has 20–80% "relevant" coupons |
| F4 | **Redemption signal**: share of instances where the household later redeemed ≥1 of its live coupons | Too sparse for the redemption metric (§7) | Report. If below ~5%, the redemption metric is reported as indicative only |
| F5 | **Brand-tier mix**: share of coupons covering mostly Private vs mostly National products | All one tier, making brand-tier claims meaningless to check | Report |
| F6 | **Lexicon collisions**: how many commodity keywords map to more than one commodity (e.g. "cheese") | Ambiguous mentions | A mention passes if *any* of the commodities its keyword maps to is covered by a selected coupon |
| F7 | **Judge reliability**, on ~50 message pairs: self-agreement (same pair judged twice) and order consistency (A/B vs B/A) | The reward is mostly noise | Self-agreement ≥ ~80% and order consistency ≥ ~75%. If below, change the judge model or rubric before building further |

F7 is the one that matters most. If the judge can't agree with itself, nothing downstream is meaningful.

---

## 2. Instance Definition

| Item | Definition | Config default |
|---|---|---|
| Anchor | (household, day `d`) where the household is targeted by ≥1 campaign live on `d`, with ≥ the L3 coupon count live | |
| Live coupons | Coupons of campaigns targeted to this household with `START_DAY ≤ d ≤ END_DAY` | |
| Coupon description | Top-3 covered commodities, dominant brand tier (Private / National / mixed), and an "ends soon" flag if `END_DAY − d ≤ ends_soon_days` | `ends_soon_days: 7` |
| Profile | From the household's trips in `[d − history_days, d)`: top 10 commodities with purchase counts, store-brand share per commodity, overall store-brand share, trips per week | `history_days: 98` |
| Demographics | **Excluded by default.** They're available for only a minority of households, and personalizing on age or income invites stereotyping, which a judge might reward | `use_demographics: false` |
| Sampling | Anchors per household ≥14 days apart, at most `max_instances_per_hh` per household; early anchors from week 32 (campaign start) to the cutoff | |

**Splits.** The existing household × time split. Campaigns spanning the cutoff appear on both sides. That's not a leakage concern, since there's no gold answer to leak.

---

## 3. Difficulty Levels

**The only lever is the number of live coupons shown**, nested (L1 ⊂ L2 ⊂ L3 per anchor), so all levels share households and days:

| Level | Coupons shown |
|---|---|
| L1 | 5 |
| L2 | 10 |
| L3 | 20 (lower if F1 says supply is short) |

More coupons make selection harder (more distractors, more to cross-reference against the profile), and they create more room for grounding slips: mentioning a category from an unselected coupon.

---

## 4. Prompt

- **System:**
  - the role: copywriter for a grocery chain's push notifications
  - the rules:
    - at most 40 words
    - no numbers, prices, or percentages
    - mention only categories covered by the coupons you select
    - say "ends soon" (or similar) only for coupons flagged as ending soon
    - "store brand" / "national brand" claims must match the coupon
    - no brand or product names (none are given)
  - the output contract
- **User:**
  - The household profile (§2).
  - The coupon table: `code | covers (top-3 commodities) | brand tier | ends soon?`. Order shuffled, short codes `k01…`.
- **Output:** reasoning, then exactly one `<answer>{"selected": ["k03", "k11"], "message": "..."}</answer>`.

---

## 5. Reward

### 5.1 Grounding gate (programmatic; any failure → R = 0)
1. **Parse:** exactly one answer block, valid JSON, 1–3 unique valid coupon codes, `message` is a string.
2. **Length:** ≤ 40 words.
3. **No numbers:** no digits, `$`, `%`, or spelled-out amounts ("half price", "free"). Nothing in the input supports any amount.
4. **Category grounding:** every commodity keyword found in the message (from the lexicon) must map to a commodity covered by a selected coupon.
5. **Must be specific:** at least one selected coupon's commodity is mentioned. Generic "great deals this week!" fails.
6. **Urgency grounding:** urgency phrases ("ends soon", "last chance", "today only", "hurry", …) are allowed only if a selected coupon has the "ends soon" flag.
7. **Brand-tier grounding:** "store brand" / "own brand" / "national brand" claims must match the tier of a selected coupon that covers the mentioned category.
8. **No judge-directed text:** the message must not address an evaluator (e.g. "evaluator", "judge", "rating", "score", "ignore previous"). This is a cheap filter against judge prompt injection.

**Commodity lexicon.** The head nouns are auto-extracted from the commodity names ("FROZEN PIZZA" → pizza, "FLUID MILK PRODUCTS" → milk), plus a short hand-written synonym list ("chips" → bag snacks, "soda" → soft drinks). **Known limitation:** an unusual paraphrase of an unselected category can slip through. The judge's faithfulness criterion is the backstop, and the analysis measures how often the lexical check and the judge disagree.

### 5.2 Quality (only if the gate passes)
- **Affinity** (programmatic, real data): the purchase-count-weighted share of selected coupons' commodities that the household actually bought in its history window, in [0, 1]. Note: ranking by affinity is near-optimal by construction, so this term is deliberately small.
- **Judge win rate:** a pairwise comparison against a **fixed reference message** per instance, generated once by a mid-strength model and stored with the instance.
  - The judge sees the profile, the coupons, both selections, and both messages.
  - It judges in both orders, so per order: win = 1, tie = 0.5, loss = 0. The average of the two orders gives {0, 0.25, 0.5, 0.75, 1}.
  - **Rubric:** relevance to this household's habits; faithful to the inputs; clear; natural tone; persuasive without pressure or flattery.

### 5.3 Total
```
gate fails:   R = 0
gate passes:  R = 0.2 + 0.2 · affinity + 0.6 · judge_win
```
Any grounded message beats any ungrounded one. The judge dominates quality, by design.

**Logged metrics (weight 0):** gate pass rate, failure type per gate rule, affinity, judge win rate, word count, **redemption hit** (§7), and judge-vs-lexicon faithfulness disagreement.

### 5.4 Training note for the RL recommendation
A fixed reference **saturates**: once the policy beats it every time, the win rate is always 1 and the gradient vanishes. For training, recommend refreshing the reference periodically (e.g. to an earlier checkpoint) or comparing within the group. For eval, a fixed reference is what makes numbers comparable across models.

---

## 6. Judge Setup
- **Primary judge:** a local open-weight model served on the 3090s (the largest current Qwen that fits). Volume costs time, not API budget.
- **Agreement check:** an OpenAI model judges a ~10% subset. Report the agreement rate between the two judges.
- **Reliability**, reported alongside every result:
  - self-agreement (re-judge ~100 pairs)
  - order consistency
  - the reference-vs-itself tie rate (should be ≈ 0.5)

---

## 7. Baselines
All are run through the same gate and judge.
1. **Template:** the top-affinity coupon, fixed sentence: "Your usual {commodity} has an offer this week." Tests whether an LLM adds anything over a template.
2. **Random coupon + template.** Isolates the value of selection.
3. **Reference message.** Scores ≈ 0.5 on the judge term by construction (sanity check).
4. **Generic message** ("Great offers this week, come and see!"). Must be gated to 0.

**Redemption hit (real-outcome sanity check, not part of the reward):** the share of selected coupons that the household actually redeemed later in the campaign window, compared with the share for random selection from the same live set. This is the only place real behavior validates the selection. It is sparse (see F4), so it's indicative.

---

## 8. Tests

**Deterministic (gate):**
- digits; `$`; "half price"
- an unselected category mentioned; a synonym of an unselected category
- no selected category mentioned
- urgency without the "ends soon" flag
- store-brand claim on a National coupon
- 41 words
- 4 coupons selected, duplicate codes, invalid codes
- multiple answer blocks
- an "evaluator" note

Each must give R = 0. A clean grounded message must pass.

**Judge-robustness set** (run once against the real judge; ~20 instances × each variant vs the reference):

| Adversarial variant | Expected |
|---|---|
| Flattery ("our most valued customer…") | Loses or ties |
| Keyword stuffing of the household's top categories (passes the gate only if they're all selected) | Loses |
| Maximum length, padded | Loses or ties |
| Emoji / exclamation spam | Loses |
| Wrong personalization (National offer to a store-brand-loyal household) | Loses |
| Reference vs itself | ≈ 0.5 |
| Injection the gate misses (paraphrased appeal to the reader-as-evaluator) | Loses |

Any variant that **wins** is a found hack. Either fix the rubric or add a gate rule, and report it on the reward slide.

---

## 9. Is This Worth RL? (decision rule for the recommendation slide)

| Observation | Interpretation | Recommendation |
|---|---|---|
| Judge reliability low (F7 / §6) | The reward is mostly noise | Don't train on it; fix the judge first |
| Some adversarial variant wins | The reward is exploitable | Patch, re-run the robustness set, and only then train |
| LLMs ≈ template baseline | No value beyond templates | Not worth RL; use templates |
| Small models fail the gate often, large models pass | Grounding is the learnable skill | RL with the gate as the main signal; cheap and reliable |
| Gate passes, but best-of-k win ≫ mean win | Quality headroom exists | RL worth it; use a refreshed reference or in-group comparison (§5.4) |
| Selection beats random on redemption hit | Personalization reflects real behavior | Supporting evidence for the task's validity |

---

## 10. Steps
1. **Feasibility script** (F1–F6), plus the **judge reliability check** (F7) on ~50 hand-picked pairs.
2. Generator + prompt with nested L1/L2/L3. Generate and store a reference message per instance. Inspect ~10 instances.
3. Gate + lexicon + deterministic tests.
4. Judge prompt + robustness set. Iterate until no adversarial variant wins.
5. Baselines.
6. Eval with the existing runner: 2–3 models × 3 levels, **k = 8, N = 50 anchors** (same anchors at every level). Judge locally on everything, and with the OpenAI judge on ~10%. Budget mostly matters for the OpenAI policy models and the agreement subset, so run the cost dry run.
7. Analysis with the existing pipeline, plus:
   - gate failure breakdown by level
   - judge win rate with bootstrap CIs
   - judge reliability numbers
   - redemption-hit lift vs random
   - examples: a strong message, a grounding failure, and a judge-preferred-but-questionable message

---

## 11. Open Decisions / Assumptions
- **Push channel (≤ 40 words).** Email (≤ 120 words) is a config change, but it gives more room for judge hacking.
- **Reference model choice.** It should be mid-strength, so that both stronger and weaker models move the win rate.
- **Lexicon grounding is imperfect.** The judge's faithfulness criterion backs it up, and their disagreement rate is reported.
- **Coupon amounts are deliberately absent.** Inventing them would contradict "only real data".
- **Demographics are off by default.** Turning them on is a config flag, but check the judge for stereotype preference first.