from typing import Self

from pydantic import BaseModel, Field, model_validator


class TaskConfig(BaseModel):
    level_sizes: dict[str, int] = Field(default={'L1': 5, 'L2': 10, 'L3': 20})
    relevant_coupons: int = 3
    coupon_top_commodities: int = 3
    profile_top_commodities: int = 10
    history_days: int = 98
    ends_soon_days: int = 7
    min_anchor_gap_days: int = 14
    max_instances_per_hh: int = 3
    tier_dominance: float = Field(default=0.8, gt=0.5, lt=1.0)
    use_demographics: bool = False

    @model_validator(mode='after')
    def _check_levels(self) -> Self:
        sizes = sorted(self.level_sizes.values())
        assert sizes, 'level_sizes must not be empty'
        assert all(size > 0 for size in sizes), 'level sizes must be positive'
        assert all(a < b for a, b in zip(sizes, sizes[1:])), 'level sizes must be distinct'
        assert self.relevant_coupons <= sizes[0], (
            'every level prefix must fit the constant relevant-coupon count'
        )
        assert self.coupon_top_commodities >= 1, 'coupons need at least one display commodity'
        assert self.history_days > 0 and self.ends_soon_days >= 0, 'windows must be non-negative'
        return self

    @property
    def pool_size(self) -> int:
        """Coupon pool per anchor; the largest level is a prefix of the full pool."""
        return max(self.level_sizes.values())


class GateConfig(BaseModel):
    max_words: int = 40
    min_selected: int = 1
    max_selected: int = 3


class RewardConfig(BaseModel):
    w_base: float = 0.2
    w_affinity: float = 0.2
    w_judge: float = 0.6

    @model_validator(mode='after')
    def _check_weights(self) -> Self:
        assert self.w_base > 0, (
            'w_base > 0 keeps every grounded message above every ungrounded one'
        )
        assert self.w_affinity >= 0 and self.w_judge >= 0, 'weights must be non-negative'
        assert self.w_base + self.w_affinity + self.w_judge <= 1, 'rewards must stay in [0, 1]'
        return self


class JudgeConfig(BaseModel):
    model: str = 'anthropic/claude-haiku-5.5'
    temperature: float = 0.0
    max_tokens: int = 1024  # reasoning models think before the verdict; 200 truncated them
    reasoning_effort: str | None = None
    agreement_model: str | None = None
    agreement_share: float = Field(default=0.1, ge=0.0, le=1.0)
