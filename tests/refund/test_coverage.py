from commgym.dunnhumby.types import BrandTier
from commgym.refund.coverage import coverage_of, describe_coverage
from commgym.refund.instance import ReceiptLine


def line(
    code: str,
    commodity: str,
    sub: str,
    tier: BrandTier = BrandTier.NATIONAL,
    size: str = '12 OZ',
) -> ReceiptLine:
    return ReceiptLine(
        code=code,
        product_id=hash(code) % 10_000,
        commodity=commodity,
        sub_commodity=sub,
        brand_tier=tier,
        size=size,
        quantity=1,
        regular_unit_cents=100,
        loyalty_disc_unit_cents=0,
        coupon_disc_unit_cents=0,
        paid_unit_cents=100,
        reference_cents=100,
    )


def test_plain_category_phrase_covers_exact_lines():
    lines = (line('L01', 'COFFEE', 'GROUND'), line('L02', 'CHEESE', 'SHREDDED'))
    assert describe_coverage(['L01'], lines) == 'national-brand coffee'
    assert coverage_of('national-brand coffee', lines) == ('L01',)


def test_overshoot_removed_by_exception_clause():
    lines = (
        line('L01', 'COFFEE', 'GROUND COFFEE'),
        line('L02', 'COFFEE', 'INSTANT COFFEE'),
        line('L03', 'CHEESE', 'SHREDDED'),
    )
    text = describe_coverage(['L01'], lines)
    assert text == 'national-brand coffee, except instant coffee'
    assert coverage_of(text, lines) == ('L01',)


def test_tier_phrase_splits_brand_scope():
    lines = (
        line('L01', 'COFFEE', 'GROUND', tier=BrandTier.NATIONAL),
        line('L02', 'COFFEE', 'GROUND', tier=BrandTier.PRIVATE),
    )
    text = describe_coverage(['L01'], lines)
    assert text == 'national-brand coffee'
    assert coverage_of(text, lines) == ('L01',)


def test_size_bound_covers_only_the_bounded_lines():
    lines = (
        line('L01', 'COFFEE', 'GROUND', size='12 OZ'),
        line('L02', 'COFFEE', 'GROUND', size='32 OZ'),
    )
    text = describe_coverage(['L01'], lines)
    assert text == 'national-brand coffee 12 oz and smaller'
    assert coverage_of(text, lines) == ('L01',)
    bigger = describe_coverage(['L02'], lines)
    assert bigger == 'national-brand coffee 32 oz and larger'
    assert coverage_of(bigger, lines) == ('L02',)


def test_unexpressible_set_returns_none():
    # covered 12oz and 16oz, uncovered 14oz between them: no bound or exclusion separates them
    lines = (
        line('L01', 'COFFEE', 'GROUND', size='12 OZ'),
        line('L02', 'COFFEE', 'GROUND', size='14 OZ'),
        line('L03', 'COFFEE', 'GROUND', size='16 OZ'),
    )
    assert describe_coverage(['L01', 'L03'], lines) is None


def test_multi_category_union_with_shared_exception():
    lines = (
        line('L01', 'COFFEE', 'GROUND COFFEE'),
        line('L02', 'COFFEE', 'INSTANT COFFEE'),
        line('L03', 'FLUID MILK PRODUCTS', 'WHOLE'),
        line('L04', 'FLUID MILK PRODUCTS', 'SKIM'),
    )
    text = describe_coverage(['L01', 'L03'], lines)
    assert text == (
        'national-brand coffee, national-brand fluid milk products, except instant coffee, skim'
    )
    assert coverage_of(text, lines) == ('L01', 'L03')


def test_exception_cannot_remove_a_kept_sub_category():
    # the overshoot shares a sub-category with a covered line, so exclusion would over-remove
    lines = (
        line('L01', 'COFFEE', 'GROUND', size='12 OZ'),
        line('L02', 'COFFEE', 'GROUND', size='32 OZ'),
        line('L03', 'TEA', 'GREEN', size='32 OZ'),
    )
    # covering L02 alone: plain coffee overshoots onto L01 (same sub); size bounds fix it
    text = describe_coverage(['L02'], lines)
    assert text == 'national-brand coffee 32 oz and larger'
    assert coverage_of(text, lines) == ('L02',)
    # covering L02+L03 across categories: coffee needs its size bound, tea does not
    both = describe_coverage(['L02', 'L03'], lines)
    assert both == 'national-brand coffee 32 oz and larger, national-brand tea'
    assert coverage_of(both, lines) == ('L02', 'L03')


def test_coverage_of_parses_oxford_comma_phrases():
    lines = (
        line('L01', 'COFFEE', 'GROUND'),
        line('L02', 'CHEESE', 'SHREDDED'),
        line('L03', 'TEA', 'GREEN'),
    )
    assert coverage_of('coffee, cheese, and tea', lines) == ('L01', 'L02', 'L03')
