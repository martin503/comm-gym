import pytest

from cartgym.instance import BrandTier, ManufacturerMultiBuy, MenuSKU, SkuCoupon, ThresholdBundle
from cartgym.pricing import cost

ICE = 'FRZN ICE'
SODA = 'SOFT DRINKS'


def _sku(
    code: str, commodity: str, shelf: int, loyalty: int, tier: BrandTier, mfr: int
) -> MenuSKU:
    return MenuSKU(
        code=code,
        product_id=0,
        commodity=commodity,
        brand_tier=tier,
        manufacturer=mfr,
        size='',
        shelf_cents=shelf,
        loyalty_disc_cents=loyalty,
    )


@pytest.fixture
def menu() -> dict[str, list[MenuSKU]]:
    # nets: A1=250, A2=200, B1=120, B2=90; A1/B1 share manufacturer 7
    return {
        ICE: [
            _sku('A1', ICE, 300, 50, BrandTier.NATIONAL, 7),
            _sku('A2', ICE, 200, 0, BrandTier.PRIVATE, 8),
        ],
        SODA: [
            _sku('B1', SODA, 150, 30, BrandTier.NATIONAL, 7),
            _sku('B2', SODA, 100, 10, BrandTier.PRIVATE, 9),
        ],
    }


def test_loyalty_discount_applied_before_coupons(make_instance, menu):
    instance = make_instance(menu)
    result = cost({ICE: 'A1', SODA: 'B2'}, instance)
    assert {
        'total': result.total_cents,
        'nets': result.sku_nets,
        'coupons': result.applied_coupon_ids,
        'coupon_total': result.coupon_total_cents,
    } == {'total': 340, 'nets': (('A1', 250), ('B2', 90)), 'coupons': (), 'coupon_total': 0}


def test_sku_coupon_applies_to_chosen_code(make_instance, menu):
    instance = make_instance(menu, coupons=(SkuCoupon('C1', 'A1', 40),))
    assert cost({ICE: 'A1', SODA: 'B2'}, instance).total_cents == 300


def test_sku_coupon_ignored_when_code_not_chosen(make_instance, menu):
    instance = make_instance(menu, coupons=(SkuCoupon('C1', 'A1', 40),))
    assert cost({ICE: 'A2', SODA: 'B2'}, instance).total_cents == 290


def test_threshold_bundle_triggers_at_exact_threshold(make_instance, menu):
    # spend on both categories with A1+B1 is exactly 250 + 120 = 370
    instance = make_instance(menu, coupons=(ThresholdBundle('C2', (ICE, SODA), 370, 100),))
    assert cost({ICE: 'A1', SODA: 'B1'}, instance).total_cents == 270


def test_threshold_bundle_one_cent_below_does_not_trigger(make_instance, menu):
    instance = make_instance(menu, coupons=(ThresholdBundle('C2', (ICE, SODA), 371, 100),))
    assert cost({ICE: 'A1', SODA: 'B1'}, instance).total_cents == 370


def test_multibuy_triggers_at_min_items(make_instance, menu):
    # A1 and B1 are both manufacturer 7
    instance = make_instance(menu, coupons=(ManufacturerMultiBuy('C3', 7, 2, 60),))
    assert cost({ICE: 'A1', SODA: 'B1'}, instance).total_cents == 310


def test_multibuy_below_min_items_does_not_trigger(make_instance, menu):
    # only B1 is manufacturer 7 here
    instance = make_instance(menu, coupons=(ManufacturerMultiBuy('C3', 7, 2, 60),))
    assert cost({ICE: 'A2', SODA: 'B1'}, instance).total_cents == 320


def test_all_coupon_kinds_stack(make_instance, menu):
    instance = make_instance(
        menu,
        coupons=(
            SkuCoupon('C1', 'A1', 40),
            ThresholdBundle('C2', (ICE, SODA), 370, 100),
            ManufacturerMultiBuy('C3', 7, 2, 60),
        ),
    )
    # base 370; sku coupon -40; bundle (spend 370 ≥ 370) -100; multibuy (2 items of mfr 7) -60
    assert cost({ICE: 'A1', SODA: 'B1'}, instance).total_cents == 170


def test_loyalty_discount_cannot_exceed_shelf_price():
    with pytest.raises(AssertionError, match='loyalty discount'):
        _sku('X', ICE, 100, 101, BrandTier.PRIVATE, 1)


def test_total_never_negative(make_instance):
    menu = {SODA: [_sku('B2', SODA, 100, 10, BrandTier.PRIVATE, 9)]}
    instance = make_instance(menu, coupons=(SkuCoupon('C1', 'B2', 500),))
    with pytest.raises(AssertionError, match='negative'):
        cost({SODA: 'B2'}, instance)
