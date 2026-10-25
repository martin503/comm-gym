# comm-gym

Commerce RL gym built on the [dunnhumby Complete Journey](https://www.dunnhumby.com/source-files/)
grocery panel: gradeable, reward-hack-resistant LLM tasks with programmatic and judge based rewards, for evaluating and training policies.

## Repository overview

```
src/commgym/
  core/       task-agnostic infra: OpenRouter client, async rollout runner,
              sweep driver, stats, configs
  dunnhumby/  dataset layer: loaders, cleaning, splits, campaign calendar
  cartopt/    cart optimization: instances, exact solver, pricing, reward
  offer/      grounded offer messages: grounding gate, lexicon, reward
  refund/     refund adjudication (closed as saturated; kept for reproducibility)
  replenish/  replenishment feasibility evidence generator (task never built)
scripts/
  check_data.py, build_splits.py        dataset-level checks and reports
  <task>/generate.py                    build instances from ./data (seeded)
  <task>/run_eval.py                    rollouts via OpenRouter (dry-run first)
  <task>/run_baselines.py               programmatic baselines (oracle, rules, templates)
  <task>/analyze.py                     report tables → reports/<task>/
  offer/generate_references.py          reference messages for the judge
  offer/judge.py, judge_check.py        pairwise judging + judge reliability checks
configs/     splits.yaml + per-task task/reward/models yaml (judge.yaml for offer)
docs/        task cards and design docs
reports/     generated reports (committed)
data/        raw dunnhumby CSVs (gitignored; not needed to run published instances)
instances/   task instances (gitignored; hosted on HuggingFace — below)
rollouts/    eval rollouts  (gitignored; hosted on HuggingFace — below)
experiments/ dated experiment dirs (gitignored)
```

## Setup

Requires Python 3.12 and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
```

Live rollouts and judging call OpenRouter: put `OPENROUTER_API_KEY=...` in a `.env` at the repo
root (override with `--env-file`). Which models run, and with what sampling parameters, is set
per task in `configs/<task>/models.yaml`; the offer judge is configured in
`configs/offer/judge.yaml`.

## Getting the data

### Original dunnhumby dataset — only needed to generate new instances

1. Register at the [dunnhumby source files page](https://www.dunnhumby.com/source-files/) and
   download **The Complete Journey** zip under their license terms.
2. Unzip the eight CSVs into `data/` at the repo root (or point `COMMGYM_DATA_DIR` elsewhere):
   `campaign_desc.csv`, `campaign_table.csv`, `causal_data.csv`, `coupon.csv`,
   `coupon_redempt.csv`, `hh_demographic.csv`, `product.csv`, `transaction_data.csv`.
3. Sanity-check: `uv run scripts/check_data.py` writes `reports/data_checks.md` (per-check
   GO/no-go verdicts); `uv run scripts/build_splits.py` writes `reports/splits_summary.md`.

Running an eval on the published instances (below) does **not** need the raw dataset — only
`generate.py` does.

### Instances and rollouts — HuggingFace

Instance and rollout artifacts live at
[`m6rtine/comm-gym`](https://huggingface.co/datasets/m6rtine/comm-gym) (cartopt and offer; the
dropped refund task's artifacts are not published). The dataset layout mirrors the local
conventions: `<task>/instances/...` maps to `instances/<task>/`, and
`<task>/rollouts/<model>/<split>_<level>.jsonl` (plus offer `*.judged.jsonl` sidecars) maps to
`rollouts/<task>/...`.

Download with the hub CLI (public dataset, no token needed; run without `uvx` if you have
`hf` installed):

```bash
# everything for one task (instances + all rollouts)
uvx --from huggingface_hub hf download m6rtine/comm-gym --repo-type dataset \
  --include "cartopt/*" --local-dir hf-dl
mkdir -p instances/cartopt rollouts/cartopt
mv hf-dl/cartopt/instances/* instances/cartopt/
mv hf-dl/cartopt/rollouts/*  rollouts/cartopt/

# or just the instances needed to run an eval
uvx --from huggingface_hub hf download m6rtine/comm-gym --repo-type dataset \
  --include "offer/instances/*" --local-dir hf-dl
mkdir -p instances/offer && mv hf-dl/offer/instances/* instances/offer/
```

## Running a task

Every task follows the same pipeline under `scripts/<task>/`:

1. **`generate.py`** — build instances from `./data` (seeded, reproducible). Only needed for
   new splits/levels/counts; published instances come from HF.
2. **`run_eval.py`** — rollouts through OpenRouter. **Always `--dry-run` first**: it clamps to
   ≤10 instances × 2 rollouts and prints a cost projection. A full sweep is 100 × 8 per level
   (cartopt) or 50 × 8 (offer); `--n/--k` scale it. Common flags:
   `--split dev|eval_unseen|eval_known`, `--levels L1,L2,...`, `--models <subset>` of the
   configured models. Runs are resume-safe:
   existing rollout records with matching sampling params are skipped, so a crashed sweep
   continues where it stopped. Cost is fetched live and shown on the progress bar.
3. **offer only — `judge.py`** (after `generate_references.py` once per instance set): pairwise
   judging of gate-passed rollouts against stored references, writing `.judged.jsonl` sidecars
   (also resume-safe). `judge_check.py` re-verifies judge reliability.
4. **`analyze.py`** — regenerates the report tables into `reports/<task>/`.
5. **`run_baselines.py`** — programmatic baselines (oracle, rule parser, templates; no API).

```bash
# cartopt
uv run scripts/cartopt/run_eval.py --models openai/gpt-6-luna --dry-run
uv run scripts/cartopt/run_eval.py --models openai/gpt-6-luna --split eval_unseen --levels L1,L2,L3,L4
uv run scripts/cartopt/analyze.py --models openai/gpt-6-luna --split eval_unseen   # → reports/cartopt/eval_report.md

# offer
uv run scripts/offer/run_eval.py --models openai/gpt-6-luna --dry-run
uv run scripts/offer/run_eval.py --models openai/gpt-6-luna --split eval_unseen
uv run scripts/offer/judge.py --split eval_unseen
uv run scripts/offer/analyze.py --models openai/gpt-6-luna --split eval_unseen     # → reports/offer/offer_eval_report.md
```

Cost ballparks at the configured params (gpt-6-luna): a full cartopt sweep ≈ $1.5, offer
sweep + judging ≈ $3.5.


