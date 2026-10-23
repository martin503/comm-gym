import itertools

import numpy as np

from commgym.cartopt.instance import (
    BrandQuota,
    BrandTier,
    Constraint,
    Coupon,
    Instance,
    LoyalSKU,
    ManufacturerMultiBuy,
    MenuSKU,
    SkuCoupon,
    ThresholdBundle,
)
from commgym.cartopt.pricing import cost
from commgym.cartopt.solver import optimal_cart, solve


def _random_skus(rng: np.random.Generator, commodity: str, prefix: str) -> list[MenuSKU]:
    skus = []
    for i in range(int(rng.integers(2, 5))):
        shelf = int(rng.integers(100, 1000))
        skus.append(
            MenuSKU(
                code=f'{prefix}{i}',
                product_id=0,
                commodity=commodity,
                brand_tier=BrandTier.NATIONAL if rng.random() < 0.5 else BrandTier.PRIVATE,
                manufacturer=int(rng.integers(1, 4)),
                size='',
                shelf_cents=shelf,
                loyalty_disc_cents=int(rng.integers(0, shelf // 2 + 1)),
            )
        )
    return skus


def _random_coupons(
    rng: np.random.Generator,
    menu: dict[str, list[MenuSKU]],
    commodities: list[str],
    min_base: int,
) -> tuple[Coupon, ...]:
    coupons: list[Coupon] = []
    cap = max(1, min_base // 3)
    for kind in rng.choice(
        ['sku', 'bundle', 'multibuy', None], size=3, p=[0.35, 0.25, 0.25, 0.15]
    ):
        if kind is None:
            continue
        if kind == 'sku':
            commodity = commodities[int(rng.integers(0, len(commodities)))]
            sku = menu[commodity][int(rng.integers(0, len(menu[commodity])))]
            coupons.append(SkuCoupon(f'K{len(coupons)}', sku.code, int(rng.integers(1, cap + 1))))
        elif kind == 'bundle' and len(commodities) >= 2:
            picked = [str(c) for c in rng.choice(commodities, size=2, replace=False)]
            nets = [[s.shelf_cents - s.loyalty_disc_cents for s in menu[c]] for c in picked]
            spend_min, spend_max = sum(min(n) for n in nets), sum(max(n) for n in nets)
            coupons.append(
                ThresholdBundle(
                    f'K{len(coupons)}',
                    tuple(picked),
                    int(rng.integers(spend_min, spend_max + 1)),
                    int(rng.integers(1, cap + 1)),
                )
            )
        elif kind == 'multibuy':
            coupons.append(
                ManufacturerMultiBuy(
                    f'K{len(coupons)}', int(rng.integers(1, 4)), 2, int(rng.integers(1, cap + 1))
                )
            )
    return tuple(coupons)


def _random_constraints(
    rng: np.random.Generator, menu: dict[str, list[MenuSKU]], commodities: list[str]
) -> tuple[Constraint, ...]:
    constraints: list[Constraint] = []
    all_skus = [sku for skus in menu.values() for sku in skus]
    if rng.random() < 0.4:
        tier = BrandTier.PRIVATE if rng.random() < 0.5 else BrandTier.NATIONAL
        max_count = sum(1 for s in all_skus if s.brand_tier == tier)
        if max_count >= 1:
            constraints.append(BrandQuota(tier, int(rng.integers(1, max_count + 1))))
    if rng.random() < 0.3:
        commodity = commodities[int(rng.integers(0, len(commodities)))]
        sku = menu[commodity][int(rng.integers(0, len(menu[commodity])))]
        constraints.append(LoyalSKU(sku.code))
    return tuple(constraints)


def _random_instance(rng: np.random.Generator) -> Instance:
    commodities = [f'CAT{j}' for j in range(int(rng.integers(1, 4)))]
    menu = {c: _random_skus(rng, c, f'S{j}') for j, c in enumerate(commodities)}
    min_base = sum(
        min(s.shelf_cents - s.loyalty_disc_cents for s in skus) for skus in menu.values()
    )
    return Instance(
        commodities=tuple(commodities),
        menu={c: tuple(skus) for c, skus in menu.items()},
        coupons=_random_coupons(rng, menu, commodities, min_base),
        constraints=_random_constraints(rng, menu, commodities),
    )


def _reference_feasible(
    cart: dict[str, str], instance: Instance, by_code: dict[str, MenuSKU]
) -> bool:
    for constraint in instance.constraints:
        match constraint:
            case BrandQuota(tier=tier, min_count=min_count):
                if (
                    sum(1 for code in cart.values() if by_code[code].brand_tier == tier)
                    < min_count
                ):
                    return False
            case LoyalSKU(code=code):
                if cart[by_code[code].commodity] != code:
                    return False
    return True


def _reference(instance: Instance) -> tuple[list[int], list[bool]]:
    by_code = {sku.code: sku for skus in instance.menu.values() for sku in skus}
    codes = [[sku.code for sku in instance.menu[c]] for c in instance.commodities]
    costs: list[int] = []
    feasible: list[bool] = []
    for combo in itertools.product(*codes):
        cart = dict(zip(instance.commodities, combo, strict=True))
        costs.append(cost(cart, instance).total_cents)
        feasible.append(_reference_feasible(cart, instance, by_code))
    return costs, feasible


def test_solver_matches_reference_on_random_instances():
    rng = np.random.default_rng(7)
    for _ in range(20):
        instance = _random_instance(rng)
        solution = solve(instance)
        ref_costs, ref_feasible = _reference(instance)
        assert solution.n_carts == len(ref_costs)
        np.testing.assert_array_equal(solution.costs_cents, np.asarray(ref_costs, dtype=np.int64))
        np.testing.assert_array_equal(solution.feasible, np.asarray(ref_feasible))
        if solution.n_feasible > 0:
            ref_c_star = min(c for c, f in zip(ref_costs, ref_feasible, strict=True) if f)
            assert solution.c_star_cents() == ref_c_star


def test_optimal_cart_is_cheapest_feasible(make_sku, make_instance):
    cat_a = make_sku('A1', 'CAT', shelf_cents=100, brand_tier=BrandTier.PRIVATE)
    cat_b = make_sku('A2', 'CAT', shelf_cents=300, brand_tier=BrandTier.NATIONAL)
    dog_a = make_sku('B1', 'DOG', shelf_cents=200, brand_tier=BrandTier.PRIVATE)
    dog_b = make_sku('B2', 'DOG', shelf_cents=150, brand_tier=BrandTier.NATIONAL)
    instance = make_instance(
        {'CAT': [cat_a, cat_b], 'DOG': [dog_a, dog_b]},
        constraints=(BrandQuota(BrandTier.NATIONAL, 1),),
    )
    solution = solve(instance)
    cart = optimal_cart(instance, solution)
    # cheapest overall (A1+B1=300) has no National item; cheapest feasible is A1+B2=250
    assert {
        'cart': cart,
        'cost': cost(cart, instance).total_cents,
        'c_star': solution.c_star_cents(),
    } == {
        'cart': {'CAT': 'A1', 'DOG': 'B2'},
        'cost': 250,
        'c_star': 250,
    }
