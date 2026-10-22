from pathlib import Path
from typing import Self

import yaml
from pydantic import BaseModel, Field, model_validator


class CleaningConfig(BaseModel):
    max_quantity: int = 12
    excluded_departments: tuple[str, ...] = ('KIOSK-GAS', 'COUP/STR & MFG', '')
    excluded_commodities: tuple[str, ...] = ('NO COMMODITY DESCRIPTION',)


class SchemaExpectations(BaseModel):
    min_day: int = 1
    max_day: int = 711
    min_week: int = 1
    max_week: int = 102
    n_households: int = 2500


class DataChecksConfig(BaseModel):
    expectations: SchemaExpectations = SchemaExpectations()
    derivation_min_valid_share: float = 0.99
    price_coverage_min_skus: int = 4
    price_coverage_min_pair_share: float = 0.50
    price_spread_min_median_cv: float = 0.05
    coupon_amounts_min_lines: int = 1000
    basket_min_share_at_max_categories: float = 0.05
    max_categories: int = 8
    ramp_steady_state_share: float = 0.80
    campaign_window_start_day: int = 224
    heldout_min_weeks: int = 10
    heldout_commodity_share: float = 0.20
    heldout_seed: int = 42


class PricingConfig(BaseModel):
    min_price_obs: int = 1


class LevelConfig(BaseModel):
    categories: int
    skus_per_category: int
    sku_coupons: tuple[int, int]
    threshold_bundles: int = 0
    brand_quota: bool = False
    coupon_gap_cap_prob: float = Field(default=0.0, ge=0.0, le=1.0)


class LevelsConfig(BaseModel):
    levels: dict[str, LevelConfig]
    tie_eps_cents: int = 1
    near_tie_delta_cents: int = 10
    trap_rate: float = 0.70
    gap_cap_margin_cents: tuple[int, int] = (15, 65)

    @model_validator(mode='after')
    def _check_gap_cap(self) -> Self:
        lo, hi = self.gap_cap_margin_cents
        assert lo <= hi, 'gap-cap margin range must be ordered'
        assert lo > self.near_tie_delta_cents, (
            'gap-cap margin must clear the near-tie band or capped instances get rejected'
        )
        return self


class RewardConfig(BaseModel):
    w_partial: float = 0.3
    w_feasible: float = 0.5
    w_opt: float = 0.4
    w_price: float = 0.1
    tie_eps_cents: int = 1
    price_tol_cents: int = 1

    @model_validator(mode='after')
    def _check_weights(self) -> Self:
        assert 0 <= self.w_partial < self.w_feasible <= 1, (
            'lexicographic invariant broken: need 0 <= w_partial < w_feasible'
        )
        assert self.w_feasible + self.w_opt + self.w_price <= 1, (
            'feasible rewards must stay in [0, 1]'
        )
        assert self.tie_eps_cents >= 0 and self.price_tol_cents >= 0, (
            'tolerances must be non-negative'
        )
        return self


class SplitsConfig(BaseModel):
    cutoff_week: int = 68
    campaign_window_start_day: int = 224
    train_hh_ratio: float = 0.8
    n_spend_tiers: int = 4
    heldout_min_skus: int = 4
    heldout_min_weeks: int = 10
    heldout_commodity_share: float = 0.20
    heldout_seed: int = 42
    seed: int = 42


def load_config[T: BaseModel](model: type[T], path: Path) -> T:
    """Parse a YAML config file into the given pydantic model."""
    data = yaml.safe_load(path.read_text())
    assert isinstance(data, dict), f'config {path} must be a YAML mapping'
    return model.model_validate(data)
