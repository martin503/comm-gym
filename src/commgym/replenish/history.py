from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd

from commgym.replenish.config import TaskConfig

PAIR_COLUMNS = (
    'household',
    'anchor_day',
    'commodity',
    'y',
    'n_prior',
    'weekly_rate',
    'days_since_last',
    'mean_interval',
    'interval_std',
    'staple',
    'hh_trip_rate',
)


@dataclass(frozen=True, slots=True)
class HouseholdHistory:
    household: int
    trip_days: np.ndarray  # sorted unique days with at least one purchase
    commodity_days: Mapping[str, np.ndarray]  # commodity -> sorted unique purchase days


@dataclass(frozen=True, slots=True)
class DaySupply:
    grid: np.ndarray
    hist_trips: np.ndarray
    window_trips: np.ndarray
    n_eligible: np.ndarray  # commodities with at least min_purchases history trips


def build_histories(txc: pd.DataFrame, granularity: str) -> dict[int, HouseholdHistory]:
    """Collapse cleaned transactions to per-household trip days and purchase days."""
    txc = txc[txc[granularity].str.strip() != '']
    trips = txc.groupby('household_key')['DAY'].agg('unique').reset_index()
    purchases = (
        txc.groupby(['household_key', granularity])['DAY']
        .agg('unique')
        .reset_index()
        .rename(columns={granularity: 'category'})
    )
    commodity_days: dict[int, dict[str, np.ndarray]] = {}
    for household, category, days in zip(
        purchases['household_key'], purchases['category'], purchases['DAY'], strict=True
    ):
        commodity_days.setdefault(int(household), {})[str(category)] = np.unique(days)
    return {
        int(household): HouseholdHistory(
            int(household), np.unique(days), commodity_days[int(household)]
        )
        for household, days in zip(trips['household_key'], trips['DAY'], strict=True)
    }


def anchor_grid(
    cfg: TaskConfig, side: Literal['train', 'eval'], cutoff_day: int, last_day: int
) -> np.ndarray:
    """Valid anchor days: train history reaches day 1, no target window crosses the cutoff."""
    if side == 'train':
        return np.arange(cfg.history_days + 1, cutoff_day - cfg.horizon_days + 2, dtype=np.int64)
    return np.arange(cutoff_day + 1, last_day - cfg.horizon_days + 2, dtype=np.int64)


def counts_in_window(
    days: np.ndarray, grid: np.ndarray, start_offset: int, end_offset: int
) -> np.ndarray:
    """For each anchor d in grid, count entries t with d + start_offset <= t <= d + end_offset."""
    hi = np.searchsorted(days, grid + end_offset, side='right')
    lo = np.searchsorted(days, grid + start_offset, side='left')
    return hi - lo


def day_supply(hh: HouseholdHistory, grid: np.ndarray, cfg: TaskConfig) -> DaySupply:
    """Per anchor day: history trip count, horizon trip count, and eligible candidate count."""
    hist_trips = counts_in_window(hh.trip_days, grid, -cfg.history_days, -1)
    window_trips = counts_in_window(hh.trip_days, grid, 0, cfg.horizon_days - 1)
    eligible = np.zeros(len(grid), dtype=np.int64)
    for days in hh.commodity_days.values():
        counts = counts_in_window(days, grid, -cfg.history_days, -1)
        eligible += counts >= cfg.min_purchases
    return DaySupply(grid, hist_trips, window_trips, eligible)


def sample_anchors(
    supply: DaySupply,
    cfg: TaskConfig,
    *,
    household: int,
    min_candidates: int,
    max_anchors: int,
    seed: int,
) -> np.ndarray:
    """Seeded greedy draw of qualifying days, kept at least horizon_days apart."""
    ok = (
        (supply.hist_trips >= cfg.min_history_trips)
        & (supply.n_eligible >= min_candidates)
        & (supply.window_trips > 0)
    )
    candidates = supply.grid[ok]
    rng = np.random.default_rng([seed, household])
    picked: list[int] = []
    for day in rng.permutation(candidates):
        day = int(day)
        if all(abs(day - other) >= cfg.horizon_days for other in picked):
            picked.append(day)
        if len(picked) >= max_anchors:
            break
    return np.array(sorted(picked), dtype=np.int64)


def extract_pairs(hh: HouseholdHistory, anchors: np.ndarray, cfg: TaskConfig) -> pd.DataFrame:
    """One row per (anchor day, eligible commodity): history features, horizon label."""
    rows: list[tuple[int, int, str, int, int, float, int, float, float, bool, float]] = []
    for anchor in anchors:
        d = int(anchor)
        single = np.array([d])
        hist_trips = int(counts_in_window(hh.trip_days, single, -cfg.history_days, -1)[0])
        assert hist_trips > 0, f'anchor {d} of household {hh.household} has no history trips'
        n_weeks = (d - 2) // 7 - (d - 1 - cfg.history_days) // 7 + 1
        for commodity, days in hh.commodity_days.items():
            lo = int(np.searchsorted(days, d - cfg.history_days, side='left'))
            hi = int(np.searchsorted(days, d - 1, side='right'))
            if hi - lo < cfg.min_purchases:
                continue
            hist = days[lo:hi].astype(np.int64)
            diffs = np.diff(hist)
            y = int(counts_in_window(days, single, 0, cfg.horizon_days - 1)[0] > 0)
            weeks_with_purchase = len(np.unique((hist - 1) // 7))
            rows.append(
                (
                    hh.household,
                    d,
                    commodity,
                    y,
                    len(hist),
                    weeks_with_purchase / n_weeks,
                    d - int(hist[-1]),
                    float(diffs.mean()),
                    float(diffs.std()),
                    len(hist) / hist_trips >= cfg.staple_trip_share,
                    hist_trips / n_weeks,
                )
            )
    return pd.DataFrame(rows, columns=list(PAIR_COLUMNS))
