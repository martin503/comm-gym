from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum

from commgym.dunnhumby.types import BrandTier
from commgym.refund.config import PolicyParams


class StatedType(StrEnum):
    """What the customer's claim is about, as stated in the message."""

    PRICE = 'price'
    COUPON = 'coupon'
    MISSING_ITEM = 'missing_item'


class Decision(StrEnum):
    APPROVE = 'approve'
    REJECT = 'reject'


class ReasonCode(StrEnum):
    OUTSIDE_WINDOW = 'OUTSIDE_WINDOW'
    NOT_ON_RECEIPT = 'NOT_ON_RECEIPT'
    NEEDS_CLARIFICATION = 'NEEDS_CLARIFICATION'
    PRICE_MATCH = 'PRICE_MATCH'
    WITHIN_TOLERANCE = 'WITHIN_TOLERANCE'
    MISSED_COUPON = 'MISSED_COUPON'
    NOT_ELIGIBLE = 'NOT_ELIGIBLE'
    ALREADY_APPLIED = 'ALREADY_APPLIED'


@dataclass(frozen=True, slots=True)
class ClaimFacts:
    """Everything the policy needs about one claim; prices are the displayed integer cents."""

    stated_type: StatedType
    days_since_purchase: int
    n_matched_lines: int
    line_code: str | None
    loyalty_unit_cents: int | None
    reference_cents: int | None
    quantity: int | None
    covering_coupon_values_cents: tuple[int, ...]
    coupon_disc_applied: bool
    brand_tier: BrandTier | None = None
    paid_unit_cents: int | None = None


@dataclass(frozen=True, slots=True)
class Adjudication:
    decision: Decision
    reason: ReasonCode
    refund_cents: int


def adjudicate(facts: ClaimFacts, policy: PolicyParams) -> Adjudication:
    """Apply the refund policy in precedence order; the first deciding rule fixes the reason."""
    assert (facts.line_code is None) == (facts.n_matched_lines != 1), (
        'line code set iff the claim resolved to exactly one receipt line'
    )
    if facts.days_since_purchase > policy.claim_window_days:
        return Adjudication(Decision.REJECT, ReasonCode.OUTSIDE_WINDOW, 0)
    if facts.n_matched_lines == 0:
        return Adjudication(Decision.REJECT, ReasonCode.NOT_ON_RECEIPT, 0)
    if facts.n_matched_lines >= 2:
        return Adjudication(Decision.REJECT, ReasonCode.NEEDS_CLARIFICATION, 0)
    if facts.stated_type is StatedType.PRICE:
        assert (
            facts.loyalty_unit_cents is not None
            and facts.reference_cents is not None
            and facts.quantity is not None
            and facts.brand_tier is not None
            and facts.paid_unit_cents is not None
        ), 'price claims carry prices, quantity, brand tier, and the paid unit price'
        if policy.price_match_national_only and facts.brand_tier is not BrandTier.NATIONAL:
            return Adjudication(Decision.REJECT, ReasonCode.NOT_ELIGIBLE, 0)
        diff = facts.loyalty_unit_cents - facts.reference_cents
        if diff > policy.price_tolerance_cents:
            # a refund never exceeds what was actually paid for the item
            refund = min(diff * facts.quantity, facts.paid_unit_cents * facts.quantity)
            return Adjudication(Decision.APPROVE, ReasonCode.PRICE_MATCH, refund)
        return Adjudication(Decision.REJECT, ReasonCode.WITHIN_TOLERANCE, 0)
    if not facts.covering_coupon_values_cents:
        return Adjudication(Decision.REJECT, ReasonCode.NOT_ELIGIBLE, 0)
    if facts.coupon_disc_applied:
        return Adjudication(Decision.REJECT, ReasonCode.ALREADY_APPLIED, 0)
    return Adjudication(
        Decision.APPROVE, ReasonCode.MISSED_COUPON, max(facts.covering_coupon_values_cents)
    )


@dataclass(frozen=True, slots=True)
class ClaimVerdict:
    """One adjudicated claim reduced to what the receipt-level rules need."""

    decision: Decision
    line_code: str | None
    refund_cents: int


def allocate_refunds(verdicts: Sequence[ClaimVerdict], policy: PolicyParams) -> tuple[int, ...]:
    """Receipt-level rules in claim order: same line pays once, then the per-receipt cap."""
    paid_lines: set[str] = set()
    remaining = policy.refund_cap_cents
    refunds: list[int] = []
    for verdict in verdicts:
        refund = verdict.refund_cents if verdict.decision is Decision.APPROVE else 0
        if refund <= 0:
            refunds.append(0)
            continue
        assert verdict.line_code is not None, 'approved claims point at a receipt line'
        first_on_line = verdict.line_code not in paid_lines
        paid_lines.add(verdict.line_code)
        if not first_on_line:
            refunds.append(0)
            continue
        if remaining is not None:
            refund = min(refund, max(remaining, 0))
            remaining -= refund
        refunds.append(refund)
    return tuple(refunds)
