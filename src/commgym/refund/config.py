from typing import Self

from pydantic import BaseModel, Field, field_validator, model_validator

IN_WINDOW_REASONS = frozenset(
    {
        'PRICE_MATCH',
        'MISSED_COUPON',
        'NOT_ON_RECEIPT',
        'NEEDS_CLARIFICATION',
        'WITHIN_TOLERANCE',
        'NOT_ELIGIBLE',
        'ALREADY_APPLIED',
    }
)


class PolicyParams(BaseModel):
    """The case policy; v2 samples window/tolerance/cap/scope per anchor (spec §12)."""

    claim_window_days: int = 14
    price_tolerance_cents: int = 5
    refund_cap_cents: int | None = None
    price_match_national_only: bool = False


class TaskConfig(BaseModel):
    """Refund-task generation parameters; see refund_claims_plan.md."""

    policy: PolicyParams = PolicyParams()
    max_receipt_lines: int = 40
    anchor_min_target_lines: int = 3
    out_of_window_anchor_rate: float = 0.15
    claims_per_anchor: int = 3
    min_redemptions: int = 2
    # per-anchor policy sampling grids; delays derive from the sampled window
    policy_window_days: tuple[int, ...] = (7, 14, 21, 30)
    policy_tolerance_cents: tuple[int, ...] = (5, 10, 15, 25, 50)
    policy_refund_caps_cents: tuple[int | None, ...] = (50, 75, 100, 150)
    policy_national_only_prob: float = 0.5
    stated_number_prob: float = 0.4
    same_line_claim_prob: float = 0.35
    in_window_type_shares: dict[str, float] = Field(
        default={
            'PRICE_MATCH': 21,
            'MISSED_COUPON': 28,
            'NOT_ON_RECEIPT': 14,
            'NEEDS_CLARIFICATION': 8,
            'WITHIN_TOLERANCE': 10,
            'NOT_ELIGIBLE': 8,
            'ALREADY_APPLIED': 4,
        }
    )

    @field_validator('in_window_type_shares')
    @classmethod
    def _check_shares(cls, value: dict[str, float]) -> dict[str, float]:
        assert set(value) <= IN_WINDOW_REASONS, 'unknown reason code in type shares'
        assert all(weight > 0 for weight in value.values()), 'type shares must be positive'
        return value


class RewardConfig(BaseModel):
    """Spec §6 per-claim weights: approve splits 0.25 across four checks, reject doubles reason."""

    w_decision: float = 0.25
    w_line: float = 0.25
    w_reason_approve: float = 0.25
    w_refund: float = 0.25
    w_reason_reject: float = 0.50
    refund_tol_cents: int = 1

    @model_validator(mode='after')
    def _check_weights(self) -> Self:
        # 0.25/0.5 are exact binary fractions, so equality holds for any spec-conformant config
        assert self.w_decision + self.w_line + self.w_reason_approve + self.w_refund == 1.0, (
            'approve weights must sum to 1'
        )
        assert self.w_decision + self.w_line + self.w_reason_reject == 1.0, (
            'reject weights must sum to 1'
        )
        return self
