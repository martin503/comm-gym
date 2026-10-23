# comm-gym

Commerce RL gym built on the Dunnhumby Complete Journey dataset.

First task: constrained promo cart optimizer — see `cart_optimizer_plan.md`.

## Setup

```bash
uv sync
```

The dataset is expected in `data/` (gitignored) or behind `COMMGYM_DATA_DIR`.

## Layout

`src/commgym/` is layered: `core/` (task-agnostic eval infra: OpenRouter client,
async rollout runner, stats), `dunnhumby/` (dataset access: loaders, cleaning,
splits, price tables), and one subpackage per task — `cartopt/` today, more later.
Scripts mirror this: `scripts/check_data.py` and `scripts/build_splits.py` are
dataset-level; task scripts live under `scripts/<task>/` (e.g. `scripts/cartopt/`)
with artifacts in `instances/<task>/`, `rollouts/<task>/`, and `configs/<task>/`.

## Data checks

```bash
uv run python scripts/check_data.py
```

Writes `reports/data_checks.md` with go/no-go verdicts per check.
