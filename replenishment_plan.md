# Task Plan: Replenishment ("Buy It Again")

## 0. Summary

**Use case.** A "buy it again" shelf or restock suggestions shown while the customer is shopping.

**Task.** For a household on day `d`, the model sees ~14 weeks of raw purchase history, one timeline per category. For each candidate category it outputs the **probability that the household buys it in the next 7 days**, given that the household shops at least once that week.

**Reward.** A proper scoring rule (Brier score). The model maximizes its expected reward only by reporting honest, calibrated probabilities.

**Where this sits in the gym.** The cart optimizer is graded by an exact solver; this task is graded by a **real outcome** (what the household actually did). Outcome noise caps the best achievable score, but it does not bias training, because every rollout in a group is scored against the same outcome.

**Reuse from the cart optimizer.** Data loading and cleaning (exclusion list), the household × time split (cutoff week 68), the eval runner, the rollout format, the analysis (bootstrap CIs, within-instance spread), and the environment-adapter pattern. Only the generator, prompt, reward, and baselines are new.

---

## 1. Feasibility Checks (run first, one script)

These answer whether the task has learnable signal at all, beyond "copy how often they buy it". Each check has a light threshold. Failing one means adjusting a parameter or rethinking the task, not adding more checks.

| # | Check | What would make the task degenerate | Threshold |
|---|---|---|---|
| F1 | **Positive rate**: share of (instance, candidate) pairs bought in the window | Almost everything bought (trivial yes) or almost nothing (trivial no) | 10–60%. If outside, adjust `history_days` / `min_purchases` |
| F2 | **Near-deterministic share**: candidates whose weekly purchase rate in history is ≥0.9 or ≤0.1 | Most candidates are "always" or "never" items, i.e. your "90% of households buy every commodity weekly" scenario | < 50% of candidates. Also report the staple share separately |
| F3 | **Due-date curve**: P(bought in window), binned by `days since last / mean interval` (e.g. <0.5, 0.5–1, 1–1.5, >1.5) | A flat curve means purchases are memoryless: there's no cycle to infer, and the task reduces to frequency copying | The "overdue" bin should be clearly above the "just bought" bin (e.g. ≥1.5×) |
| F4 | **Timing lift**: Brier skill of the logistic-regression baseline over the household-weekly-rate baseline, on dev | If timing features add nothing beyond frequency, there's no reasoning headroom beyond simple bookkeeping | Positive, with a bootstrap CI excluding 0 |
| F5 | **Any signal at all**: Brier skill of the household-weekly-rate baseline over the constant baseline | History is useless | Clearly positive |
| F6 | **Candidate supply**: share of anchors with ≥10 / ≥20 / ≥30 eligible candidates | L3 only feasible for very heavy shoppers | Enough anchors at ≥30 for N = 100 per eval split after caps. If not, lower L3 to 25 |
| F7 | **Conditioning drop rate**: share of windows with no trip | | Report only |
| F8 | **Per-instance positives**: share of instances with 0 positives or all positives | Instances with no information | Report. Consider dropping instances with 0 positives if they're a large share |

**If F3 and F4 both fail**, the honest conclusion is that household purchases look memoryless at this granularity. The task then measures frequency estimation, not cycle reasoning. Before building further, try sub-commodity granularity (more specific items have more regular cycles), or drop the task.

---

## 2. Instance Definition

| Item | Definition | Config default |
|---|---|---|
| Granularity | `COMMODITY_DESC` | `granularity: commodity` |
| Anchor day `d` | A day with ≥`min_history_trips` household trips in the history window, **and** ≥ the L3 candidate count eligible (see §3) | `min_history_trips: 6` |
| History | All of the household's trips with `d − history_days ≤ day < d` | `history_days: 98` (14 weeks) |
| Eligible candidates | Commodities bought on ≥2 distinct trips in the history window | `min_purchases: 2` |
| Target window | Days `[d, d + 6]` | `horizon_days: 7` |
| Label `y_c` | 1 if commodity `c` is bought on any trip in the target window, else 0 | |
| Conditioning | Keep only windows with ≥1 trip, **and say so in the prompt**. Variant: `conditioning: none` keeps no-trip windows (all labels 0). | `conditioning: shops_in_window` |
| Staples | Kept as candidates. Results reported with and without them (staple = bought on ≥`staple_trip_share` of history trips) | `staple_trip_share: 0.6` |

**Why condition on a trip.** A buy-again shelf appears when the customer is shopping, so "given they shop, what do they restock" *is* the deployment distribution. A proactive push reminder would be unconditional, and would also have to predict whether the household shops at all. That's available as a config variant. Train and eval use the same conditioning, and the condition is stated in the prompt so the model's probabilities can be calibrated to the instances it actually sees.

**Sampling:**
- A household's anchors are spaced ≥`horizon_days` apart.
- At most `max_instances_per_hh` instances per household.
- Train anchors run from week 15 (after the ramp) up to the cutoff, and the **whole target window must end before the cutoff**.
- Eval anchors fall after the cutoff. Their history may reach back before it.

**Splits.** The existing household × time split.

---

## 3. Difficulty Levels

**The only lever is the number of candidates. Every level uses the raw timeline.**

| Level | Candidates |
|---|---|
| L1 | 10 |
| L2 | 20 |
| L3 | 30 (25 if F6 says supply is short) |

**Nested design.** Every anchor qualifies for L3. Its L1 candidates are a random subset of its L2 candidates, which are a random subset of its L3 candidates. So all three levels share the same households, days, and outcomes, and any difference between levels comes from the number of timelines the model has to track, not from a different population. (If each level were sampled separately, L3 would contain only heavy shoppers, confounding difficulty with household type.)

**Intrinsic predictability** is stratified after the fact rather than used as a lever:
- **By instance:** terciles of the logistic-regression baseline's Brier (predictable / medium / unpredictable).
- **By candidate:** number of prior purchases of that category (2, 3–4, 5+). This is the key stratum for §8.

---

## 4. Prompt

- **System:**
  - the role ("predict which categories this household restocks this week")
  - the conditioning statement ("the household will shop at least once during the next 7 days")
  - the output contract
  - a note that outputs are probabilities scored by squared error
- **User:**
  - The household's trip days in the history window, as "days ago" (the overall shopping rhythm).
  - One line per candidate: `code | commodity | purchases as days-ago (quantity)`, e.g. `c07 | COFFEE | 82(1), 55(1), 27(2)`. No precomputed statistics.
  - Candidate order is shuffled per instance, with short codes `c01…cNN`.
- **Output contract:** reasoning first, then exactly one `<answer>{"c01": 0.35, "c02": 0.9, ...}</answer>` containing **every** candidate code exactly once, each with a value in [0, 1].

The token count is logged per instance (~1–1.5k at 30 candidates).

---

## 5. Reward

**Parse gate (all-or-nothing).** Zero reward unless all of these hold:
- exactly one `<answer>` block
- valid JSON
- the key set equals the candidate set exactly
- every value is a number in [0, 1]

**Score:**
```
brier = mean over candidates of (p_c − y_c)²
R     = 1 − brier            # in [0, 1]
```

**Why Brier.**
- **It's proper:** the expected penalty is lowest exactly when `p_c` equals the true chance of purchase.
- **It's bounded:** log-loss is also proper, but it explodes at hard 0s and 1s.
- **It gives credit on every candidate.**

**Shortcut analysis:**

| Strategy | Reward at a 25% positive rate | Notes |
|---|---|---|
| Always 0.5 | 0.75, regardless of outcome | Below every informative strategy |
| Always 0 | 0.75 | Same |
| Constant base rate (0.25) | ~0.81 | The best *uninformed* strategy |
| Household weekly rate | higher | First informative baseline |
| Oracle | 1.0 | |

The realistic failure mode is **collapsing to near-constant predictions**. It shows up as AUC ≈ 0.5, which is why AUC is logged.

**Reporting.** Raw rewards cluster high, so always report the **Brier skill score** vs the baselines.

**Training note for the RL recommendation.** Rollouts will differ by small amounts in R. GRPO's per-group std normalization blows those small differences up, which can amplify sampling noise in the decimals. Consider a variant without std normalization (e.g. Dr. GRPO), or coarser probability bins (§10).

**Considered and rejected.**
- **Class-balanced Brier:** it's not proper.
- **Top-K + F1:** fixed set size, frequent ties within a group, and "pick the K most frequent" is a strong fallback.

**Logged metrics (weight 0):**
- `parse_ok` and `brier`
- AUC per instance, where both classes are present
- precision@3 and @5
- mean predicted `p` vs actual positive rate
- Brier by staple / non-staple and by number of prior purchases

---

## 6. Baselines
All output probabilities and run through the same reward.
1. **Constant:** the global positive rate from train.
2. **Household weekly rate:** the fraction of history weeks in which the household bought `c`.
3. **Due-date rule:** a logistic curve on `days_since_last / mean_interval`, with 2 parameters fit on train.
4. **Logistic regression:** weekly rate, days since last, mean interval, interval std, purchase count, staple flag, and household trip rate. Fit on train. This is the classical-ML reference.
5. **Oracle:** `p = y` (sanity check).

The baselines are computed once per anchor on its L3 candidate set, then subset for L1/L2. Their scores barely change across levels, which makes them the flat reference line on the difficulty plot.

---

## 7. Tests
- Oracle → 1.0. `p = 1 − y` → 0.0. Hand-computed values for all 0 / all 1 / all 0.5.
- Missing key, extra key, duplicate answer blocks, out-of-range values, strings, NaN → R = 0.
- **Properness check:** for simulated candidates with a known true probability `q`, the expected reward is maximized at `p = q`.
- **Generator:**
  - no target window crosses the cutoff
  - anchors are ≥7 days apart
  - with conditioning on, every window has ≥1 trip
  - the L1 ⊂ L2 ⊂ L3 nesting holds
  - labels match a direct recomputation from raw transactions for 20 random instances

---

## 8. Is This an LLM Task? (decision rule for the recommendation slide)

**The case for.**
- In a real product, an assistant would reason over the customer's history in context, alongside conversation and other signals.
- LLMs bring semantic priors that a per-household model lacks: coffee lasts longer than milk, perishables cycle faster, buying 2 units delays the next purchase.
- Those priors should matter most where the household has **few purchases** of a category.

**The case against.** Classical models on engineered features are cheap, strong, and calibrated.

**How the results decide:**

| Observation | Interpretation | Recommendation |
|---|---|---|
| Best LLM ≈ or > LR, flat across L1→L3 | The LLM extracts the signal | RL worth it, training on L3 |
| LLM ≈ LR at L1 but degrades at L2/L3 while baselines stay flat | The bottleneck is tracking many timelines at once | RL targets L2/L3. This is the main difficulty-curve story. |
| LLM ≪ LR even at L1 | No added value over the features, at least in raw-timeline form | Not an LLM task as posed; use a classical model. A run with precomputed stats would tell whether the gap is extraction or reasoning, but that is out of scope by design. |
| LLM > LR on the 2-purchase stratum, < LR elsewhere | Semantic priors help in the sparse-data regime | A hybrid: LLM for sparse/cold categories, classical model otherwise |
| AUC good, calibration bad | It ranks well, but the probabilities are off | Cheap fix (recalibration). RL would also fix it, but it's overkill. |

The gap between the best and the average of the k samples (best-of-k vs mean-of-k Brier) is reported as RL headroom per level.

---

## 9. Steps
1. **Feasibility script** (§1, checks F1–F8). Adjust parameters once if needed, or stop if F3 and F4 both fail.
2. Generator + prompt with the nested L1/L2/L3 candidate sets. Inspect ~10 instances by eye.
3. Reward + tests.
4. Baselines (fit LR on train).
5. Eval with the existing runner: 2–3 models × 3 levels, **k = 8, N = 100 anchors on the primary eval split**, with the same anchors at every level. The cost is low (single turn, no judge), but run the cost dry run anyway.
6. Analysis with the existing pipeline, plus:
   - Brier skill vs each baseline across L1→L3, with bootstrap CIs (the difficulty plot)
   - a reliability diagram per model
   - AUC and precision@K
   - the staple and prior-purchase strata
   - the predictability terciles
   - the reward spread across k samples (quantiles)
   - examples: well calibrated / overconfident miss / a cycle the model catches that the weekly-rate baseline misses

---

## 10. Open Decisions / Assumptions
- Conditioning on ≥1 trip (buy-again shelf framing). The unconditional variant is available for the push-reminder framing.
- Commodity granularity. Sub-commodity is the fallback if F3/F4 show memoryless behavior.
- Candidates come only from the household's own history, so first-time purchases are out of scope.
- If models emit noisy or erratic decimals, switch the output to 5 bins (0.05 / 0.25 / 0.5 / 0.75 / 0.95). The cost is that it's only approximately proper.