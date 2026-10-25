import json

from commgym.dunnhumby.types import BrandTier
from commgym.refund.config import PolicyParams
from commgym.refund.instance import (
    Claim,
    CouponView,
    ReceiptLine,
    Reference,
    RefundInstance,
    instance_to_record,
    record_to_instance,
)
from commgym.refund.lexicon import (
    parse_size,
    plural_of,
    resolve_reference,
    unique_reference,
    words_of,
)
from commgym.refund.policy import Decision, ReasonCode, StatedType


def _line(
    code: str,
    noun_category: str,
    *,
    brand: BrandTier = BrandTier.NATIONAL,
    size: str = '12 OZ',
    quantity: int = 1,
    sub: str = 'MISC',
) -> ReceiptLine:
    return ReceiptLine(
        code=code,
        product_id=ord(code[1]) * 100 + int(code[2:]),
        commodity=noun_category,
        sub_commodity=sub,
        brand_tier=brand,
        size=size,
        quantity=quantity,
        regular_unit_cents=200,
        loyalty_disc_unit_cents=0,
        coupon_disc_unit_cents=0,
        paid_unit_cents=200,
        reference_cents=200,
    )


def test_parse_size_normalizes_units_and_takes_first_match():
    cases = {
        '12 OZ': (12.0, 'OZ'),
        '16.9 OZ': (16.9, 'OZ'),
        '4 CT': (4.0, 'CT'),
        '2PK': (2.0, 'PACK'),
        '1 LB 4 OZ': (1.0, 'LB'),
        '6/12 OZ': None,
        '2 LITERS': (2.0, 'LT'),
        'NO SIZE': None,
        '': None,
    }
    actual = {
        text: (spec.value, spec.unit) if (spec := parse_size(text)) is not None else None
        for text in cases
    }
    assert actual == cases


def test_resolve_reference_ladder_narrows_in_order():
    small = _line('L01', 'YOGURT', brand=BrandTier.PRIVATE, size='6 OZ')
    big = _line('L02', 'YOGURT', brand=BrandTier.NATIONAL, size='32 OZ')
    both = (small, big)
    actual = {
        'word': resolve_reference(Reference(word='yogurt'), both),
        'tier': resolve_reference(Reference(word='yogurt', brand_tier=BrandTier.PRIVATE), both),
        'bigger': resolve_reference(Reference(word='yogurt', size_cmp='bigger'), both),
        'smaller': resolve_reference(Reference(word='yogurt', size_cmp='smaller'), both),
        'absent': resolve_reference(Reference(word='soda'), both),
    }
    assert actual == {
        'word': ('L01', 'L02'),
        'tier': ('L01',),
        'bigger': ('L02',),
        'smaller': ('L01',),
        'absent': (),
    }


def test_specific_word_sub_grounds_to_its_sub_kind():
    ricotta = _line('L01', 'MILK BY-PRODUCTS', size='15 OZ', sub='RICOTTA CHEESE')
    dips = _line('L02', 'MILK BY-PRODUCTS', size='8 OZ', sub='REFRIG DIPS')
    lines = (ricotta, dips)
    assert {
        # 'ricotta' is specific: only the ricotta-kind line counts
        'specific': resolve_reference(Reference(word='ricotta'), lines),
        # 'cream' is specific but no line carries the kind, so the generic fallback keeps all
        'ungrounded_specific': resolve_reference(Reference(word='cream'), lines),
        # 'yogurt' echoes its category name and is never sub-grounded
        'generic': resolve_reference(Reference(word='yogurt'), lines),
    } == {'specific': ('L01',), 'ungrounded_specific': ('L01', 'L02'), 'generic': ()}


def test_close_sizes_never_become_size_references():
    small = _line('L01', 'CANDY - PACKAGED', size='12 OZ')
    big = _line('L02', 'CANDY - PACKAGED', size='16.9 OZ')
    assert {
        'no_rung': unique_reference(small, (small, big)),
        'no_rung_big': unique_reference(big, (small, big)),
    } == {'no_rung': None, 'no_rung_big': None}


def test_cereal_word_covers_hot_cereal_lines():
    # dry-run bug regression: a claim word is never 'not on receipt' while one of its
    # categories is on the receipt
    oatmeal = _line('L01', 'HOT CEREAL')
    lines = (oatmeal, _line('L02', 'COFFEE'))
    assert {
        'cereal': resolve_reference(Reference(word='cereal'), lines),
        'oatmeal': resolve_reference(Reference(word='oatmeal'), lines),
        'words_of': words_of('HOT CEREAL'),
    } == {
        'cereal': ('L01',),
        'oatmeal': ('L01',),
        'words_of': ('oats', 'grits', 'cereal', 'oatmeal', 'instant oatmeal'),
    }


def test_mixed_units_make_size_comparison_undecidable():
    ounce = _line('L01', 'FROZEN PIZZA', size='14 OZ', quantity=2)
    liter = _line('L02', 'FROZEN PIZZA', size='1.25 LT')
    actual = {
        'bigger': resolve_reference(
            Reference(word='frozen pizza', size_cmp='bigger'), (ounce, liter)
        ),
        'qty': resolve_reference(Reference(word='frozen pizza', quantity=2), (ounce, liter)),
    }
    assert actual == {'bigger': ('L01', 'L02'), 'qty': ('L01',)}


def test_unique_reference_walks_the_word_ladder():
    unique = _line('L01', 'COFFEE', quantity=3)
    private_yog = _line('L02', 'YOGURT', brand=BrandTier.PRIVATE, size='6 OZ')
    national_yog = _line('L03', 'YOGURT', brand=BrandTier.NATIONAL, size='32 OZ')
    middle = _line('L04', 'SOFT DRINKS', size='12 OZ')
    small_soda = _line('L05', 'SOFT DRINKS', size='6 OZ')
    big_soda = _line('L06', 'SOFT DRINKS', size='20 OZ')
    milk_pair = (_line('L07', 'FLUID MILK PRODUCTS'), _line('L08', 'FLUID MILK PRODUCTS'))
    lines = (unique, private_yog, national_yog, middle, small_soda, big_soda, *milk_pair)
    actual = {
        'word': unique_reference(unique, lines),
        'tier': unique_reference(private_yog, lines),
        'size': unique_reference(big_soda, lines),
        'middle_none': unique_reference(middle, lines),
        'mass_word': unique_reference(milk_pair[0], lines),
    }
    assert actual == {
        'word': (Reference(word='coffee'), 'word'),
        'tier': (Reference(word='yogurt', brand_tier=BrandTier.PRIVATE), 'brand_tier'),
        'size': (Reference(word='pop', size_cmp='bigger'), 'size'),
        'middle_none': None,
        # milk is a mass word (plural == word), so the quantity rung never applies
        'mass_word': None,
    }


def test_plural_of_singular_and_mass_words():
    assert {
        'hot dog': plural_of('hot dog'),
        'potatoes': plural_of('potatoes'),
        'milk': plural_of('milk'),
        'trash bag': plural_of('trash bag'),
    } == {'hot dog': 'hot dogs', 'potatoes': 'potatoes', 'milk': 'milk', 'trash bag': 'trash bags'}


def test_record_round_trip_preserves_instance():
    claim = Claim(
        stated_type=StatedType.PRICE,
        reference_text='the coffee',
        reference_kind='unique',
        truth_line='L01',
        truth_decision=Decision.APPROVE,
        truth_reason=ReasonCode.PRICE_MATCH,
        truth_refund_cents=30,
        stated_number=True,
        stated_cents=499,
    )
    instance = RefundInstance(
        instance_id='dev-L1-0007',
        anchor_id='dev-0007',
        split='dev',
        level='L1',
        household=42,
        basket=1234,
        purchase_day=240,
        claim_day=249,
        policy=PolicyParams(claim_window_days=14, price_tolerance_cents=5),
        lines=(_line('L01', 'COFFEE'),),
        coupons=(CouponView(coupon_id='C01', typical_value_cents=50, coverage='coffee'),),
        message='The coffee cost $4.99 at checkout.',
        claims=(claim,),
        is_out_of_window=False,
    )
    record = json.loads(json.dumps(instance_to_record(instance)))
    assert record_to_instance(record) == instance


def test_words_of_covers_curated_categories():
    assert {
        'HOT DOGS': words_of('HOT DOGS'),
        'unknown': words_of('MADE UP CATEGORY'),
    } == {
        'HOT DOGS': ('franks', 'hot dog', 'hot dogs', 'beef franks', 'kosher dogs'),
        'unknown': (),
    }
