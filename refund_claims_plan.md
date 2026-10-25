# Task Plan: Refund-Claim Adjudication

## 0. Summary

**Use case.** Customer-support automation: a customer writes about a purchase, and the agent decides whether a refund is owed under the store's policy, and how much.

**Task.** The model gets:
- a **real receipt**
- this week's **reference prices** for those items
- the household's **real live coupons**
- a fixed **refund policy**
- a customer message with 1–3 claims in natural language

For each claim it outputs the receipt line, approve/reject, the reason code, and the refund amount.

**Reward.** Fully programmatic, with no judge. Every claim's correct outcome follows deterministically from the policy applied to real data.

**Why an LLM.** A program can apply the policy *once the claim is structured*. The hard part is getting there from free text: resolving "the bigger bag of chips" or "my store-brand coffee" to a receipt line, identifying which rule the claim invokes, and applying rule precedence. There's no ML baseline for this; the only non-LLM competitor is a hand-written rule parser, which we build and report (§7).

**Reuse.** The cart optimizer's price table and pricing definitions (regular/loyalty unit price), its coupon eligibility logic (targeting × campaign window × coupon→product), data cleaning and exclusions, the household × time split, the eval runner, the rollout format, and the analysis.

**Real vs templated:**

| Element | Source |
|---|---|
| Receipt lines (items, quantities, prices, discounts) | Real |
| Reference prices | Real (chain median for that week) |
| Coupons (targeting, coverage, live window) | Real |
| Coupon typical value | Real (median redeemed amount) |
| Which claims are true or false | Derived from the real facts above |
| Policy text | Written by us (fixed) |
| Claim wording | Templated, with phrasings held out between train and eval |
| Claim date (days after purchase) | Sampled |

---

## 1. Policy (fixed, shown in the system prompt)

Rules are checked **in this order**; the first rule that decides a claim determines the reason code.

1. **Window:** claims filed more than `claim_window_days` after purchase → reject `OUTSIDE_WINDOW`.
2. **Item on receipt:** if the item isn't on the receipt → reject `NOT_ON_RECEIPT`.
3. **Price match** (the claim says they were overcharged):
   - if `paid loyalty unit price − reference price > price_tolerance` → approve `PRICE_MATCH`, with refund = difference × quantity
   - otherwise → reject `WITHIN_TOLERANCE`
4. **Missed coupon** (the claim says a coupon didn't apply):
   - no live coupon of this household covers the line → reject `NOT_ELIGIBLE`
   - a coupon discount was already applied on the line → reject `ALREADY_APPLIED`
   - otherwise → approve `MISSED_COUPON`, with refund = the coupon's typical value

Each claim is adjudicated **as stated**. A price claim is not re-interpreted as a coupon claim. Refunds are rounded to the cent at the end.

Config defaults: `claim_window_days: 14`, `price_tolerance: 0.10`.

---

## 2. Feasibility Checks (one script)

| # | Check | Why | Threshold / action |
|---|---|---|---|
| F1 | **Price-match supply**: distribution of (paid loyalty unit price − weekly reference) across lines | Need both real overcharges and real within-tolerance lines | Tune `price_tolerance` so 15–50% of eligible lines qualify |
| F2 | **Missed-coupon supply**: lines covered by a live targeted coupon with no coupon discount, per split | Source of valid `MISSED_COUPON` and of `NOT_ELIGIBLE` contrast | Enough for N = 100 per level after balancing |
| F3 | **Already-applied supply**: lines with a coupon discount that maps to one of the household's listed coupons | Redemptions are rare (~1% of lines) | If too few, drop the `ALREADY_APPLIED` type or upsample those receipts, and say so |
| F4 | **Typical coupon value coverage**: coupons with ≥`min_redemptions` redemptions | Refund amount needs a grounded value | Fallback chain: coupon → campaign median → global median. Report the share at each level |
| F5 | **Reference resolvability**: share of lines that a category noun alone identifies uniquely, vs needing a brand-tier, size, or quantity modifier, vs not uniquely describable | Claims must point to exactly one line | Lines that can't be uniquely described are never claim targets |
| F6 | **Receipt length**: lines per basket, with token estimates | Prompt size | Cap at `max_receipt_lines` (e.g. 40); report tokens |
| F7 | **Lexicon coverage**: share of receipt lines whose category has a curated everyday noun ("FLUID MILK PRODUCTS" → milk) | Natural references need a vocabulary | Claims target only covered categories. Curate the most frequent categories by hand |

Weight-priced and quantity-anomaly lines (from the existing exclusion logic) are never claim targets.

---

## 3. Instance Generation

1. **Anchor:** a real basket (household, day, receipt lines) from the split, with ≥1 eligible claim target. The **claim date** is the purchase day plus a sampled delay. Most delays fall inside the window; a configured share falls outside, to produce `OUTSIDE_WINDOW` claims.
2. **Context:**
   - reference prices for the receipt's products that week
   - the household's live coupons on the purchase day, each with its typical value and **the codes of the receipt lines it covers** (explicit membership, so there's no ambiguity)
3. **Claims:** sample up to 3 claims about **distinct lines**.
   - **Claim types** are balanced so that ~50% of claims are valid, spread over the approve reasons (`PRICE_MATCH`, `MISSED_COUPON`) and the reject reasons (`OUTSIDE_WINDOW`, `NOT_ON_RECEIPT`, `WITHIN_TOLERANCE`, `NOT_ELIGIBLE`, `ALREADY_APPLIED`).
   - **True and false claims come from real facts**: a price-match claim on a line that really is above reference vs one that isn't; a missed-coupon claim on a line that really is covered and unredeemed vs not covered vs already redeemed.
   - **`NOT_ON_RECEIPT` items** are sampled from categories in the household's history that are absent from this receipt, so the claims are plausible.
4. **Item references:** pick the cheapest reference style that resolves uniquely:
   - category noun ("the milk")
   - brand-tier modifier ("the store-brand coffee")
   - size ("the bigger bag of chips", when two lines share a category)
   - quantity ("the two yogurts")

   Then **re-resolve against the receipt to verify exactly one line matches.**
5. **Message:** fill phrasings for each claim type, chain the claims naturally ("…and also…"), and optionally add irrelevant filler ("my kids love it, but…").

   **Phrasing pools are split:** about 70% of phrasings are used for train/dev and about 30% are held out for eval only. This tests generalization to unseen wording, and it stops the rule parser from overfitting its development set.
6. **Store** the instance's ground truth: per claim, its line, decision, reason and refund, plus generator metadata (reference style, claim type, filler on/off).

---

## 4. Difficulty Levels

**The lever is the number of claims per message:** L1 / L2 / L3 = 1 / 2 / 3 claims.

**Nested:** every anchor gets 3 claims. L1 uses claim 1, L2 uses claims 1–2, and L3 uses all three, on the **same receipt and context**; only the message text changes. Differences between levels then come purely from handling more claims in one message: tracking several items, avoiding cross-claim mix-ups, and keeping the order straight.

Receipt length, reference style, and claim type are **stratified in the analysis**, not used as levers.

---

## 5. Prompt

- **System:** the role (support agent for a grocery chain), the policy (§1) with its precedence, the reason-code list, and the output contract.
- **User:**
  - Purchase day and claim date (or "days since purchase").
  - The receipt as a table:

    `line | category | sub-category | brand tier | size | qty | regular unit price | loyalty disc | coupon disc | paid`
  - The reference price per line.
  - The live coupons:

    `coupon | typical value | covers lines`
  - The customer message.
- **Output:** reasoning, then exactly one

  `<answer>{"claims": [{"line": "L07" | null, "decision": "approve" | "reject", "reason": "<CODE>", "refund": 0.42}, ...]}</answer>`

  with claims **in the order they appear in the message**. `line` is `null` only for `NOT_ON_RECEIPT`, and the refund is 0 for rejections.

---

## 6. Reward

**Parse gate (all-or-nothing).** Zero reward unless all of these hold:
- exactly one answer block, and valid JSON
- the number of claims equals the number in the message
- valid enums
- `line` is a receipt code or `null`
- `refund` is a number ≥ 0

**Per claim** (a wrong decision scores 0 for that claim):
```
truth = approve:  r = correct_decision · (0.25 + 0.25·line_ok + 0.25·reason_ok + 0.25·refund_ok)
truth = reject:   r = correct_decision · (0.25 + 0.25·line_ok + 0.50·reason_ok)
```
- `refund_ok` means within $0.01.
- For rejects, the refund must be 0, or the claim's `r` is 0.
- `NOT_ON_RECEIPT` counts `line = null` as `line_ok`.

**Instance reward** = the mean of `r` over its claims, in [0, 1].

**Why these weights.** The reject reason carries double weight: telling *which* check fails is the actual work. So "always reject with a guessed reason" earns little.

**Shortcut table** (to be computed exactly on dev; rough expectations):

| Strategy | Expected R |
|---|---|
| Always reject, most common reason, no line | ≈ 0.15–0.2 |
| Always reject, correct line, random reason | ≈ 0.3 |
| Always approve, refund = median coupon value | ≈ 0.15–0.25 |
| Oracle | 1.0 |

**Logged metrics (weight 0):** parse_ok, per-claim decision accuracy, line accuracy, reason accuracy, refund accuracy, **false-approve rate** (money wrongly paid out), **false-reject rate** (valid customers denied), and **dollar-weighted error** (total |refund − correct refund|).

---

## 7. Baselines

All run through the same reward.
1. **Always reject**, with the most frequent reject reason.
2. **Always approve**, with refund = the median coupon value.
3. **Rule-based parser.** Keyword rules for the claim type, plus lexicon matching from nouns and modifiers to receipt lines, then exact policy application. It's developed **only on train/dev phrasings**, without access to generator internals. This is the realistic non-LLM competitor; the gap between it and LLMs on held-out phrasings is the central "why an LLM" evidence.
4. **Oracle:** the generator's ground truth (sanity check, R = 1).

---

## 8. Tests

**Reward:**
- Oracle → 1.0.
- Correct decisions but claims out of order → penalized by the line, reason, and refund terms.
- Wrong number of claims, invalid enum, negative refund, `line` not on the receipt, multiple answer blocks → 0.
- Approve with the right line and wrong refund → 0.75 for that claim.
- A reject with a nonzero refund → 0 for that claim.

**Generator:**
- every reference resolves to exactly one line (re-resolved independently)
- every true claim's conditions hold and every false claim's condition fails, recomputed from raw transactions for 50 random claims
- policy precedence gives a unique reason
- L1 ⊂ L2 ⊂ L3 nesting holds
- train and eval phrasing pools are disjoint
- no claim targets a weight-priced line

---

## 9. Analysis (existing pipeline plus)

- Per-claim accuracy by **claim type × level**, with bootstrap CIs.
- A **reason confusion matrix**: which checks models skip or confuse, e.g. `ALREADY_APPLIED` vs `NOT_ELIGIBLE`.
- **Line-resolution accuracy by reference style** (noun / brand tier / size / quantity), which shows where natural-language grounding breaks.
- **Seen vs held-out phrasings** for LLMs and the rule parser.
- **False-approve vs false-reject** rates, and dollar-weighted error. This is the business view of errors.
- Within-instance spread and **zero-variance group share** per level. The reward is discrete here, so this share is meaningful. Also pass@1 vs pass@8 (exact R = 1).
- Examples: a clean multi-claim success, a line mis-resolution, a precedence error (e.g. approving an out-of-window claim), and a refund arithmetic error.

---

## 10. Is This Worth RL? (decision rule for the recommendation slide)

| Observation | Interpretation | Recommendation |
|---|---|---|
| Strong models ≈ 1.0 at all levels | Saturated | Make it harder before training (§12 variants) |
| Rule parser ≈ LLMs on held-out phrasings | Wording isn't the bottleneck; the task is too templated | Increase phrasing diversity before training |
| Small models fail mostly on line resolution (size/brand references) or precedence | A learnable grounding and rule-following skill | RL worth it, training on L2–L3 |
| Errors mostly in refund arithmetic | Arithmetic, not reasoning | Cheaper fix: a calculator tool, or the refund computed from the decision |
| High zero-variance share at a level | No GRPO signal there | Train at the level where pass@8 ≫ pass@1 |
| False approvals dominate errors | Costly failure mode | For training, consider asymmetric weights (false approve worse than false reject) |

---

## 11. Steps

1. Feasibility script (F1–F7). Tune `price_tolerance` once and curate the lexicon for the most frequent categories.
2. Generator: claims, reference styles with uniqueness verification, phrasing pools with a train/eval split, nested levels. Inspect ~10 instances by eye.
3. Reward + tests.
4. Baselines, including the rule parser, developed on train/dev phrasings only.
5. Eval with the existing runner: 2–3 models × 3 levels, **k = 8, N = 100 anchors on the primary eval split** (same anchors at every level). Run the cost dry run first.
6. Analysis (§9).

---

## 12. Open Decisions / Defaults

- **Lever = claims per message.** Receipt length is stratified, not leveled.
- **Structured output only**, no customer-facing reply text, so the reward needs no judge. Adding an unscored reply is possible later.
- **Coupon coverage is shown as explicit line codes.** *Harder v2:* describe coverage by attributes ("national-brand coffee from manufacturer M"), so the model must match attributes to lines.
- **Claims are adjudicated as stated.** *Harder v2:* the customer describes the problem wrongly ("overcharged", when actually a coupon was missed), and the policy says to check all applicable rules.
- **Partial-unit claims** ("one of the two yogurts was overpriced") are deferred.
- **The policy is fixed across instances.** *Harder v2:* vary the policy parameters per instance (window, tolerance), so the model must read the policy, not memorize it.
