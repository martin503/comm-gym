from dataclasses import asdict, dataclass

from pydantic import BaseModel, ConfigDict

from commgym.dunnhumby.types import BrandTier
from commgym.refund.config import PolicyParams
from commgym.refund.policy import Decision, ReasonCode, StatedType


@dataclass(frozen=True, slots=True)
class ReceiptLine:
    """One receipt row; cents columns satisfy paid = regular - loyalty_disc - coupon_disc."""

    code: str
    product_id: int
    commodity: str
    sub_commodity: str
    brand_tier: BrandTier
    size: str
    quantity: int
    regular_unit_cents: int
    loyalty_disc_unit_cents: int
    coupon_disc_unit_cents: int
    paid_unit_cents: int
    reference_cents: int

    def __post_init__(self) -> None:
        assert 0 <= self.loyalty_disc_unit_cents <= self.regular_unit_cents, 'loyalty disc range'
        assert (
            0
            <= self.coupon_disc_unit_cents
            <= self.regular_unit_cents - self.loyalty_disc_unit_cents
        ), 'coupon disc range'
        expected = (
            self.regular_unit_cents - self.loyalty_disc_unit_cents - self.coupon_disc_unit_cents
        )
        assert self.paid_unit_cents == expected, 'paid column must equal regular - discounts'

    @property
    def loyalty_unit_cents(self) -> int:
        """The price-match comparison price, reproducible from the displayed columns."""
        return self.regular_unit_cents - self.loyalty_disc_unit_cents


@dataclass(frozen=True, slots=True)
class CouponView:
    """A live household coupon as shown in the prompt; provenance is never displayed."""

    coupon_id: str
    typical_value_cents: int
    coverage: str


@dataclass(frozen=True, slots=True)
class Reference:
    """How a claim points at items; modifiers narrow the word-matched receipt lines."""

    word: str
    brand_tier: BrandTier | None = None
    size_cmp: str | None = None
    quantity: int | None = None


@dataclass(frozen=True, slots=True)
class Claim:
    """One customer claim with its adjudicated ground truth and render metadata."""

    stated_type: StatedType
    reference_text: str  # LLM-written item phrase, e.g. 'the navel oranges'
    reference_kind: str  # 'unique' (one line) | 'clarify' (several) | 'absent' (no line)
    truth_line: str | None
    truth_decision: Decision
    truth_reason: ReasonCode
    truth_refund_cents: int
    stated_number: bool = False
    stated_cents: int | None = None  # the injected contradicting figure, for leak checks


@dataclass(frozen=True, slots=True)
class RefundInstance:
    """A nested-level instance: receipt + coupons + the level's prefix of the anchor's claims."""

    instance_id: str
    anchor_id: str
    split: str
    level: str
    household: int
    basket: int
    purchase_day: int
    claim_day: int
    policy: PolicyParams
    lines: tuple[ReceiptLine, ...]
    coupons: tuple[CouponView, ...]
    message: str  # the customer message; level prefixes show their prefix of it
    claims: tuple[Claim, ...]
    is_out_of_window: bool


class LineRecord(BaseModel):
    model_config = ConfigDict(extra='forbid')

    code: str
    product_id: int
    commodity: str
    sub_commodity: str
    brand_tier: BrandTier
    size: str
    quantity: int
    regular_unit_cents: int
    loyalty_disc_unit_cents: int
    coupon_disc_unit_cents: int
    paid_unit_cents: int
    reference_cents: int


class CouponRecord(BaseModel):
    model_config = ConfigDict(extra='forbid')

    coupon_id: str
    typical_value_cents: int
    coverage: str


class ClaimRecord(BaseModel):
    model_config = ConfigDict(extra='forbid')

    stated_type: StatedType
    reference_text: str
    reference_kind: str
    truth_line: str | None
    truth_decision: Decision
    truth_reason: ReasonCode
    truth_refund_cents: int
    stated_number: bool = False
    stated_cents: int | None = None


class InstanceRecord(BaseModel):
    model_config = ConfigDict(extra='forbid')

    instance_id: str
    anchor_id: str
    split: str
    level: str
    household: int
    basket: int
    purchase_day: int
    claim_day: int
    policy: PolicyParams
    lines: list[LineRecord]
    coupons: list[CouponRecord]
    message: str
    claims: list[ClaimRecord]
    is_out_of_window: bool


def instance_to_record(instance: RefundInstance) -> dict[str, object]:
    record = InstanceRecord(
        instance_id=instance.instance_id,
        anchor_id=instance.anchor_id,
        split=instance.split,
        level=instance.level,
        household=instance.household,
        basket=instance.basket,
        purchase_day=instance.purchase_day,
        claim_day=instance.claim_day,
        policy=instance.policy,
        lines=[LineRecord(**asdict(line)) for line in instance.lines],
        coupons=[
            CouponRecord(
                coupon_id=coupon.coupon_id,
                typical_value_cents=coupon.typical_value_cents,
                coverage=coupon.coverage,
            )
            for coupon in instance.coupons
        ],
        message=instance.message,
        claims=[
            ClaimRecord(
                stated_type=claim.stated_type,
                reference_text=claim.reference_text,
                reference_kind=claim.reference_kind,
                truth_line=claim.truth_line,
                truth_decision=claim.truth_decision,
                truth_reason=claim.truth_reason,
                truth_refund_cents=claim.truth_refund_cents,
                stated_number=claim.stated_number,
                stated_cents=claim.stated_cents,
            )
            for claim in instance.claims
        ],
        is_out_of_window=instance.is_out_of_window,
    )
    return record.model_dump()


def record_to_instance(record: dict[str, object]) -> RefundInstance:
    parsed = InstanceRecord.model_validate(record)
    return RefundInstance(
        instance_id=parsed.instance_id,
        anchor_id=parsed.anchor_id,
        split=parsed.split,
        level=parsed.level,
        household=parsed.household,
        basket=parsed.basket,
        purchase_day=parsed.purchase_day,
        claim_day=parsed.claim_day,
        policy=parsed.policy,
        lines=tuple(
            ReceiptLine(
                code=line.code,
                product_id=line.product_id,
                commodity=line.commodity,
                sub_commodity=line.sub_commodity,
                brand_tier=line.brand_tier,
                size=line.size,
                quantity=line.quantity,
                regular_unit_cents=line.regular_unit_cents,
                loyalty_disc_unit_cents=line.loyalty_disc_unit_cents,
                coupon_disc_unit_cents=line.coupon_disc_unit_cents,
                paid_unit_cents=line.paid_unit_cents,
                reference_cents=line.reference_cents,
            )
            for line in parsed.lines
        ),
        coupons=tuple(
            CouponView(
                coupon_id=coupon.coupon_id,
                typical_value_cents=coupon.typical_value_cents,
                coverage=coupon.coverage,
            )
            for coupon in parsed.coupons
        ),
        message=parsed.message,
        claims=tuple(
            Claim(
                stated_type=claim.stated_type,
                reference_text=claim.reference_text,
                reference_kind=claim.reference_kind,
                truth_line=claim.truth_line,
                truth_decision=claim.truth_decision,
                truth_reason=claim.truth_reason,
                truth_refund_cents=claim.truth_refund_cents,
                stated_number=claim.stated_number,
                stated_cents=claim.stated_cents,
            )
            for claim in parsed.claims
        ),
        is_out_of_window=parsed.is_out_of_window,
    )
