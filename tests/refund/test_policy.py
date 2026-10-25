from commgym.dunnhumby.types import BrandTier
from commgym.refund.config import PolicyParams
from commgym.refund.policy import (
    ClaimFacts,
    ClaimVerdict,
    Decision,
    ReasonCode,
    StatedType,
    adjudicate,
    allocate_refunds,
)

POLICY = PolicyParams()


def facts(
    *,
    stated_type: StatedType = StatedType.PRICE,
    days_since_purchase: int = 3,
    n_matched_lines: int = 1,
    line_code: str | None = 'L01',
    loyalty_unit_cents: int | None = 160,
    reference_cents: int | None = 100,
    quantity: int | None = 2,
    covering_coupon_values_cents: tuple[int, ...] = (),
    coupon_disc_applied: bool = False,
    brand_tier: BrandTier | None = BrandTier.NATIONAL,
    paid_unit_cents: int | None = 160,
) -> ClaimFacts:
    """Default: in-window on-receipt price claim, overcharged 60c on a qty-2 line."""
    return ClaimFacts(
        stated_type=stated_type,
        days_since_purchase=days_since_purchase,
        n_matched_lines=n_matched_lines,
        line_code=line_code,
        loyalty_unit_cents=loyalty_unit_cents,
        reference_cents=reference_cents,
        quantity=quantity,
        covering_coupon_values_cents=covering_coupon_values_cents,
        coupon_disc_applied=coupon_disc_applied,
        brand_tier=brand_tier,
        paid_unit_cents=paid_unit_cents,
    )


def test_window_precedes_price_and_missing_item():
    late_price = adjudicate(facts(days_since_purchase=15), POLICY)
    late_missing = adjudicate(
        facts(
            stated_type=StatedType.MISSING_ITEM,
            days_since_purchase=20,
            n_matched_lines=0,
            line_code=None,
            loyalty_unit_cents=None,
            reference_cents=None,
            quantity=None,
        ),
        POLICY,
    )
    assert {
        'late_price': (late_price.decision, late_price.reason, late_price.refund_cents),
        'late_missing': (late_missing.decision, late_missing.reason, late_missing.refund_cents),
    } == {
        'late_price': (Decision.REJECT, ReasonCode.OUTSIDE_WINDOW, 0),
        'late_missing': (Decision.REJECT, ReasonCode.OUTSIDE_WINDOW, 0),
    }


def test_missing_receipt_precedes_price_and_coupon_rules():
    off_receipt = (
        facts(
            n_matched_lines=0,
            line_code=None,
            loyalty_unit_cents=None,
            reference_cents=None,
            quantity=None,
        ),
        facts(
            stated_type=StatedType.COUPON,
            n_matched_lines=0,
            line_code=None,
            loyalty_unit_cents=None,
            reference_cents=None,
            quantity=None,
        ),
    )
    priced, couped = (adjudicate(f, POLICY) for f in off_receipt)
    assert {
        'priced': (priced.reason, priced.refund_cents),
        'couped': (couped.reason, couped.refund_cents),
    } == {
        'priced': (ReasonCode.NOT_ON_RECEIPT, 0),
        'couped': (ReasonCode.NOT_ON_RECEIPT, 0),
    }


def test_ambiguous_reference_clarifies_before_stated_type_rules():
    ambiguous_price = facts(
        n_matched_lines=2,
        line_code=None,
        loyalty_unit_cents=None,
        reference_cents=None,
        quantity=None,
        paid_unit_cents=None,
        brand_tier=None,
    )
    ambiguous_coupon = facts(
        stated_type=StatedType.COUPON,
        n_matched_lines=3,
        line_code=None,
        loyalty_unit_cents=None,
        reference_cents=None,
        quantity=None,
        brand_tier=None,
        paid_unit_cents=None,
        covering_coupon_values_cents=(75,),
    )
    priced, couped = (adjudicate(f, POLICY) for f in (ambiguous_price, ambiguous_coupon))
    assert {
        'priced': (priced.decision, priced.reason, priced.refund_cents),
        'couped': (couped.decision, couped.reason, couped.refund_cents),
    } == {
        'priced': (Decision.REJECT, ReasonCode.NEEDS_CLARIFICATION, 0),
        'couped': (Decision.REJECT, ReasonCode.NEEDS_CLARIFICATION, 0),
    }


def test_price_branch_boundary_and_refund():
    over = adjudicate(facts(), POLICY)
    boundary = adjudicate(facts(loyalty_unit_cents=105), POLICY)  # diff == tolerance exactly
    one_over = adjudicate(facts(loyalty_unit_cents=106), POLICY)
    assert {
        'over': (over.decision, over.reason, over.refund_cents),
        'boundary': (boundary.decision, boundary.reason, boundary.refund_cents),
        'one_over': (one_over.decision, one_over.reason, one_over.refund_cents),
    } == {
        'over': (Decision.APPROVE, ReasonCode.PRICE_MATCH, 120),
        'boundary': (Decision.REJECT, ReasonCode.WITHIN_TOLERANCE, 0),
        'one_over': (Decision.APPROVE, ReasonCode.PRICE_MATCH, 12),
    }


def test_coupon_branch_takes_max_covering_value():
    missed = adjudicate(
        facts(stated_type=StatedType.COUPON, covering_coupon_values_cents=(30, 75, 50)), POLICY
    )
    ineligible = adjudicate(facts(stated_type=StatedType.COUPON), POLICY)
    applied = adjudicate(
        facts(
            stated_type=StatedType.COUPON,
            covering_coupon_values_cents=(30, 75),
            coupon_disc_applied=True,
        ),
        POLICY,
    )
    assert {
        'missed': (missed.decision, missed.reason, missed.refund_cents),
        'ineligible': (ineligible.decision, ineligible.reason, ineligible.refund_cents),
        'applied': (applied.decision, applied.reason, applied.refund_cents),
    } == {
        'missed': (Decision.APPROVE, ReasonCode.MISSED_COUPON, 75),
        'ineligible': (Decision.REJECT, ReasonCode.NOT_ELIGIBLE, 0),
        'applied': (Decision.REJECT, ReasonCode.ALREADY_APPLIED, 0),
    }


def test_national_only_toggle_rejects_private_price_claims():
    scoped = PolicyParams(price_match_national_only=True)
    private = adjudicate(facts(brand_tier=BrandTier.PRIVATE, paid_unit_cents=160), scoped)
    national = adjudicate(facts(brand_tier=BrandTier.NATIONAL, paid_unit_cents=160), scoped)
    assert {
        'private': (private.decision, private.reason, private.refund_cents),
        'national': (national.decision, national.reason, national.refund_cents),
    } == {
        'private': (Decision.REJECT, ReasonCode.NOT_ELIGIBLE, 0),
        'national': (Decision.APPROVE, ReasonCode.PRICE_MATCH, 120),
    }


def test_price_refund_never_exceeds_what_was_paid():
    # loyalty unit 300 vs reference 20, qty 2 -> raw 560, but only 2 x 100 was paid
    result = adjudicate(
        facts(loyalty_unit_cents=300, reference_cents=20, quantity=2, paid_unit_cents=100), POLICY
    )
    assert (result.decision, result.reason, result.refund_cents) == (
        Decision.APPROVE,
        ReasonCode.PRICE_MATCH,
        200,
    )


def _verdict(decision: Decision, line: str | None, refund: int) -> ClaimVerdict:
    return ClaimVerdict(decision, line, refund)


def test_allocate_applies_receipt_cap_in_claim_order():
    verdicts = [
        _verdict(Decision.APPROVE, 'L01', 300),
        _verdict(Decision.APPROVE, 'L02', 250),
        _verdict(Decision.APPROVE, 'L03', 100),
        _verdict(Decision.REJECT, 'L04', 0),
    ]
    capped = allocate_refunds(verdicts, PolicyParams(refund_cap_cents=500))
    uncapped = allocate_refunds(verdicts, PolicyParams())
    assert {'capped': capped, 'uncapped': uncapped} == {
        'capped': (300, 200, 0, 0),
        'uncapped': (300, 250, 100, 0),
    }


def test_allocate_pays_each_line_only_once():
    verdicts = [
        _verdict(Decision.APPROVE, 'L01', 120),
        _verdict(Decision.APPROVE, 'L01', 50),
        _verdict(Decision.APPROVE, 'L02', 75),
    ]
    assert allocate_refunds(verdicts, PolicyParams()) == (120, 0, 75)
