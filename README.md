# comm-gym

Commerce RL gym built on the Dunnhumby Complete Journey dataset.

First task: constrained promo cart optimizer — see `cart_optimizer_plan.md`.

## Setup

```bash
uv sync
```

The dataset is expected in `data/` (gitignored) or behind `CARTGYM_DATA_DIR`.

## Data checks

```bash
uv run python scripts/check_data.py
```

Writes `reports/data_checks.md` with go/no-go verdicts per check.
