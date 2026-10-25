import re
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass, replace

from commgym.dunnhumby.types import BrandTier
from commgym.refund.config import PolicyParams
from commgym.refund.coverage import coverage_of
from commgym.refund.instance import CouponView, ReceiptLine, Reference, RefundInstance
from commgym.refund.lexicon import QUANTITY_WORDS, plural_of, resolve_reference
from commgym.refund.policy import (
    ClaimFacts,
    ClaimVerdict,
    Decision,
    ReasonCode,
    StatedType,
    adjudicate,
    allocate_refunds,
)
from commgym.refund.prompts import user_prompt
from commgym.refund.renderer import split_sentences
from commgym.refund.reward import ParsedClaim
from commgym.refund.wordmap import WORD_CATEGORIES

# the parser's own keywords and word map: authored before and independent of the generated
# claim texts, which are LLM-written and verified by two other readers — a fair baseline
COUPON_WORDS = ('coupon', 'discount')
ABSENCE_WORDS = (
    'missing',
    'not in my bag',
    'never received',
    'did not receive',
    'never made it',
    'forgot to bag',
    'never got',
    'did not come home',
    'not delivered',
    'never arrived',
    'skipped',
)
# claims say 'name-brand'; coupon coverage descriptions say 'national-brand'
TIER_WORDS_PARSER = {
    'store-brand': BrandTier.PRIVATE,
    'name-brand': BrandTier.NATIONAL,
    'national-brand': BrandTier.NATIONAL,
}
SIZE_WORDS_PARSER = {'larger': 'bigger', 'smaller': 'smaller'}


@dataclass(frozen=True, slots=True)
class PromptView:
    """A rendered user prompt parsed back from text; all the rule parser is allowed to see."""

    purchase_day: int
    claim_day: int
    policy: PolicyParams
    lines: tuple[ReceiptLine, ...]
    coupons: tuple[CouponView, ...]
    message: str


@dataclass(frozen=True, slots=True)
class ConstantFits:
    """Train-set fits for the constant baselines."""

    reject_reason: ReasonCode
    approve_reason: ReasonCode
    refund_cents: int


def parse_user_prompt(text: str) -> PromptView:
    """Extract days, the case policy, receipt rows, coupon rows, and the message."""
    purchase_day = _day(r'Purchase day: (\d+)', text)
    claim_day = _day(r'Claim filed: day (\d+)', text)
    lines: list[ReceiptLine] = []
    coupons: list[CouponView] = []
    message = ''
    for row in text.splitlines():
        if row.startswith('| L'):
            lines.append(_receipt_row(row))
        elif row.startswith('| C'):
            coupons.append(_coupon_row(row))
        elif row.startswith('Customer message:'):
            message = text.split('Customer message:', 1)[1].strip()
    assert message, 'prompt must contain the customer message'
    return PromptView(
        purchase_day=purchase_day,
        claim_day=claim_day,
        policy=_policy_block(text),
        lines=tuple(lines),
        coupons=tuple(coupons),
        message=message,
    )


def rule_parser_answers(view: PromptView) -> tuple[ParsedClaim, ...]:
    """Segment the message, classify and resolve each claim, then adjudicate by the book."""
    days = view.claim_day - view.purchase_day
    answers: list[ParsedClaim] = []
    for sentence in split_sentences(view.message):
        stated = classify_stated_type(sentence)
        ref = extract_reference(sentence, view.lines)
        codes = resolve_reference(ref, view.lines) if ref is not None else ()
        line_code = codes[0] if len(codes) == 1 else None
        line = next((item for item in view.lines if item.code == line_code), None)
        values = tuple(
            coupon.typical_value_cents
            for coupon in view.coupons
            if line_code is not None and line_code in coverage_of(coupon.coverage, view.lines)
        )
        adjudication = adjudicate(
            ClaimFacts(
                stated_type=stated,
                days_since_purchase=days,
                n_matched_lines=len(codes),
                line_code=line_code,
                loyalty_unit_cents=line.loyalty_unit_cents if line is not None else None,
                reference_cents=line.reference_cents if line is not None else None,
                quantity=line.quantity if line is not None else None,
                covering_coupon_values_cents=values,
                coupon_disc_applied=bool(line and line.coupon_disc_unit_cents != 0),
                brand_tier=line.brand_tier if line is not None else None,
                paid_unit_cents=line.paid_unit_cents if line is not None else None,
            ),
            view.policy,
        )
        answers.append(
            ParsedClaim(
                line=line_code,
                decision=adjudication.decision,
                reason=adjudication.reason,
                refund_cents=adjudication.refund_cents,
            )
        )
    refunds = allocate_refunds(
        [ClaimVerdict(a.decision, a.line, a.refund_cents) for a in answers], view.policy
    )
    return tuple(
        replace(answer, refund_cents=refund)
        for answer, refund in zip(answers, refunds, strict=True)
    )


def always_reject_answers(n_claims: int, reason: ReasonCode) -> tuple[ParsedClaim, ...]:
    return tuple(ParsedClaim(None, Decision.REJECT, reason, 0) for _ in range(n_claims))


def always_approve_answers(
    n_claims: int, reason: ReasonCode, refund_cents: int
) -> tuple[ParsedClaim, ...]:
    return tuple(
        ParsedClaim(None, Decision.APPROVE, reason, refund_cents) for _ in range(n_claims)
    )


def oracle_answers(instance: RefundInstance) -> tuple[ParsedClaim, ...]:
    return tuple(
        ParsedClaim(
            claim.truth_line, claim.truth_decision, claim.truth_reason, claim.truth_refund_cents
        )
        for claim in instance.claims
    )


def fit_constants(instances: Sequence[RefundInstance]) -> ConstantFits:
    """Most frequent reject and approve reasons plus the median live-coupon value, from train."""
    reject_counts: Counter[ReasonCode] = Counter()
    approve_counts: Counter[ReasonCode] = Counter()
    values: list[int] = []
    for instance in instances:
        for claim in instance.claims:
            if claim.truth_decision is Decision.REJECT:
                reject_counts[claim.truth_reason] += 1
            else:
                approve_counts[claim.truth_reason] += 1
        values += [coupon.typical_value_cents for coupon in instance.coupons]
    assert reject_counts and approve_counts and values, 'train instances must cover all fits'
    ordered = sorted(values)
    return ConstantFits(
        reject_reason=reject_counts.most_common(1)[0][0],
        approve_reason=approve_counts.most_common(1)[0][0],
        refund_cents=ordered[(len(ordered) - 1) // 2],
    )


def classify_stated_type(sentence: str) -> StatedType:
    lowered = sentence.lower()
    if any(word in lowered for word in COUPON_WORDS):
        return StatedType.COUPON
    if any(word in lowered for word in ABSENCE_WORDS):
        return StatedType.MISSING_ITEM
    return StatedType.PRICE


def extract_reference(sentence: str, lines: Sequence[ReceiptLine]) -> Reference | None:
    """Longest map word mentioned in the sentence, with any tier/size/quantity modifiers."""
    lowered = sentence.lower()
    words = sorted(WORD_CATEGORIES)
    matched = [
        form
        for word in words
        for form in {word, plural_of(word)}
        if re.search(rf'\b{re.escape(form)}\b', lowered)
    ]
    if not matched:
        return None
    # longest match wins ('frozen vegetables' beats 'vegetables'); ties break deterministically
    best = max(sorted(matched), key=lambda form: (len(form), form))
    word = next(word for word in words if best in (word, plural_of(word)))
    forms = [word, plural_of(word)]
    return Reference(
        word=word,
        brand_tier=_tier_before(forms, lowered),
        size_cmp=_size_before(forms, lowered),
        quantity=_quantity_before(forms, lowered),
    )


def prompt_view_of(instance: RefundInstance) -> PromptView:
    return parse_user_prompt(user_prompt(instance))


def _receipt_row(row: str) -> ReceiptLine:
    cells = [cell.strip() for cell in row.split('|')]
    return ReceiptLine(
        code=cells[1],
        product_id=0,
        commodity=cells[2],
        sub_commodity=cells[3],
        brand_tier=BrandTier(cells[4]),
        size=cells[5],
        quantity=int(cells[6]),
        regular_unit_cents=_cents(cells[7]),
        loyalty_disc_unit_cents=_cents(cells[8]),
        coupon_disc_unit_cents=_cents(cells[9]),
        paid_unit_cents=_cents(cells[10]),
        reference_cents=_cents(cells[11]),
    )


def _coupon_row(row: str) -> CouponView:
    cells = [cell.strip() for cell in row.split('|')]
    return CouponView(coupon_id=cells[1], typical_value_cents=_cents(cells[2]), coverage=cells[3])


def _policy_block(text: str) -> PolicyParams:
    window = _int(r'filed more than (\d+) days after the purchase day', text)
    tolerance = _cents(_match(r'more than \$([\d.]+) per unit', text))
    cap_match = re.search(r'capped at \$(\d+(?:\.\d+)?)', text)
    return PolicyParams(
        claim_window_days=window,
        price_tolerance_cents=tolerance,
        refund_cap_cents=_cents(cap_match.group(1)) if cap_match is not None else None,
        price_match_national_only='national-brand items only' in text,
    )


def _match(pattern: str, text: str) -> str:
    match = re.search(pattern, text)
    if match is None:
        raise ValueError(f'prompt does not match {pattern!r}')
    return match.group(1)


def _cents(cell: str) -> int:
    return int(round(float(cell.lstrip('$')) * 100))


def _day(pattern: str, text: str) -> int:
    return int(_match(pattern, text))


def _int(pattern: str, text: str) -> int:
    return int(_match(pattern, text))


def _tier_before(nouns: Sequence[str], lowered: str) -> BrandTier | None:
    for word, tier in TIER_WORDS_PARSER.items():
        for noun in nouns:
            if re.search(rf'\b{word} {re.escape(noun)}\b', lowered):
                return tier
    return None


def _size_before(nouns: Sequence[str], lowered: str) -> str | None:
    for word, comparison in SIZE_WORDS_PARSER.items():
        for noun in nouns:
            if re.search(rf'\b{word} size of the {re.escape(noun)}\b', lowered):
                return comparison
    return None


def _quantity_before(nouns: Sequence[str], lowered: str) -> int | None:
    for value, word in QUANTITY_WORDS.items():
        for noun in nouns:
            if re.search(rf'\b{word} {re.escape(plural_of(noun))}\b', lowered):
                return value
    return None
