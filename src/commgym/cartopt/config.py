from typing import Self

from pydantic import BaseModel, Field, model_validator


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
