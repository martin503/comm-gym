import numpy as np
import pytest

from commgym.cartopt.baselines import (
    baseline_carts,
    constraint_aware_greedy,
    couponed_cheapest_cart,
    greedy_max_discount_cart,
    lowest_shelf_cart,
    oracle_cart,
    random_cart,
    real_shopper_cart,
    tier_cheapest_cart,
)
from commgym.cartopt.instance import (
    BrandQuota,
    BrandTier,
    Instance,
    LoyalSKU,
    SkuCoupon,
)
from commgym.cartopt.pricing import cost

# Hand-derived fixture (cents): CAT A1 Private 200 / A2 National 280 (coupon 30c)
# DOG B1 Private 150 / B2 National 210 ; quota >= 1 National
# greedy A1+B1 = 350 infeasible; repair premiums: DOG B2 +60 < CAT A2 +80 -> A1+B2 = 410
# oracle A2+B1 = 400 (uses the coupon)


@pytest.fixture
def trap(make_sku, make_instance) -> Instance:
    return make_instance(
        {
            'CAT': [
                make_sku('A1', 'CAT', shelf_cents=200),
                make_sku('A2', 'CAT', shelf_cents=280, brand_tier=BrandTier.NATIONAL),
            ],
            'DOG': [
                make_sku('B1', 'DOG', shelf_cents=150),
                make_sku('B2', 'DOG', shelf_cents=210, brand_tier=BrandTier.NATIONAL),
            ],
        },
        coupons=(SkuCoupon('c1', 'A2', 30),),
        constraints=(BrandQuota(BrandTier.NATIONAL, 1),),
    )


def test_constraint_aware_greedy_repairs_quota_by_smallest_premium(trap: Instance):
    assert constraint_aware_greedy(trap) == {'CAT': 'A1', 'DOG': 'B2'}


def test_constraint_aware_greedy_forces_loyal_sku_then_repairs(make_sku, make_instance):
    instance = make_instance(
        {
            'CAT': [
                make_sku('A1', 'CAT', shelf_cents=200),
                make_sku('A2', 'CAT', shelf_cents=280, brand_tier=BrandTier.NATIONAL),
            ],
            'DOG': [
                make_sku('B1', 'DOG', shelf_cents=150),
                make_sku('B2', 'DOG', shelf_cents=210, brand_tier=BrandTier.NATIONAL),
            ],
        },
        coupons=(SkuCoupon('c1', 'A2', 30),),
        constraints=(LoyalSKU('A1'), BrandQuota(BrandTier.NATIONAL, 1)),
    )
    # CAT is locked on the loyal Private A1, so the repair can only move DOG
    assert constraint_aware_greedy(instance) == {'CAT': 'A1', 'DOG': 'B2'}


def test_shortcut_baselines_pick_their_signature_skus(trap: Instance):
    assert {
        'always_private': tier_cheapest_cart(trap, BrandTier.PRIVATE),
        'always_coupon_sku': couponed_cheapest_cart(trap),
        'oracle': oracle_cart(trap),
        'oracle_cost': cost(oracle_cart(trap), trap).total_cents,
    } == {
        'always_private': {'CAT': 'A1', 'DOG': 'B1'},
        'always_coupon_sku': {'CAT': 'A2', 'DOG': 'B1'},
        'oracle': {'CAT': 'A2', 'DOG': 'B1'},
        'oracle_cost': 400,
    }


def test_lowest_shelf_and_max_discount_ignore_opposite_signals(make_sku, make_instance):
    # A1: shelf 300, loyalty 100 -> net 200 ; A2: shelf 250, loyalty 0 -> net 250
    instance = make_instance(
        {
            'CAT': [
                make_sku('A1', 'CAT', shelf_cents=300, loyalty_disc_cents=100),
                make_sku('A2', 'CAT', shelf_cents=250),
            ]
        }
    )
    assert {
        'lowest_shelf': lowest_shelf_cart(instance),
        'max_discount': greedy_max_discount_cart(instance),
    } == {'lowest_shelf': {'CAT': 'A2'}, 'max_discount': {'CAT': 'A1'}}


def test_tier_baseline_falls_back_when_tier_absent(make_sku, make_instance):
    instance = make_instance(
        {
            'CAT': [
                make_sku('A1', 'CAT', shelf_cents=300, brand_tier=BrandTier.NATIONAL),
                make_sku('A2', 'CAT', shelf_cents=250, brand_tier=BrandTier.NATIONAL),
            ]
        }
    )
    assert tier_cheapest_cart(instance, BrandTier.PRIVATE) == {'CAT': 'A2'}


def test_random_cart_is_seed_deterministic_and_on_menu(trap: Instance):
    first = random_cart(trap, np.random.default_rng(7))
    second = random_cart(trap, np.random.default_rng(7))
    on_menu = all(
        code in {sku.code for sku in trap.menu[commodity]} for commodity, code in first.items()
    )
    assert {
        'stable': first == second,
        'on_menu': on_menu,
        'full': set(first) == set(trap.commodities),
    } == {
        'stable': True,
        'on_menu': True,
        'full': True,
    }


def test_real_shopper_cart_reads_info_codes():
    info: dict[str, object] = {'real_cart_codes': {'CAT': 'A1', 'DOG': 'B2'}}
    assert real_shopper_cart(info) == {'CAT': 'A1', 'DOG': 'B2'}


def test_baseline_carts_covers_every_registered_name(trap: Instance):
    carts = baseline_carts(
        trap, {'real_cart_codes': {'CAT': 'A1', 'DOG': 'B2'}}, np.random.default_rng(1)
    )
    assert sorted(carts) == [
        'always_coupon_sku',
        'always_lowest_shelf',
        'always_private',
        'constraint_aware_greedy',
        'greedy_cheapest',
        'greedy_max_discount',
        'oracle',
        'random',
        'real_shopper',
    ]
