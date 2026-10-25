# Dropped tasks: replenishment and refund

Card on the two tasks that did not make it into the gym, and why. Both decisions follow the
project's pre-registered feasibility discipline: the pass rule is written down before the
run and applied verbatim, including the failure branch — on failure, drop the task.

## Replenishment — failed feasibility, never built

**What it would have been.** Next-week repurchase prediction: given a household's 98-day
purchase history, predict which of its candidate commodities (bought at least twice in the
window) it will buy in the next 7 days — one probability per (household, anchor day,
commodity) pair, Brier-scored. Commerce motivation: replenishment timing is the signal
behind subscribe-and-save, "buy it again" placements, and out-of-stock nudges.

It was dropped **at the feasibility stage**: no prompt, reward, or instance code was ever
written. What remains — `src/commgym/replenish/` and `scripts/replenish/feasibility.py` —
is the reproducible evidence generator and nothing else.

**Pre-registered rule** (fixed before the recheck run; both must hold on the stratum of
commodities with ≥ 4 prior purchases):

- **R1** — is there a purchase cycle at all? `P(buy | due in window) ≥ 1.5 × P(buy | due
  after window)`.
- **R2** — is it extractable beyond frequency? Logistic regression with timing features
  (days since last, mean interval, interval std, …) must beat the weekly-rate baseline by
  ≥ +3% Brier skill, CI > 0 (10,000-resample cluster bootstrap).

**Result** (dev, 45,886 pairs in the stratum, of 120,339 total; 481,723 train pairs):

- R1 **passed**: 50.1% vs 32.0% → ratio 1.56 (bar 1.50).
- R2 **failed**: **+2.05% [+1.65, +2.45]** — the CI sits entirely below the +3% bar.

Baseline Brier scores on dev: constant 0.1825, weekly rate 0.1640, logistic regression
0.1625.

**Interpretation.** Repurchase in this dataset is frequency-driven. A cycle signal exists
but only among frequent purchasers (5+ purchases: 54.8% buy when due vs 27.7% when not —
a real ~2× lift), and in aggregate it buys only 1–2% Brier skill. Two rescue directions
were tried *before* the rule ran and both failed: the initial run's overdue gate failed
outright (overdue items were bought *less* — 20.0% vs 28.5% for recently-bought — the
opposite of replenishment), and the sub-commodity variant didn't help (+1.28% skill). An
LLM predicting next-week baskets would mostly be re-deriving the weekly rate: no headroom
for a policy to learn.

**Cost of finding out:** one day, local classical ML only, zero API spend
(`experiments/261023_replenish_feasibility/`, 3 reports).

## Refund — feasible, fully built, closed as saturated

**What it is.** Customer-support refund adjudication: given the purchase and filing days,
a per-case policy block (return window, price tolerance, price-match scope, refund cap), a
receipt table, the live coupons, and a customer message with ~3 claims, the model outputs
one entry per claim — line, approve/reject, one of 8 reason codes (`OUTSIDE_WINDOW`,
`NOT_ON_RECEIPT`, `NEEDS_CLARIFICATION`, `NOT_ELIGIBLE`, `PRICE_MATCH`, `WITHIN_TOLERANCE`,
`MISSED_COUPON`, `ALREADY_APPLIED`), and a refund amount. Ground truth is programmatic
(precedence-ordered rules; price tolerance frozen at 5c by feasibility), never judged.
Reward: per-claim decision/line/reason/refund scored, averaged over claims; any parse
failure is 0.

**The version history — three attempts to escape a circular design:**

| version | what changed | eval (L1/L2/L3) | verdict |
|---|---|---|---|
| v1 | fixed policy; claims rendered from a frozen word map | 1.000 / 1.000 / 0.996 | saturated at birth; rule parser also 1.000 |
| v2 | per-anchor policy sampling + contradicting dollar figures in messages | 0.950 / 0.975 / 0.979 | still saturated |
| v3 | ambiguity injection (NEEDS_CLARIFICATION claims, same-line claims) | 0.838 / 0.787 / 0.800 | finally non-saturated — for the wrong reason |
| v4 | LLM-written claims + two-reader verification (the pivot) | 0.990 (L2, full) | valid — and near-solved |

**Why the map approach didn't work (v1–v3).** The truth labels derived from the same
frozen word map that generated the claim wording — circular by construction. A rule parser
using that map scored 1.000/0.999 (it shared the label source, so the "language layer" was
a deterministic lookup with no headroom). The map was also closed-vocabulary: 420 curated
words, ~87% receipt-line coverage, and a hand audit of v3's dry-run failures reclassified
three links as outright label errors (cookies→CRACKERS, whipped cream→MILK BY-PRODUCTS,
milk→ICE CREAM). v3's apparent difficulty was wording collisions, not reasoning.

**The 2026-10-24 pivot (v4).** Claim texts are written by claude-haiku-5.5; two
independent readers (haiku + deepseek-v4.1-flash-1017 — neither is the eval model
gpt-6-luna) must each resolve every item reference to exactly the intended receipt line or
the anchor is discarded (~75% render survival). Leak checks bar line codes, coupon codes,
and unshown dollar amounts. The word map survives only as the rule parser's own
vocabulary — finally a fair non-LLM baseline. Rewards stay programmatic; no judge.

**Final numbers (v4, eval_unseen L2, 100 instances × 8 attempts, gpt-6-luna):**

- mean reward **0.990 [0.983, 0.996]**, pass@1 **97%**, parse **100%**, zero-variance
  **85%**, within-instance SD **0.018**;
- of 1,600 claims: 1,577 fully correct; 12 wrong decisions (0.8%, mostly
  PRICE_MATCH↔WITHIN_TOLERANCE boundary math) and 10 refund-arithmetic slips; **0 false
  approvals**; mean refund error 1.1c;
- dev 0.991 — no unseen-anchor gap; rule parser 66% vs model 99% (the model's +42% on
  uniquely-referencing claims is exactly the natural-language resolution the parser can't
  do);
- the pre-set saturation gate ("mean ≥ 0.95 at every level") **TRIGGERED**; a
  qwen3.8-27b dry run returned a perfect 1.000 (20/20 parse) and was skipped as redundant.

**Why dropped.** A valid task that zero-shot models already solve: ~1% headroom, 85% of
instances give the identical reward on every attempt — no gradient for RL. And the L1→L3
level ladder (1-, 2-, 3-claim prefixes) never produced a difficulty gradient in *any*
version — v1 1.000/1.000/0.996, v2 0.950/0.975/0.979, v3 0.838/0.787/0.800, v4 dry
0.988/0.950/0.967 — flat or inverted at every sample size; the level dimension was
decoration, not a lever, and evaluation was narrowed to L2. Total task spend ~$2.4 of the
API budget.

**What survived.** The v4 artifacts are complete and retained: instances, rollouts and
reports (`refund_*_v4`) at 100 per level × L1–L3 × train/dev/eval_unseen — the only train
instances in the repo. The always-reject baseline's FAIL (0.310, outside the pre-registered
[0.15, 0.20] band) stays recorded as-is. The G5 breadth shortfall is disclosed as a
selection effect, not a gate: anchors require ≥ 3 ladder-resolvable targets, so selected
baskets (12.6 mean lines, 1.76 missed coupons) differ from all baskets (8.5, 1.12).

## What admission to the gym requires (the lessons)

1. **Pre-registration is cheap and it works.** Replenishment was killed in a day with zero
   API spend by a rule fixed before the run. The tempting case — R1 passed, R2's point
   estimate positive with CI > 0, just 1pp short — is exactly the marginal scenario
   pre-registration exists to police.
2. **Feasibility ≠ viability.** Refund passed every validity gate and still died — of
   saturation. Admission needs *headroom* evidence (zero-shot models below ceiling, reward
   varying across attempts at the same instance), not just correctness evidence.
3. **Label provenance must not be circular.** When the mechanism that writes the examples
   also defines their labels, measured difficulty is artifact: v3's 0.79–0.84 was
   substantially label noise; clean labels showed ~1% headroom.
4. **Difficulty levers must be measured, not assumed.** The level ladder was designed to
   ladder difficulty and measured flat in four consecutive versions before being
   abandoned.

Evidence: `experiments/261023_replenish_feasibility/` (replenish, 3 reports),
`experiments/261023_refund_feasibility/` + `experiments/261024_llm_text_gen/` (refund
feasibility + v4 render caches), `reports/refund/refund_eval_report_v4.md` (final numbers).
