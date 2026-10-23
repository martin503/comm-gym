import pytest

from commgym.cartopt.instance import (
    BrandTier,
    Coupon,
    ManufacturerMultiBuy,
    MenuSKU,
    SkuCoupon,
    ThresholdBundle,
)
from commgym.cartopt.pricing import cost

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


def test_sku_coupon_scoped_to_chosen_code(make_instance, menu):
    instance = make_instance(menu, coupons=(SkuCoupon('C1', 'A1', 40),))
    assert {
        'chosen': cost({ICE: 'A1', SODA: 'B2'}, instance).total_cents,
        'not_chosen': cost({ICE: 'A2', SODA: 'B2'}, instance).total_cents,
    } == {'chosen': 300, 'not_chosen': 290}


def test_bundle_and_multibuy_trigger_only_at_boundaries(make_instance, menu):
    def total(coupons: tuple[Coupon, ...], cart: dict[str, str]) -> int:
        return cost(cart, make_instance(menu, coupons=coupons)).total_cents

    a1_b1 = {ICE: 'A1', SODA: 'B1'}  # nets 250 + 120 = 370; both items manufacturer 7
    a2_b1 = {ICE: 'A2', SODA: 'B1'}  # only B1 is manufacturer 7
    assert {
        'bundle_at_threshold': total((ThresholdBundle('C2', (ICE, SODA), 370, 100),), a1_b1),
        'bundle_one_cent_below': total((ThresholdBundle('C2', (ICE, SODA), 371, 100),), a1_b1),
        'multibuy_at_min_items': total((ManufacturerMultiBuy('C3', 7, 2, 60),), a1_b1),
        'multibuy_below_min_items': total((ManufacturerMultiBuy('C3', 7, 2, 60),), a2_b1),
    } == {
        'bundle_at_threshold': 270,
        'bundle_one_cent_below': 370,
        'multibuy_at_min_items': 310,
        'multibuy_below_min_items': 320,
    }


def test_all_coupon_kinds_stack(make_instance, menu):
    instance = make_instance(
        menu,
        coupons=(
            SkuCoupon('C1', 'A1', 40),
            ThresholdBundle('C2', (ICE, SODA), 370, 100),
            ManufacturerMultiBuy('C3', 7, 2, 60),
        ),
    )
    # base 370; sku coupon -40; bundle (spend 370 >= 370) -100; multibuy (2 items of mfr 7) -60
    assert cost({ICE: 'A1', SODA: 'B1'}, instance).total_cents == 170
