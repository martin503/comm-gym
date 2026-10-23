from pydantic import BaseModel


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
