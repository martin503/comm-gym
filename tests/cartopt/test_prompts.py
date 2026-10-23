from commgym.cartopt.instance import (
    BrandQuota,
    BrandTier,
    LoyalSKU,
    ManufacturerMultiBuy,
    SkuCoupon,
    ThresholdBundle,
)
from commgym.cartopt.prompts import messages, system_prompt, user_prompt


def _instance(make_sku, make_instance):
    return make_instance(
        {
            'CAT': [
                make_sku('A1', 'CAT', shelf_cents=200, loyalty_disc_cents=15),
                make_sku('A2', 'CAT', shelf_cents=280, brand_tier=BrandTier.NATIONAL),
            ],
            'DOG': [
                make_sku('B1', 'DOG', shelf_cents=150),
                make_sku('B2', 'DOG', shelf_cents=210, brand_tier=BrandTier.NATIONAL),
            ],
        },
        coupons=(
            SkuCoupon('K0', 'A2', 30),
            ThresholdBundle('K1', ('CAT', 'DOG'), 500, 100),
            ManufacturerMultiBuy('K2', 7, 2, 75),
        ),
        constraints=(BrandQuota(BrandTier.NATIONAL, 2), LoyalSKU('B1')),
    )


def test_system_prompt_states_pricing_and_contract(make_sku, make_instance):
    prompt = system_prompt()
    assert {
        'stable': prompt == system_prompt(),
        'pricing': 'shelf price minus loyalty discount' in prompt,
        'stacking': 'stack' in prompt,
        'one_block': 'exactly one answer block' in prompt,
        'answer_shape': '"cart": {"<category>": "<code>", ...}' in prompt,
    } == {
        'stable': True,
        'pricing': True,
        'stacking': True,
        'one_block': True,
        'answer_shape': True,
    }


def test_user_prompt_lists_menu_coupons_constraints(make_sku, make_instance):
    prompt = user_prompt(_instance(make_sku, make_instance))
    assert {
        'codes': all(code in prompt for code in ('A1', 'A2', 'B1', 'B2')),
        'categories': all(c in prompt for c in ('CAT', 'DOG')),
        'prices': '| A1 | CAT | Private | 1 | - | $2.00 | $0.15 |' in prompt,
        'sku_coupon': 'K0: $0.30 off item A2' in prompt,
        'bundle': 'K1: $1.00 off when the combined net spend on CAT, DOG reaches $5.00' in prompt,
        'multi_buy': 'K2: $0.75 off when buying at least 2 items from manufacturer 7' in prompt,
        'quota': 'buy at least 2 National-brand items' in prompt,
        'loyal': 'item B1 must be in the cart' in prompt,
    } == {
        'codes': True,
        'categories': True,
        'prices': True,
        'sku_coupon': True,
        'bundle': True,
        'multi_buy': True,
        'quota': True,
        'loyal': True,
    }


def test_user_prompt_hides_empty_sections(make_sku, make_instance):
    bare = make_instance({'CAT': [make_sku('A1', 'CAT', shelf_cents=100)]})
    assert {
        'coupons': 'Coupons:' in user_prompt(bare),
        'constraints': 'Constraints:' in user_prompt(bare),
    } == {
        'coupons': False,
        'constraints': False,
    }


def test_messages_has_system_then_user(make_sku, make_instance):
    chat = messages(_instance(make_sku, make_instance))
    assert [m['role'] for m in chat] == ['system', 'user']
