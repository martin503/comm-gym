from collections.abc import Mapping

import numpy as np

from commgym.cartopt.generator import greedy_cheapest_cart
from commgym.cartopt.instance import BrandQuota, BrandTier, Instance, LoyalSKU, MenuSKU, SkuCoupon
from commgym.cartopt.pricing import sku_net_cents
from commgym.cartopt.solver import optimal_cart, solve

SHORTCUT_BASELINES = ('always_private', 'always_coupon_sku', 'always_lowest_shelf')


def baseline_carts(
    instance: Instance, info: Mapping[str, object], rng: np.random.Generator
) -> dict[str, dict[str, str]]:
    """Every baseline's cart for one instance; graded through the shared reward downstream."""
    return {
        'random': random_cart(instance, rng),
        'greedy_cheapest': greedy_cheapest_cart(instance),
        'greedy_max_discount': greedy_max_discount_cart(instance),
        'constraint_aware_greedy': constraint_aware_greedy(instance),
        'always_private': tier_cheapest_cart(instance, BrandTier.PRIVATE),
        'always_coupon_sku': couponed_cheapest_cart(instance),
        'always_lowest_shelf': lowest_shelf_cart(instance),
        'real_shopper': real_shopper_cart(info),
        'oracle': oracle_cart(instance),
    }


def random_cart(instance: Instance, rng: np.random.Generator) -> dict[str, str]:
    """One uniformly random SKU per category, ignoring constraints."""
    return {
        commodity: instance.menu[commodity][int(rng.integers(len(instance.menu[commodity])))].code
        for commodity in instance.commodities
    }


def greedy_max_discount_cart(instance: Instance) -> dict[str, str]:
    """Largest loyalty discount per category, ignoring everything else."""
    return {
        commodity: max(instance.menu[commodity], key=lambda sku: sku.loyalty_disc_cents).code
        for commodity in instance.commodities
    }


def lowest_shelf_cart(instance: Instance) -> dict[str, str]:
    """Lowest shelf price per category, ignoring the loyalty discount (the shortcut it polices)."""
    return {
        commodity: min(instance.menu[commodity], key=lambda sku: sku.shelf_cents).code
        for commodity in instance.commodities
    }


def tier_cheapest_cart(instance: Instance, tier: BrandTier) -> dict[str, str]:
    """Cheapest SKU of the tier per category; falls back to the cheapest overall when absent."""
    return {
        commodity: min(_of_tier_or_all(instance.menu[commodity], tier), key=sku_net_cents).code
        for commodity in instance.commodities
    }


def couponed_cheapest_cart(instance: Instance) -> dict[str, str]:
    """Cheapest SKU carrying an SKU coupon per category; falls back to the cheapest overall."""
    couponed = {c.code for c in instance.coupons if isinstance(c, SkuCoupon)}

    def pool(skus: tuple[MenuSKU, ...]) -> tuple[MenuSKU, ...]:
        preferred = tuple(sku for sku in skus if sku.code in couponed)
        return preferred or skus

    return {
        commodity: min(pool(instance.menu[commodity]), key=sku_net_cents).code
        for commodity in instance.commodities
    }


def constraint_aware_greedy(instance: Instance) -> dict[str, str]:
    """Cheapest per category, loyal SKUs forced, then brand-quota repair by smallest premium."""
    by_code = {sku.code: sku for skus in instance.menu.values() for sku in skus}
    loyal = {
        by_code[c.code].commodity: c.code for c in instance.constraints if isinstance(c, LoyalSKU)
    }
    cart = {
        commodity: loyal.get(commodity) or min(instance.menu[commodity], key=sku_net_cents).code
        for commodity in instance.commodities
    }
    for quota in [c for c in instance.constraints if isinstance(c, BrandQuota)]:
        deficit = quota.min_count - _tier_count(cart, quota, by_code)
        if deficit > 0:
            _repair_quota(cart, instance, quota, loyal, by_code, deficit)
    return cart


def oracle_cart(instance: Instance) -> dict[str, str]:
    """The solver's cheapest feasible cart; sanity check that reward = 1."""
    return optimal_cart(instance, solve(instance))


def real_shopper_cart(info: Mapping[str, object]) -> dict[str, str]:
    """The household's actual purchased SKUs (already on every menu by construction)."""
    codes = info.get('real_cart_codes')
    assert isinstance(codes, dict), 'record info lacks real_cart_codes'
    return {str(commodity): str(code) for commodity, code in codes.items()}


def _of_tier_or_all(skus: tuple[MenuSKU, ...], tier: BrandTier) -> tuple[MenuSKU, ...]:
    of_tier = tuple(sku for sku in skus if sku.brand_tier == tier)
    return of_tier or skus


def _tier_count(cart: dict[str, str], quota: BrandQuota, by_code: dict[str, MenuSKU]) -> int:
    return sum(1 for code in cart.values() if by_code[code].brand_tier == quota.tier)


def _repair_quota(
    cart: dict[str, str],
    instance: Instance,
    quota: BrandQuota,
    loyal: dict[str, str],
    by_code: dict[str, MenuSKU],
    deficit: int,
) -> None:
    """Swap non-tier picks to the tier by smallest net premium, never touching loyal picks."""
    swaps: list[tuple[int, str, str]] = []
    for commodity, skus in instance.menu.items():
        if commodity in loyal or by_code[cart[commodity]].brand_tier == quota.tier:
            continue
        tier_skus = [sku for sku in skus if sku.brand_tier == quota.tier]
        if tier_skus:
            best = min(tier_skus, key=sku_net_cents)
            premium = sku_net_cents(best) - sku_net_cents(by_code[cart[commodity]])
            swaps.append((premium, commodity, best.code))
    for _, commodity, code in sorted(swaps)[:deficit]:
        cart[commodity] = code
