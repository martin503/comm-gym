# Project Plan: Commerce RL Gym — Constrained Promo Cart Optimizer

## 0. Summary

**Task.** Given a household's shopping list (real categories from a real basket), a menu of real SKUs with real prices for that week, real coupon eligibility, and constraints derived from the household's own history, the model picks exactly one SKU per category so that the final out-of-pocket total is as low as possible. It also reports that total.

**Why this task.**
- **Deterministic ground truth.** An exact solver computes the optimum, so the target has zero aleatoric noise. Every bit of reward variance reflects the policy, not the data.
- **The candidate pool is part of the task.** No negative sampling is needed: the menu is the candidate set by construction.
- **Difficulty is a dial.** The number of categories, SKUs per category, and coupled coupon rules control difficulty. That lets us place models where RL has signal.
- **There is a clear heuristic gap.** Without coupled rules, greedy is optimal. Coupling (threshold bundles, brand quotas) is exactly what makes greedy fail, and we measure that.

**Design principles.**
1. **Pure-Python core, thin framework adapter.** The pricing engine, solver, and reward are plain functions with no framework imports. `verifiers` is only an adapter, which shields us from API churn.
2. **Everything is config.** Difficulty, splits, reward weights, and sampling rates come from YAML/CLI. No magic numbers live in code.
3. **Anti-hacking by construction first, penalties second.** Feasibility gating and lexicographic reward ordering do most of the work. Adversarial tests then prove the ordering holds.
4. **State what is real and what is synthetic.** Every prompt field is tagged in the generator as `real` or `synthetic`, and the slides report it.

---

## 1. Data Layer

### 1.1 Files used
| File | Use |
|---|---|
| `transaction_data.csv` | Baskets (shopping lists), observed prices and discounts, household history |
| `product.csv` | `COMMODITY_DESC`, `BRAND` (National/Private), `MANUFACTURER`, `CURR_SIZE_OF_PRODUCT` |
| `coupon.csv` | Real coupon → eligible `PRODUCT_ID` mapping, per campaign |
| `campaign_desc.csv` | Campaign `START_DAY` / `END_DAY` (which coupons are live on the target day) |
| `campaign_table.csv` | Which households were targeted by which campaign |
| `hh_demographic.csv` | Used only for split stratification (it covers a minority of households) |
| `causal_data.csv` | *Optional v2:* display/mailer flags as extra menu attributes |

The dataset lives outside the repo. Its path comes from the `CARTGYM_DATA_DIR` environment variable, and `.gitignore` excludes it.

### 1.2 Data checks (`scripts/check_data.py`), run before building anything else
Each check prints numbers and has an explicit go/no-go threshold. The outputs go into `reports/data_checks.md` and later back the slides.

- [ ] **Schema and ranges.** Column names, the `DAY`/`WEEK_NO` range (expected ≈1–711 / 1–102), household count.
- [ ] **Discount sign convention.** Confirm the sign of `RETAIL_DISC` and `COUPON_MATCH_DISC`. Derive the regular shelf price and the loyalty price per the user guide's definition, then verify `regular ≥ loyalty > 0` for ≥99% of clean rows.
- [ ] **Exclusions.** Find the fuel / kiosk / `COUPON/MISC ITEMS` commodities, rows with `QUANTITY ≤ 0` or `SALES_VALUE ≤ 0`, and quantity outliers (weight-priced items). Decide on an exclusion list.
- [ ] **Price coverage.** For each (commodity, week), and for each (store, commodity, week), count the distinct products with an observed price. *Go:* ≥50% of (commodity, week) pairs have ≥4 priced SKUs, so menus can be built from real data.
- [ ] **Within-category price spread.** The coefficient of variation of unit price within (commodity, week), and the National vs Private price premium per commodity. *Go:* enough spread that SKU choice matters.
- [ ] **Menu scope.** Commodity- vs sub-commodity-scoped menus: feasibility, within-scope price spread, and tier mix. Decides how the pack-size shortcut is avoided. *(Result 2026-10-22: sub-commodity scope adopted — see §3.1.)*
- [ ] **Coupon coverage.** The share of (commodity, week) menus that contain ≥1 SKU eligible for a live coupon (`coupon.csv` × campaign window). This decides how many coupon rules can be real rather than templated.
- [ ] **Empirical coupon values.** The distribution of `COUPON_DISC` on redeemed lines. Synthetic coupon amounts are sampled from it.
- [ ] **Household brand-tier share.** Per household, the Private-label share in Year 1, and how much it varies across households. This shows whether brand quotas can be household-specific.
- [ ] **Basket category count.** The distribution of distinct eligible commodities per basket. *Go:* enough baskets with ≥C categories for every difficulty level.
- [ ] **Household entry ramp and campaign-window cutoff.** Active households per week, plus live-campaign coverage per week; the panel must be ramped before the campaign window opens (day 224). The time-split cutoff is the campaign-window midpoint, sanity-checked against campaign density on both sides.

### 1.3 Price table (`src/cartgym/data/prices.py`)
- Build `price[product, week]` from cleaned rows: the median regular unit price, the median loyalty discount per unit, and the observation count.
- Look prices up from the target basket's `STORE_ID` first. Fall back to the chain-wide median for that week, and record which source was used in `info`.
- Keep only products with ≥`min_price_obs` observations in the week (config).

### 1.4 Size parsing (*v2, optional*)
Parse `CURR_SIZE_OF_PRODUCT` into (amount, unit) where possible. This would enable unit-price reasoning and "minimum size" constraints as an extra difficulty axis. It is excluded from v1 to keep scope tight.

---

## 2. Splits (`src/cartgym/data/splits.py`)

*Revised 2026-10-22: both axes kept — household cohorts and time — with the time axis anchored inside the coupon-active window (campaigns run days 224–719 only), not on the year boundary. Anchors are restricted to campaign-live days so every instance can carry real coupon eligibility. Household disjointness is a distribution-shift precaution, not leakage control.*

| Parameter | Default | Note |
|---|---|---|
| `--anchor_days` | campaign-live days only (≥ day 224) | instances need live coupons |
| `--cutoff_week` | from the data check (campaign-window midpoint, ~week 66–68) | early / late within the window |
| `--train_hh_ratio` | 0.8 | Stratified by early-period spend tier × has-demographics |
| `--max_instances_per_hh` | config | Stops heavy shoppers dominating |
| `--seed` | 42 | |

Splits:
- `train`: cohort A, anchor days ≤ cutoff
- `dev`: cohort B, anchor days ≤ cutoff. **All tuning happens here**: difficulty levels, trap rates, `C_ref`, generator rebalancing.
- `eval_unseen`: cohort B, anchor days > cutoff. **This is the primary eval split.** Reporting only — nothing is tuned against it.
- `eval_known`: cohort A, anchor days > cutoff (optional)

**Dedupe (across all splits).** Never sample the same anchor basket twice. Drop exact fingerprint duplicates (sorted menu product IDs + normalized coupon rules + constraints). Log the near-duplicate rate (Jaccard ≥ 0.8 on menu product sets) as a stat; promote to a hard filter only if material.

**Split balance is a first-class output.** Campaign coverage, trap rate, `C*`, coupon counts, and category mix are reported per split so eval deltas are not confounded with distribution drift.

**Shortcut policing (generator gate).** Shortcut baselines (§7) must score clearly below constraint-aware greedy on `dev` before levels are frozen. Rebalance via the synthetic rules (thresholds, quotas, coupon amounts) rather than by making menus unrealistic. *(First gate run 2026-10-22, dev n=30/level: L1 failed on always-coupon-SKU — 0.972 vs 0.904, 80% exact-opt — because empirical coupon amounts dominate sub-commodity price gaps, so the couponed SKU is almost always cheapest post-coupon. Fix: `coupon_gap_cap_prob` per level shrinks a share of flip-inducing amounts so the couponed SKU stays above the cheapest alternative by a margin that clears the near-tie band. At 0.5 all six gates pass; L1 margins stay thin (0.918 vs 0.939) and L2 separates cleanly (≤ 0.54 vs 0.95) — revisit the prob at level tuning.)*

**Generalization probes** (separate eval rows, never the main number):
- *Held-out rule template*: the manufacturer multi-buy coupon appears only in eval. Tests whether a policy reads rules or memorized templates it trained on.
- *Held-out difficulty*: train on L1–L3, evaluate on L4.
- *Held-out commodities*: ~20% of eligible commodities are eval-only. Train/dev instances contain **zero** held-out categories (excluded from category sampling, not deprioritized). The main eval set draws from the same non-held-out pool as dev, so the primary dev↔eval comparison stays clean; the held-out probe is a separate eval row that injects ≥ 1 held-out category per instance (all-held-out at C=8 is dead: 1.2% of baskets qualify).

**Leakage rules.** Household constraints are derived only from that household's transactions *before* the target day. All stratification statistics use the early period only.

**Stated assumption (to say on the slide).** Zero-shot models never see `train`; the split exists so that a future RL run trains and evaluates on disjoint households and time periods. We do not claim a known-vs-unseen gap from zero-shot results. The genuine leakage risk is *selection*: everything is tuned on `dev` and reported on a `dev`-disjoint eval.

---

## 3. Instance Generator (`src/cartgym/generator.py`)

### 3.1 Construction of one instance
1. **Anchor.** Sample a target basket `(household, basket, day, week, store)` from the split.
2. **Shopping list.** Pick `C` eligible categories from the basket. A category is eligible only if the bought product's **sub-commodity** has ≥`S` priced SKUs that week (89% of purchase lines qualify; 29% of baskets still yield ≥ 8 eligible categories, so L4 is covered). *(real)*
3. **Menu.** For each category, pick `S` SKUs **from the bought product's sub-commodity**, not the whole commodity:
   - Sub-commodity scoping keeps menu entries genuinely comparable products: commodity-level menus mix pack sizes, so "buy the smallest pack" becomes a learnable shortcut (within-pair CV drops 0.48 → 0.30 when scoped; the National premium survives at ~34%, so brand-tier economics are real, not a size artifact).
   - **Always include the product the household actually bought.** *(real)* This enables the "real shopper vs optimal" analysis in §7.
   - Fill the remaining `S−1` from sub-commodity products priced that week. Sample for a brand mix (≥1 National and ≥1 Private when available; 899 sub-commodities price both tiers) and for price spread. *(real)*
   - No fallback to commodity scope: categories that don't qualify are simply not used for that instance (logged).
   - Assign shuffled short codes per instance (e.g. `D2`) so that no ordering or ID is informative.
4. **Coupons** (all stack; at most one application per coupon):
   - **Coupon counts are fixed per level** (§3.2), so week-to-week campaign density cannot change difficulty. Real eligibility is preferred; if the live pool has no eligible SKU for the drawn coupon, the coupon is synthetic and tagged as such, and the real/synthetic share is logged per split.
   - **SKU coupons**: real eligibility from `coupon.csv` for campaigns live on `day`, preferring campaigns the household was targeted by. *(eligibility real; amount sampled from the empirical `COUPON_DISC` distribution)*
   - **Threshold bundles**: "$X off if spend on {commodity A, commodity B} ≥ $T". *(synthetic template)* `T` is placed so the threshold is reachable but not by the cheapest SKUs, which is what creates coupling.
   - **Manufacturer multi-buy** (*optional*): "$X off when buying ≥2 items from manufacturer M". *(real manufacturer IDs, synthetic rule)*
5. **Household constraints:**
   - **Brand-tier quota**: "≥ q items must be Private label" (or National), with `q` derived from the household's historical share × `C`, rounded. *(derived from real history)*
   - **Loyal SKU** (optional): if the household bought the same product in ≥`loyalty_threshold` of its purchases in a commodity, require that product. *(derived from real history)* Such a category has no free choice, but its price still feeds thresholds and quotas.
   - **No negative "never buys X" constraints.** Absence over a few trips is weak evidence.
6. **Solve** (§4), then apply the acceptance filters (§3.3).
7. **Serialize** the prompt (§3.4) and an `info` dict with the full instance, optimum, cost distribution stats, difficulty features, the household's real cart cost, and real/synthetic provenance tags.

### 3.2 Difficulty levels (config)
| Level | C (categories) | S (SKUs/cat) | Threshold bundles | SKU coupons | Brand quota | Search space |
|---|---|---|---|---|---|---|
| L1 | 4 | 3 | 0 | 1–2 | no | 81 |
| L2 | 5 | 4 | 1 | 2–3 | yes | 1,024 |
| L3 | 6 | 4 | 2 | 2–4 | yes | 4,096 |
| L4 | 8 | 5 | 3 | 3–5 | yes | 390,625 |

The levels get tuned on `dev` after the first model sweep. The goal is a spread where at least one model sits in the ~30–70% exact-optimal band.

### 3.3 Acceptance filters
- ≥1 feasible cart.
- **Tie handling**: every cart with `cost ≤ C* + ε` counts as optimal (`ε = $0.01`). Reject the instance if the best non-optimal cart is within `δ` of `C*` (`δ = $0.10`, config), so that near-ties don't produce noisy labels.
- **Greedy-trap stratification**: compute the greedy-cheapest and greedy-max-discount baselines. Each instance is tagged `trap` (greedy infeasible or suboptimal) or `no_trap`. Sample to a configured trap rate per level (e.g. 70%). Results are always reported separately per stratum.
- Log the difficulty features: `n_carts`, `n_feasible`, `n_binding_rules` (rules active in the optimum), `greedy_gap`, `C*`, `C_ref`.

### 3.4 Prompt format (`src/cartgym/prompts.py`)
- **System**: role, pricing rules (shelf price − loyalty discount − applicable coupons; all coupons stack; round to cents only at the end), and the output contract.
- **User**: the shopping list, the menu as a compact table (`code | commodity | brand tier | manufacturer | size | price | loyalty disc`), coupons, and constraints.
- **Output contract**: free reasoning, then **exactly one** `<answer>{"cart": {"<commodity>": "<code>", ...}, "total": 12.34}</answer>`.
- **Measure tokens per level** (tiktoken plus the Qwen tokenizer) and log them.

---

## 4. Pricing Engine and Solver

### 4.1 `src/cartgym/pricing.py`
The single source of truth for `cost(cart, instance) -> (total, breakdown)`. The solver, the reward, the baselines, and the tests all call this function.

### 4.2 `src/cartgym/solver.py`
- **Vectorized NumPy brute force** over all `S^C` carts (≤ ~400k at L4). It returns the full cost and feasibility arrays, not just the argmin. The full distribution feeds `C_ref`, the tie checks, and random-baseline statistics.
- **Cross-check** on 1k random instances against a naive `itertools` implementation, and optionally against OR-Tools CP-SAT for L4.
- **Hard cap**: if `S^C` exceeds `max_brute_force` (config), switch to CP-SAT.

---

## 5. Reward (`src/cartgym/reward.py`)

### 5.1 Parsing
- Exactly one `<answer>...</answer>` block. Zero or several blocks mean a parse failure.
- Valid JSON. `cart` maps every required commodity to exactly one menu code. `total` is numeric.

### 5.2 Components (all pure functions, logged individually)
- `parse_ok ∈ {0,1}`
- `frac_constraints`: the fraction of constraints satisfied. These include: every category covered, codes in the menu, the code matching its category, the brand quota, and the loyal SKU.
- `feasible = parse_ok ∧ all constraints satisfied`
- `opt = clip((C_ref − cost) / (C_ref − C*), 0, 1)`, where `C_ref` is the **median feasible cart cost** (config). A random feasible cart scores ~0 about half the time. `opt = 1` iff `cost ≤ C* + ε`.
- `price_ok = |total − cost| ≤ $0.01`. It only counts when `feasible`.

### 5.3 Total (lexicographic by construction)
```
if not parse_ok:        R = 0
elif not feasible:      R = w_partial * frac_constraints               # w_partial = 0.3
else:                   R = w_feasible + w_opt * opt + w_price * price_ok   # 0.5 + 0.4 + 0.1
```
**Invariant (tested):** `max R(infeasible) < min R(feasible)`, i.e. `w_partial < w_feasible`. This holds for any number of constraints, without relying on weight arithmetic.

### 5.4 Logged metrics (weight 0 in the verifiers Rubric)
`parse_ok`, `feasible`, `opt`, `exact_opt`, `price_ok`, `n_violations`, `violation_types`, `cost_gap_$`, `cost_gap_%`.

---

## 6. Tests (`tests/`)

### 6.1 Pricing and solver
- Hand-computed instances with known totals, covering each coupon type, stacking, and threshold edges (exactly at `T`, one cent below).
- Brute force vs `itertools` vs CP-SAT agreement.
- **Menu-shuffle invariance**: permuting the menu order and codes leaves the optimum cost unchanged.

### 6.2 Reward adversaries (`test_reward_hacking.py`)
| Adversary | Expected |
|---|---|
| Oracle (solver argmin, correct total) | R = 1.0 |
| Oracle cart with wrong total | R = 0.9 |
| Total fudged to look under budget / cheaper than real | `price_ok = 0` |
| Code not in the menu | infeasible |
| Two SKUs in one category / missing category | infeasible |
| Code assigned to the wrong category | infeasible |
| Multiple `<answer>` blocks (hedging) | R = 0 |
| No answer block / malformed JSON / JSON outside tags | R = 0 |
| Always the first SKU listed per category | ≈ random; no positional leak |
| Greedy-cheapest, greedy-max-discount | below oracle on `trap` instances |
| Random valid cart | `opt` distribution centered ≈ 0 |

### 6.3 Property tests (`hypothesis`)
- `R ∈ [0, 1]` for arbitrary strings.
- `R(infeasible) < R(feasible)` for all generated instances.
- Generator determinism: same seed → identical instances.

---

## 7. Baselines (`src/cartgym/baselines.py`)
Run through the **same reward function** and saved in the same rollout format.
1. **Random valid cart**: one SKU per category, ignoring constraints.
2. **Greedy-cheapest**: the cheapest net price per category, ignoring quotas and thresholds.
3. **Greedy-max-discount**: the largest discount per category.
4. **Constraint-aware greedy**: cheapest first, then repair the brand quota by smallest premium. This is the strongest simple heuristic; the LLM needs to beat it on `trap` instances.
5. **Shortcut baselines** *(added 2026-10-22)*: always-Private, always-the-couponed-SKU, always-lowest-shelf-price-ignoring-loyalty. These police the generator: each must score clearly below constraint-aware greedy on `dev` (gate before levels are frozen), and the table is reported permanently.
6. **Real shopper**: the household's actual purchased SKUs, priced under the same rules. This yields a data-backed stat: *"money left on the table"* by real shoppers, measured against `C*`.
7. **Oracle**: the solver. This is a sanity check that reward = 1.

---

## 8. Environment Adapter (`src/cartgym/env.py`)
- `load_environment(level, split, n, seed)` returns a `verifiers` environment, single-turn, with the Rubric wrapping `reward.total` (weight 1) and the logged metrics (weight 0).
- **Pinned `verifiers==0.3.1`** *(2026-10-22; eval-only usage, training integration deferred)*. It accepts our `openai>=3.x`; 0.4.0 would force `openai<3`. Adapter notes for the pinned API: dataset rows need a `prompt` column (Messages) plus arbitrary context columns, which the Rubric passes to reward funcs as kwargs matched by parameter name; `system_prompt` is prepended at dataset build; **individual reward funcs must return `float`** — a dict return is force-floated and silently scores 0 — so each logged metric is its own weight-0 func.
- **Our own `run_eval.py` writes our own JSONL** (below), so the saved rollouts do not depend on the library's output format.

---

## 9. Evaluation (`scripts/run_eval.py`)

### 9.1 Models
- **API lineup (2026-10-23): `openai/gpt-6-luna` only.** `qwen/qwen3.7-flash` was tried as the cheap tier and dropped: at `max_tokens=2048` it spent all 2048 tokens on reasoning with an empty completion (0/20 parseable), at ~37 s/rollout — slow and effectively more expensive per usable rollout. To revive it: a larger completion budget or thinking disabled via `extra_body`.
- **Locked sweep protocol (2026-10-23, dev dry runs): temperature 1.0, `reasoning_effort=low`, `max_tokens=8192`.** At default effort + 2048 tokens the L3/L4 headlines (45%/10% exact) were truncation artifacts — every parse failure sat at exactly 2048/2048 output tokens while parsed rollouts went 9/9 exact at L3. Under the locked protocol luna lands at **95% / 55% / 55% / 35% exact-optimal (L1–L4)** with zero parse failures; failures are suboptimal-feasible (mean gaps 11–135¢), quota violations at L2/L4, and a few price-arithmetic slips at L3/L4 — L2–L4 sit in the 30–70% band. Protocol sensitivity is real and reported: L2 moves 95%→55% between default-effort and low-effort runs.
- **Local**: a current small Qwen3.x instruct model on vLLM on one 3090. This also demonstrates the open-weight path RL would actually train.

### 9.2 Protocol
- Per model, per level: `N` instances from `eval_unseen` (e.g. 100), with **k = 8** rollouts each.
- **Sampling temperature 1.0** for models that accept it, matching typical RL sampling. Reasoning models may not expose temperature; record their sampling params as given.
- **Budget dry run first**: 10 instances × k = 2 per model and level. Measure input, output, and reasoning tokens, extrapolate cost, and size `N` to stay within the key limit with a safety margin. Log cost per rollout.
- Retries with backoff. Failed API calls are logged as such and **excluded** from reward statistics, never scored as 0.

### 9.3 Rollout record (`rollouts/<model>/<split>_<level>.jsonl`)
`instance_id, level, stratum(trap/no_trap), model, sampling_params, rollout_idx, prompt, completion, parsed_answer, reward, components{...}, cost, C*, tokens{in,out,reasoning}, latency, seed, git_sha`

---

## 10. Analysis (`scripts/analyze.py`)
For each task × level × stratum × model:
- **Mean reward** with a 95% bootstrap CI over instances (resampling instances, not rollouts).
- **Exact-optimal rate**, i.e. pass@1, and **pass@k** for k ∈ {1, 4, 8} with the unbiased estimator.
- **Within-instance std**, plus a **variance decomposition** (between-instance vs within-instance share).
- **Zero-variance group fraction**: instances where all k rollouts get an identical reward, which give no GRPO advantage. This is the key RL-relevance number per level.
- **Feasibility rate** and **price-report accuracy**, kept separate from optimality.
- **Automated failure taxonomy** from the components: parse error / missing category / quota violated / threshold missed (feasible but a binding bundle was not triggered) / arithmetic error / suboptimal-feasible.
- **Reward vs difficulty curve** per model, with baselines overlaid.
- Example selection: a success, a near-miss (feasible, `opt` between 0.7 and 1), and characteristic failures per taxonomy class, each with a link to its rollout record.

---

## 11. Repository Layout
```
cartgym/
├── pyproject.toml            # uv; verifiers pinned
├── README.md                 # install, data setup, rerun small eval (L1, N=10, k=2)
├── configs/                  # levels.yaml, splits.yaml, reward.yaml, eval.yaml
├── src/cartgym/
│   ├── data/{load.py, clean.py, prices.py, splits.py}
│   ├── generator.py
│   ├── pricing.py
│   ├── solver.py
│   ├── reward.py
│   ├── prompts.py
│   ├── baselines.py
│   └── env.py
├── scripts/{check_data.py, build_splits.py, generate.py, run_eval.py, run_baselines.py, analyze.py}
├── tests/{test_pricing.py, test_solver.py, test_reward_hacking.py, test_properties.py, test_generator.py}
├── rollouts/                 # committed: saved rollouts behind the reported results
└── reports/                  # data_checks.md, results tables, figures
```

---

## 12. Build Order (each step gated by the previous one)
1. `check_data.py`: run all §1.2 checks and decide go/no-go and the exclusion list.
2. `pricing.py` + `solver.py` + their tests.
3. `generator.py` at L1–L2, then inspect 20 instances by hand.
4. `reward.py` + adversary and property tests.
5. Baselines on `dev`, to verify that greedy fails on `trap` instances as designed.
6. Env adapter, plus the README small-eval path working end to end.
7. Budget dry run, then tune the levels on `dev` with the cheapest model.
8. Full eval on `eval_unseen`, then analysis.
9. Slides.

---

## 13. Slide Mapping (≤ 5)
1. **Data → task**: what is real vs synthetic, how instances are built, the split diagram, and key data-check numbers.
2. **Reward and anti-hacking**: lexicographic structure, the adversary table, and the greedy-trap rate per level.
3. **Results**: reward vs difficulty per model with baselines, CIs, and the trap/no-trap split. Include the real-shopper "money left on the table" stat.
4. **Rollouts**: a success, a near-miss, and characteristic failures with the taxonomy breakdown.
5. **RL recommendation**: which level and model to train (zero-variance fraction, pass@8 − pass@1 headroom), the top remaining hacking risks, and what to change next.

---

## 13b. Results — full zero-shot eval (2026-10-23, `eval_unseen`, n=100/level, k=8)

`openai/gpt-6-luna`, temp 1.0, `reasoning_effort=low`, `max_tokens=8192`. 3,200 rollouts, 0 API failures, **$1.52 total spend** (of the $10 key cap; dev dry runs added ~$0.15).

| level | mean reward [95% CI] | pass@1 | pass@4 | pass@8 | feasible | price ok | zero-var inst |
|---|---|---|---|---|---|---|---|
| L1 | 0.996 [0.994, 0.998] | 97% | 100% | 100% | 100% | 98% | 77% |
| L2 | 0.943 [0.929, 0.955] | 69% | 97% | 100% | 97% | 90% | 7% |
| L3 | 0.945 [0.934, 0.955] | 64% | 95% | 98% | 97% | 87% | 7% |
| L4 | 0.915 [0.898, 0.930] | 47% | 80% | 86% | 94% | 78% | 3% |
| L4 (traps) | 0.891 [0.871, 0.910] | 38% | 72% | 80% | 91% | 72% | 1% |

- **L2–L4 sit in the 30–70% pass@1 band** — the level-design goal, at the level the sweep was tuned for. L4 traps (38%) are the deepest point; pass@8 86% shows the optimum is reachable but not reliable — the RL-relevant regime.
- **Zero-variance fraction collapses from 77% (L1) to ≤7% (L2–L4)** — L2–L4 give GRPO-style advantage signal on nearly every instance; L1 is warm-up only.
- Failure taxonomy is level-graded with **zero parse failures anywhere**: suboptimal-feasible dominates and grows (24 → 201 → 225 → 301), arithmetic (price-report) slips grow with menu size (12 → 55 → 84 → 130), quota violations appear from L2 (22–50).
- Baseline anchor (dev): constraint-aware greedy 0.94–0.95 mean reward, 37–50% exact — luna's L4 pass@1 (47%) sits right at that anchor; the LLM needs the trap stratum (38%) to differentiate.

## 14. Assumptions and Open Decisions
- **Objective = minimize out-of-pocket total** under hard constraints. Alternative, kept ready as a config switch in case "an assumption changes" onsite: *maximize a household preference score subject to a budget cap*. That turns it into a knapsack and uses history more heavily.
- **`C_ref` = median feasible cost.** This is the normalization for `opt`. The alternative is the worst feasible cart, which compresses scores upward. Decide on `dev` by looking at the baseline distributions.
- **Coupon amounts and threshold rules are synthetic.** Eligibility, prices, brands, and shopping lists are real. Say this explicitly.
- **Store-level vs chain-level pricing.** The choice depends on the price-coverage check.
- **Reasoning visibility.** Free-form reasoning is allowed and not scored. Only the `<answer>` block is graded, so no judge is needed.

---

## 15. Deferred: Phase 2 (after Phase 1 is complete)
- **Best-of-N pressure test.** Sample N = 32–64 per instance from the local model and pick the argmax under (a) a naive reward (e.g. `frac_constraints + opt` without gating) and (b) the full reward. Show what the naive argmax exploits.
- **Optional GRPO PoC** on 2×3090 (vLLM on one GPU, LoRA trainer on the other) using `train` at the level recommended on slide 5. This is out of scope for the assignment and kept separate from the submission.
