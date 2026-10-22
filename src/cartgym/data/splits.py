from dataclasses import dataclass

import numpy as np
import pandas as pd

from cartgym.config import SplitsConfig
from cartgym.data.load import Campaign


@dataclass(frozen=True, slots=True)
class SplitSpec:
    name: str
    households: frozenset[int]
    first_week: int
    last_week: int


@dataclass(frozen=True, slots=True)
class Splits:
    train: SplitSpec
    dev: SplitSpec
    eval_unseen: SplitSpec
    eval_known: SplitSpec
    heldout_commodities: frozenset[str]

    def spec(self, name: str) -> SplitSpec:
        specs = {
            'train': self.train,
            'dev': self.dev,
            'eval_unseen': self.eval_unseen,
            'eval_known': self.eval_known,
        }
        assert name in specs, f'unknown split {name!r}'
        return specs[name]


@dataclass(frozen=True, slots=True)
class CampaignCalendar:
    campaigns: tuple[Campaign, ...]

    def live_campaigns(self, day: int) -> tuple[Campaign, ...]:
        return tuple(c for c in self.campaigns if c.start_day <= day <= c.end_day)

    def live_days(self) -> frozenset[int]:
        """Days covered by at least one campaign window."""
        days: set[int] = set()
        for campaign in self.campaigns:
            days.update(range(campaign.start_day, campaign.end_day + 1))
        return frozenset(days)


def build_splits(
    txc: pd.DataFrame, demographics: set[int], coverage: pd.DataFrame, cfg: SplitsConfig
) -> Splits:
    """Cohorts (spend × demographics stratified) crossed with the time split."""
    first_week = (cfg.campaign_window_start_day - 1) // 7 + 1
    last_week = int(txc['WEEK_NO'].max())
    cohort_a, cohort_b = _split_cohorts(txc, demographics, cfg, first_week)
    return Splits(
        train=SplitSpec('train', cohort_a, first_week, cfg.cutoff_week),
        dev=SplitSpec('dev', cohort_b, first_week, cfg.cutoff_week),
        eval_unseen=SplitSpec('eval_unseen', cohort_b, cfg.cutoff_week + 1, last_week),
        eval_known=SplitSpec('eval_known', cohort_a, cfg.cutoff_week + 1, last_week),
        heldout_commodities=select_heldout_commodities(coverage, cfg),
    )


def eligible_commodities(coverage: pd.DataFrame, min_skus: int, min_weeks: int) -> pd.Index:
    """Commodities with >= min_skus priced SKUs in >= min_weeks weeks."""
    qualified = coverage[coverage['n_skus'] >= min_skus].groupby('commodity').size()
    return qualified[qualified >= min_weeks].index


def select_heldout_commodities(coverage: pd.DataFrame, cfg: SplitsConfig) -> frozenset[str]:
    """Seeded draw of eval-only commodities; the same rule backs the data check."""
    eligible = eligible_commodities(coverage, cfg.heldout_min_skus, cfg.heldout_min_weeks)
    rng = np.random.default_rng(cfg.heldout_seed)
    n_held = round(len(eligible) * cfg.heldout_commodity_share)
    held = rng.choice(eligible.to_numpy(), size=n_held, replace=False)
    return frozenset(str(c) for c in held)


def _split_cohorts(
    txc: pd.DataFrame, demographics: set[int], cfg: SplitsConfig, first_week: int
) -> tuple[frozenset[int], frozenset[int]]:
    early = txc[(txc['WEEK_NO'] >= first_week) & (txc['WEEK_NO'] <= cfg.cutoff_week)]
    spend = early.groupby('household_key')['SALES_VALUE'].sum()
    tiers = pd.qcut(spend, q=cfg.n_spend_tiers, labels=False)
    strata: dict[tuple[int, bool], list[int]] = {}
    for household in sorted(txc['household_key'].unique()):
        household = int(household)
        tier = int(tiers.loc[household]) if household in tiers.index else -1
        strata.setdefault((tier, household in demographics), []).append(household)
    rng = np.random.default_rng(cfg.seed)
    cohort_a: list[int] = []
    cohort_b: list[int] = []
    for members in strata.values():
        order = rng.permutation(len(members))
        n_a = round(len(members) * cfg.train_hh_ratio)
        cohort_a += [members[i] for i in order[:n_a]]
        cohort_b += [members[i] for i in order[n_a:]]
    return frozenset(cohort_a), frozenset(cohort_b)
