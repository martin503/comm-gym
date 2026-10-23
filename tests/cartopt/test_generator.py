import json
from dataclasses import asdict, replace

import numpy as np
import pandas as pd
import pytest

from commgym.cartopt.config import LevelConfig, LevelsConfig
from commgym.cartopt.generator import (
    GeneratorContext,
    _cap_coupon_amounts,
    build_generator_context,
    evaluate_instance,
    generate_batch,
    greedy_cheapest_cart,
    instance_to_record,
    record_to_instance,
)
from commgym.cartopt.instance import (
    BrandQuota,
    BrandTier,
    Coupon,
    LoyalSKU,
    ManufacturerMultiBuy,
    MenuSKU,
    SkuCoupon,
)
from commgym.cartopt.solver import solve
from commgym.dunnhumby.clean import prepare_transactions
from commgym.dunnhumby.config import CleaningConfig, PricingConfig
from commgym.dunnhumby.load import Campaign, Product
from commgym.dunnhumby.prices import build_price_table
from commgym.dunnhumby.splits import CampaignCalendar, Splits, SplitSpec

PRODUCT_PRICES = {
    # product_id: (sales_value, retail_disc) per unit at quantity 1
    101: (2.00, 0.00),
    102: (2.50, 0.20),
    103: (1.50, 0.00),
    104: (3.00, 0.50),
    201: (1.80, 0.00),
    202: (1.20, 0.20),
    203: (2.20, 0.00),
    204: (1.00, 0.00),
    301: (2.00, 0.00),
    302: (2.60, 0.20),
    303: (1.40, 0.00),
    304: (2.80, 0.00),
}

PRODUCTS = [
    Product.model_validate(
        {
            'PRODUCT_ID': pid,
            'MANUFACTURER': (pid // 100) % 3 + 1,
            'DEPARTMENT': 'GROCERY',
            'BRAND': 'Private' if pid % 2 == 1 else 'National',
            'COMMODITY_DESC': f'CAT-{pid // 100}',
            'SUB_COMMODITY_DESC': f'SUB-{pid // 100}1',
            'CURR_SIZE_OF_PRODUCT': '1 LB',
        }
    )
    for pid in PRODUCT_PRICES
]

# household 1, day 250: history before the day-281 anchors
# lines 101 (Private), 102 (National), 201 (Private) -> private share 2/3
MINI_LINES = [
    (1, 900, 250, 101),
    (1, 900, 250, 102),
    (1, 900, 250, 201),
    (1, 1001, 281, 101),
    (1, 1001, 281, 201),
    (1, 1001, 281, 301),
    (1, 1002, 281, 102),
    (1, 1002, 281, 202),
    (1, 1002, 281, 302),
    (1, 1003, 281, 103),
    (1, 1003, 281, 203),
    (1, 1003, 281, 303),
    (1, 1004, 281, 104),
    (1, 1004, 281, 204),
    (1, 1004, 281, 304),
    (1, 1005, 281, 101),
    (1, 1005, 281, 203),
    (1, 1005, 281, 302),
    (1, 1006, 281, 102),
    (1, 1006, 281, 204),
    (1, 1006, 281, 303),
]

LEVELS = LevelsConfig(
    levels={
        'T1': LevelConfig(categories=2, skus_per_category=3, sku_coupons=(1, 2)),
        'T2': LevelConfig(
            categories=2,
            skus_per_category=3,
            sku_coupons=(1, 1),
            threshold_bundles=1,
            brand_quota=True,
        ),
    }
)

SPLITS = Splits(
    train=SplitSpec('train', frozenset({2}), 36, 41),
    dev=SplitSpec('dev', frozenset({1}), 36, 41),
    eval_unseen=SplitSpec('eval_unseen', frozenset({1}), 42, 45),
    eval_known=SplitSpec('eval_known', frozenset({2}), 42, 45),
    heldout_commodities=frozenset(),
)

EVAL_CFG = LevelsConfig(
    levels={'T': LevelConfig(categories=2, skus_per_category=2, sku_coupons=(0, 0))}
)


@pytest.fixture(scope='module')
def context() -> GeneratorContext:
    tx = _mini_tx()
    txc, _ = prepare_transactions(tx, PRODUCTS, CleaningConfig())
    prices = build_price_table(txc, PricingConfig())
    campaign = Campaign.model_validate(
        {'DESCRIPTION': 'TypeA', 'CAMPAIGN': 1, 'START_DAY': 270, 'END_DAY': 300}
    )
    calendar = CampaignCalendar((campaign,))
    return build_generator_context(
        txc,
        PRODUCTS,
        prices,
        calendar,
        {102: {1}},
        {1: {1}},
        np.array([50, 100, 150]),
        SPLITS,
        LEVELS,
    )


def _mini_tx() -> pd.DataFrame:
    rows = []
    for household, basket, day, product_id in MINI_LINES:
        sales, retail = PRODUCT_PRICES[product_id]
        rows.append(
            {
                'household_key': household,
                'BASKET_ID': basket,
                'DAY': day,
                'PRODUCT_ID': product_id,
                'QUANTITY': 1,
                'SALES_VALUE': sales,
                'STORE_ID': 364,
                'RETAIL_DISC': -retail,
                'TRANS_TIME': 1200,
                'WEEK_NO': (day - 1) // 7 + 1,
                'COUPON_DISC': 0.0,
                'COUPON_MATCH_DISC': 0.0,
            }
        )
    return pd.DataFrame(rows)


def test_generated_instances_are_valid_and_deterministic(context: GeneratorContext):
    batch = generate_batch(context, 'T1', 'dev', n=3, seed=5)
    repeat = generate_batch(context, 'T1', 'dev', n=3, seed=5)
    assert len(batch.instances) == 3
    for generated in batch.instances:
        instance = generated.instance
        codes = [sku.code for skus in instance.menu.values() for sku in skus]
        menu_ids = {sku.product_id for skus in instance.menu.values() for sku in skus}
        bought = generated.info['bought_products']
        assert isinstance(bought, dict)
        assert {
            'menu_sizes': {len(skus) for skus in instance.menu.values()},
            'n_categories': len(instance.commodities),
            'n_unique_codes': len(set(codes)),
            'c_star_matches_solver': solve(instance).c_star_cents()
            == generated.info['c_star_cents'],
            'bought_products_in_menu': set(bought.values()).issubset(menu_ids),
        } == {
            'menu_sizes': {3},
            'n_categories': 2,
            'n_unique_codes': 6,
            'c_star_matches_solver': True,
            'bought_products_in_menu': True,
        }

    def _digest(generated_batch) -> list[object]:
        return [
            (
                generated.info['c_star_cents'],
                [sku.code for skus in generated.instance.menu.values() for sku in skus],
            )
            for generated in generated_batch.instances
        ]

    assert {
        'unique_baskets': len({generated.info['basket'] for generated in batch.instances}),
        'deterministic': _digest(batch) == _digest(repeat),
    } == {'unique_baskets': 3, 'deterministic': True}


def test_brand_quota_derived_from_history(context: GeneratorContext):
    batch = generate_batch(context, 'T2', 'dev', n=2, seed=7)
    for generated in batch.instances:
        quotas = [c for c in generated.instance.constraints if isinstance(c, BrandQuota)]
        # private share 2/3 before day 281 -> round(2/3 * 2) = 1 required private item
        assert [(q.tier, q.min_count) for q in quotas] == [(BrandTier.PRIVATE, 1)]


def test_heldout_categories_never_sampled(context: GeneratorContext):
    heldout_ctx = replace(
        context, splits=replace(SPLITS, heldout_commodities=frozenset({'CAT-1'}))
    )
    batch = generate_batch(heldout_ctx, 'T1', 'dev', n=2, seed=5)
    for generated in batch.instances:
        assert 'CAT-1' not in generated.instance.commodities


def test_record_round_trip_preserves_instance(context: GeneratorContext):
    batch = generate_batch(context, 'T2', 'dev', n=1, seed=7)
    record = json.loads(json.dumps(instance_to_record(batch.instances[0])))
    assert record_to_instance(record) == batch.instances[0].instance


def test_record_to_instance_parses_eval_only_rules(make_sku):
    record = {
        'instance': {
            'commodities': ['CAT'],
            'menu': {
                'CAT': [
                    json.loads(json.dumps(asdict(make_sku('A1', 'CAT', shelf_cents=100))))
                    | {'brand_tier': 'Private'}
                ]
            },
            'coupons': [
                {
                    'kind': 'ManufacturerMultiBuy',
                    'coupon_id': 'm1',
                    'manufacturer': 1,
                    'min_items': 2,
                    'amount_cents': 40,
                }
            ],
            'constraints': [{'kind': 'LoyalSKU', 'code': 'A1'}],
        }
    }
    instance = record_to_instance(record)
    assert {
        'coupons': instance.coupons,
        'constraints': instance.constraints,
        'menu_sizes': {len(skus) for skus in instance.menu.values()},
    } == {
        'coupons': (ManufacturerMultiBuy('m1', 1, 2, 40),),
        'constraints': (LoyalSKU('A1'),),
        'menu_sizes': {1},
    }


def test_evaluate_instance_accepts_traps_and_rejects_degenerates(make_sku, make_instance):
    trap = make_instance(
        {
            'CAT': [
                make_sku('A1', 'CAT', shelf_cents=100, brand_tier=BrandTier.PRIVATE),
                make_sku('A2', 'CAT', shelf_cents=300, brand_tier=BrandTier.NATIONAL),
            ],
            'DOG': [
                make_sku('B1', 'DOG', shelf_cents=150, brand_tier=BrandTier.PRIVATE),
                make_sku('B2', 'DOG', shelf_cents=200, brand_tier=BrandTier.NATIONAL),
            ],
        },
        constraints=(BrandQuota(BrandTier.NATIONAL, 1),),
    )
    # best non-optimal cart (A2+B1=205c) sits 5c above C*, inside the 10c near-tie band
    near_tie = make_instance(
        {
            'CAT': [
                make_sku('A1', 'CAT', shelf_cents=100),
                make_sku('A2', 'CAT', shelf_cents=105),
            ],
            'DOG': [
                make_sku('B1', 'DOG', shelf_cents=100),
                make_sku('B2', 'DOG', shelf_cents=200),
            ],
        }
    )
    all_tie = make_instance({'CAT': [make_sku('A1', 'CAT', shelf_cents=100)]})

    def stats(instance):
        return evaluate_instance(
            instance, solve(instance), greedy_cheapest_cart(instance), EVAL_CFG
        )

    trap_stats = stats(trap)
    # greedy on the trap (A1+B1=250c) has no National item; cheapest feasible is
    # A1+B2=300c, so the greedy cart is cheaper but infeasible: negative gap
    assert {
        'trap_accept': trap_stats.accept,
        'trap_reason': trap_stats.reject_reason,
        'trap': trap_stats.is_trap,
        'trap_gap': trap_stats.greedy_gap_cents,
        'trap_binding': trap_stats.binding_rules,
        'near_tie': (stats(near_tie).accept, stats(near_tie).reject_reason),
        'all_tie': (stats(all_tie).accept, stats(all_tie).reject_reason),
    } == {
        'trap_accept': True,
        'trap_reason': None,
        'trap': True,
        'trap_gap': -50,
        'trap_binding': ('quota:National',),
        'near_tie': (False, 'near_tie'),
        'all_tie': (False, 'all_carts_tie'),
    }


def test_gap_cap_caps_only_flip_inducing_coupons(make_sku):
    # A2 net 250 vs A1 net 100 -> gap 150; a 200c coupon would flip the ranking (50 < 100),
    # capping to 150-30=120 leaves A2 post-coupon at 130, i.e. 30c above the alternative
    menu: dict[str, tuple[MenuSKU, ...]] = {
        'CAT': (
            make_sku('A1', 'CAT', shelf_cents=100),
            make_sku('A2', 'CAT', shelf_cents=250),
        )
    }
    cfg = LevelsConfig(levels={}, near_tie_delta_cents=10, gap_cap_margin_cents=(30, 30))
    on = LevelConfig(
        categories=1, skus_per_category=2, sku_coupons=(1, 1), coupon_gap_cap_prob=1.0
    )
    off = LevelConfig(categories=1, skus_per_category=2, sku_coupons=(1, 1))
    flip: list[Coupon] = [SkuCoupon('K0', 'A2', 200)]
    small: list[Coupon] = [SkuCoupon('K0', 'A2', 80)]  # below the 150c gap already
    skip: list[Coupon] = [SkuCoupon('K0', 'A2', 200)]
    _cap_coupon_amounts(flip, menu, on, cfg, np.random.default_rng(0))
    _cap_coupon_amounts(small, menu, on, cfg, np.random.default_rng(0))
    _cap_coupon_amounts(skip, menu, off, cfg, np.random.default_rng(0))
    assert {'capped': flip, 'already_small': small, 'prob_zero': skip} == {
        'capped': [SkuCoupon('K0', 'A2', 120)],
        'already_small': [SkuCoupon('K0', 'A2', 80)],
        'prob_zero': [SkuCoupon('K0', 'A2', 200)],
    }
