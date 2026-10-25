import json
from collections.abc import Sequence
from dataclasses import replace

from commgym.dunnhumby.types import BrandTier
from commgym.refund.config import PolicyParams, RewardConfig
from commgym.refund.instance import Claim, ReceiptLine, RefundInstance
from commgym.refund.policy import Decision, ReasonCode, StatedType
from commgym.refund.reward import GradeResult, ParsedClaim, grade, grade_parsed, parse_completion

CFG = RewardConfig()


def _line(
    code: str,
    commodity: str,
    *,
    quantity: int = 1,
    regular: int = 100,
    loyalty_disc: int = 0,
    coupon_disc: int = 0,
    reference: int = 100,
    brand_tier: BrandTier = BrandTier.NATIONAL,
    size: str = '12 OZ',
) -> ReceiptLine:
    return ReceiptLine(
        code=code,
        product_id=hash(code) % 10_000,
        commodity=commodity,
        sub_commodity='MISC',
        brand_tier=brand_tier,
        size=size,
        quantity=quantity,
        regular_unit_cents=regular,
        loyalty_disc_unit_cents=loyalty_disc,
        coupon_disc_unit_cents=coupon_disc,
        paid_unit_cents=regular - loyalty_disc - coupon_disc,
        reference_cents=reference,
    )


# Hand-derived receipt (cents): L01 overcharged 60c x2, L02 within 3c, L03 loyalty price at
# reference, L04 covered by a $0.50 coupon never applied, L06 coupon already applied, L07
# overcharged 10c x3.
RECEIPT = (
    _line(
        'L01',
        'POTATOES',
        quantity=2,
        regular=160,
        reference=100,
        brand_tier=BrandTier.PRIVATE,
        size='5 LB',
    ),
    _line('L02', 'BAG SNACKS', regular=103, reference=100),
    _line('L03', 'FLUID MILK PRODUCTS', regular=120, loyalty_disc=20, reference=120, size='1 GAL'),
    _line('L04', 'YOGURT', regular=150, reference=150, brand_tier=BrandTier.PRIVATE, size='6 OZ'),
    _line('L06', 'CHEESE', regular=230, coupon_disc=30, reference=200, size='8 OZ'),
    _line('L07', 'COFFEE', quantity=3, regular=150, reference=140, brand_tier=BrandTier.PRIVATE),
    _line('L08', 'FROZEN PIZZA', regular=100, reference=100, size='14 OZ'),
)


def _claim(
    stated: StatedType, line: str | None, decision: Decision, reason: ReasonCode, refund: int
) -> Claim:
    return Claim(
        stated_type=stated,
        reference_text='the coffee',
        reference_kind='unique',
        truth_line=line,
        truth_decision=decision,
        truth_reason=reason,
        truth_refund_cents=refund,
    )


INSTANCE = RefundInstance(
    instance_id='dev-L2-0001',
    anchor_id='dev-0001',
    split='dev',
    level='L2',
    household=1,
    basket=9001,
    purchase_day=240,
    claim_day=244,
    policy=PolicyParams(),
    lines=RECEIPT,
    coupons=(),
    message='Claim 1: trouble. Claim 2: trouble. Claim 3: missing.',
    claims=(
        _claim(StatedType.PRICE, 'L01', Decision.APPROVE, ReasonCode.PRICE_MATCH, 120),
        _claim(StatedType.COUPON, 'L04', Decision.APPROVE, ReasonCode.MISSED_COUPON, 50),
        _claim(StatedType.MISSING_ITEM, None, Decision.REJECT, ReasonCode.NOT_ON_RECEIPT, 0),
    ),
    is_out_of_window=False,
)

ORACLE: list[dict[str, object]] = [
    {'line': 'L01', 'decision': 'approve', 'reason': 'PRICE_MATCH', 'refund': 1.20},
    {'line': 'L04', 'decision': 'approve', 'reason': 'MISSED_COUPON', 'refund': 0.50},
    {'line': None, 'decision': 'reject', 'reason': 'NOT_ON_RECEIPT', 'refund': 0},
]


def _text(entries: Sequence[object]) -> str:
    payload = json.dumps({'claims': entries})
    return f'Looking at the receipt...\n<answer>{payload}</answer>'


def _grade(entries: list[dict[str, object]]) -> GradeResult:
    return grade(_text(entries), INSTANCE, CFG)


def _swap(entries: list[dict[str, object]], i: int, j: int) -> list[dict[str, object]]:
    out = list(entries)
    out[i], out[j] = out[j], out[i]
    return out


def test_oracle_answer_scores_one():
    result = _grade(ORACLE)
    assert {
        'reward': result.reward,
        'parse': (result.parse_ok, result.parse_reason),
        'scores': [s.score for s in result.claim_scores],
        'false_flags': [(s.false_approve, s.false_reject) for s in result.claim_scores],
        'dollar_errors': [s.dollar_error_cents for s in result.claim_scores],
    } == {
        'reward': 1.0,
        'parse': (True, None),
        'scores': [1.0, 1.0, 1.0],
        'false_flags': [(False, False)] * 3,
        'dollar_errors': [0, 0, 0],
    }


def test_out_of_order_answers_lose_line_reason_and_refund_credit():
    # grading is positional: each swapped answer keeps only the decision credit
    result = _grade(_swap(ORACLE, 0, 1))
    assert {
        'reward': result.reward,
        'scores': [round(s.score, 10) for s in result.claim_scores],
    } == {'reward': (0.25 + 0.25 + 1.0) / 3, 'scores': [0.25, 0.25, 1.0]}


def test_wrong_refund_on_approve_keeps_three_quarters():
    result = _grade([ORACLE[0] | {'refund': 0.99}, ORACLE[1], ORACLE[2]])
    assert {
        'reward': result.reward,
        'first': (result.claim_scores[0].score, result.claim_scores[0].refund_ok),
    } == {'reward': (0.75 + 1.0 + 1.0) / 3, 'first': (0.75, False)}


def test_refund_within_one_cent_still_counts():
    result = _grade([ORACLE[0] | {'refund': 1.21}, ORACLE[1] | {'refund': 0.49}, ORACLE[2]])
    assert {
        'reward': result.reward,
        'refund_ok': [s.refund_ok for s in result.claim_scores],
    } == {'reward': 1.0, 'refund_ok': [True, True, True]}


def test_reject_with_penny_refund_zeroes_the_claim():
    result = _grade([ORACLE[0], ORACLE[1], ORACLE[2] | {'refund': 0.01}])
    assert {
        'reward': result.reward,
        'third': (result.claim_scores[2].score, result.claim_scores[2].reason_ok),
    } == {'reward': (1.0 + 1.0 + 0.0) / 3, 'third': (0.0, True)}


def test_wrong_decision_zeroes_the_claim():
    result = _grade([ORACLE[0], ORACLE[1], ORACLE[2] | {'decision': 'approve', 'refund': 0}])
    third = result.claim_scores[2]
    assert {
        'reward': result.reward,
        'third': (third.score, third.false_approve, third.false_reject),
    } == {'reward': 2.0 / 3, 'third': (0.0, True, False)}


def test_false_reject_flagged_on_approve_truth():
    result = _grade([ORACLE[0] | {'decision': 'reject', 'refund': 0}, ORACLE[1], ORACLE[2]])
    first = result.claim_scores[0]
    assert {'score': first.score, 'false_reject': first.false_reject} == {
        'score': 0.0,
        'false_reject': True,
    }


def test_wrong_line_on_reject_keeps_decision_and_reason():
    # NOT_ON_RECEIPT truth: naming any receipt line loses line credit (0.25) but keeps the rest
    result = _grade([ORACLE[0], ORACLE[1], ORACLE[2] | {'line': 'L08'}])
    assert {
        'reward': result.reward,
        'third': (result.claim_scores[2].score, result.claim_scores[2].line_ok),
    } == {'reward': (1.0 + 1.0 + 0.75) / 3, 'third': (0.75, False)}


def test_parse_failure_modes_score_zero():
    good = json.dumps({'claims': ORACLE})

    def broken(**overrides: object) -> str:
        first = ORACLE[0] | overrides
        return _text([first, *ORACLE[1:]])

    no_refund = {key: value for key, value in ORACLE[0].items() if key != 'refund'}
    cases = {
        'no_block': 'The refund is $1.20 for the potatoes.',
        'multiple_blocks': f'<answer>{good}</answer><answer>{good}</answer>',
        'invalid_json': '<answer>{"claims": [}</answer>',
        'payload_not_a_dict': f'<answer>{json.dumps([ORACLE])}</answer>',
        'claims_not_a_list': '<answer>{"claims": "all rejected"}</answer>',
        'wrong_claim_count': _text(ORACLE[:2]),
        'claim_not_a_dict': _text(['L01', *ORACLE[1:]]),
        'missing_refund_field': _text([no_refund, *ORACLE[1:]]),
        'bad_line': broken(line='L99'),
        'line_not_a_string': broken(line=1),
        'bad_decision': broken(decision='maybe'),
        'unknown_reason': broken(reason='TOO_EXPENSIVE'),
        'string_refund': broken(refund='1.20'),
        'bool_refund': broken(refund=True),
        'nan_refund': broken(refund=float('nan')),
        'negative_refund': broken(refund=-0.10),
    }
    expected_reasons = {
        'no_block': 'no_answer_block',
        'multiple_blocks': 'multiple_answer_blocks',
        'invalid_json': 'invalid_json',
        'payload_not_a_dict': 'payload_not_a_dict',
        'claims_not_a_list': 'claims_not_a_list',
        'wrong_claim_count': 'wrong_claim_count',
        'claim_not_a_dict': 'claim_not_a_dict',
        'missing_refund_field': 'missing_field:refund',
        'bad_line': 'bad_line',
        'line_not_a_string': 'bad_line',
        'bad_decision': 'bad_decision_or_reason',
        'unknown_reason': 'bad_decision_or_reason',
        'string_refund': 'refund_not_numeric',
        'bool_refund': 'refund_not_numeric',
        'nan_refund': 'refund_not_finite',
        'negative_refund': 'refund_negative',
    }
    actual = {name: _outcome(grade(text, INSTANCE, CFG)) for name, text in cases.items()}
    assert actual == {name: (0.0, False, reason, ()) for name, reason in expected_reasons.items()}


def _outcome(result: GradeResult) -> tuple[float, bool, str | None, tuple[object, ...]]:
    return (result.reward, result.parse_ok, result.parse_reason, result.claim_scores)


def test_extra_keys_are_ignored_and_int_refunds_parse():
    entries = [
        ORACLE[0] | {'refund': 1, 'confidence': 0.9},
        ORACLE[1] | {'note': 'checked'},
        ORACLE[2],
    ]
    result = _grade(entries)
    assert {
        'parse': (result.parse_ok, result.parse_reason),
        'refund_cents_ok': result.reward < 1.0,  # 100c vs 120c truth loses refund credit only
        'first_score': result.claim_scores[0].score,
    } == {'parse': (True, None), 'refund_cents_ok': True, 'first_score': 0.75}


def test_grade_parsed_shared_path_scores_oracle():
    parsed = (
        ParsedClaim('L01', Decision.APPROVE, ReasonCode.PRICE_MATCH, 120),
        ParsedClaim('L04', Decision.APPROVE, ReasonCode.MISSED_COUPON, 50),
        ParsedClaim(None, Decision.REJECT, ReasonCode.NOT_ON_RECEIPT, 0),
    )
    result = grade_parsed(parsed, INSTANCE, CFG)
    assert {'reward': result.reward, 'parse': result.parse_ok} == {
        'reward': 1.0,
        'parse': True,
    }


def test_zero_refund_approve_keeps_full_credit():
    # a dedup/cap-exhausted truth: the second approve on the same line pays nothing
    claims = (
        _claim(StatedType.PRICE, 'L01', Decision.APPROVE, ReasonCode.PRICE_MATCH, 120),
        _claim(StatedType.COUPON, 'L01', Decision.APPROVE, ReasonCode.MISSED_COUPON, 0),
    )
    instance = replace(INSTANCE, claims=claims)
    parsed = (
        ParsedClaim('L01', Decision.APPROVE, ReasonCode.PRICE_MATCH, 120),
        ParsedClaim('L01', Decision.APPROVE, ReasonCode.MISSED_COUPON, 0),
    )
    result = grade_parsed(parsed, instance, CFG)
    assert {
        'reward': result.reward,
        'refund_ok': [s.refund_ok for s in result.claim_scores],
    } == {'reward': 1.0, 'refund_ok': [True, True]}


def test_parse_completion_returns_normalized_claims():
    parsed = parse_completion(_text(ORACLE), 3, frozenset(line.code for line in RECEIPT))
    assert parsed.claims == (
        ParsedClaim('L01', Decision.APPROVE, ReasonCode.PRICE_MATCH, 120),
        ParsedClaim('L04', Decision.APPROVE, ReasonCode.MISSED_COUPON, 50),
        ParsedClaim(None, Decision.REJECT, ReasonCode.NOT_ON_RECEIPT, 0),
    )
