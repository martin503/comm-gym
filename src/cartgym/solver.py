from dataclasses import dataclass

import numpy as np

from cartgym.instance import (
    BrandQuota,
    Coupon,
    Instance,
    LoyalSKU,
    ManufacturerMultiBuy,
    SkuCoupon,
    ThresholdBundle,
)
from cartgym.pricing import sku_net_cents

DEFAULT_MAX_CARTS = 1_000_000


@dataclass(frozen=True, slots=True)
class Solution:
    costs_cents: np.ndarray
    feasible: np.ndarray
    n_carts: int
    n_feasible: int

    def c_star_cents(self) -> int:
        """Cheapest feasible cart cost; instances with no feasible cart are rejected upstream."""
        assert self.n_feasible > 0, 'no feasible cart in this instance'
        return int(self.costs_cents[self.feasible].min())

    def c_ref_cents(self) -> int:
        """Median feasible cart cost; the reward's optimality reference."""
        assert self.n_feasible > 0, 'no feasible cart in this instance'
        return int(round(float(np.median(self.costs_cents[self.feasible]))))


def solve(instance: Instance, *, max_carts: int = DEFAULT_MAX_CARTS) -> Solution:
    """Brute-force every cart (one SKU per commodity) with vectorized pricing and feasibility."""
    sizes = tuple(len(instance.menu[c]) for c in instance.commodities)
    n_carts = int(np.prod(sizes))
    if n_carts > max_carts:
        raise ValueError(f'{n_carts} carts exceed the brute-force cap of {max_carts}')
    choice = _choice_matrix(sizes)
    totals = _base_totals(instance, choice) - _coupon_discounts(instance, choice)
    feasible = _feasibility_mask(instance, choice)
    return Solution(totals, feasible, n_carts, int(feasible.sum()))


def optimal_cart(instance: Instance, solution: Solution, eps_cents: int = 1) -> dict[str, str]:
    """A cheapest feasible cart as commodity -> code (first of the ties)."""
    c_star = solution.c_star_cents()
    feasible_idx = np.flatnonzero(solution.feasible)
    best = feasible_idx[solution.costs_cents[feasible_idx] <= c_star + eps_cents]
    return cart_at(instance, int(best[0]))


def cart_at(instance: Instance, index: int) -> dict[str, str]:
    """Map a row of the enumerated cart space back to commodity -> code."""
    sizes = tuple(len(instance.menu[c]) for c in instance.commodities)
    positions = np.unravel_index(index, sizes)
    return {
        commodity: instance.menu[commodity][int(pos)].code
        for commodity, pos in zip(instance.commodities, positions, strict=True)
    }


def _choice_matrix(sizes: tuple[int, ...]) -> np.ndarray:
    grids = np.meshgrid(*[np.arange(size) for size in sizes], indexing='ij')
    return np.stack([grid.ravel() for grid in grids], axis=-1)


def _base_totals(instance: Instance, choice: np.ndarray) -> np.ndarray:
    totals = np.zeros(choice.shape[0], dtype=np.int64)
    for j, commodity in enumerate(instance.commodities):
        totals += _nets_array(instance, commodity)[choice[:, j]]
    return totals


def _coupon_discounts(instance: Instance, choice: np.ndarray) -> np.ndarray:
    commodity_pos = {c: j for j, c in enumerate(instance.commodities)}
    discounts = np.zeros(choice.shape[0], dtype=np.int64)
    for coupon in instance.coupons:
        mask = _coupon_mask(coupon, instance, choice, commodity_pos)
        discounts += np.where(mask, coupon.amount_cents, 0)
    return discounts


def _coupon_mask(
    coupon: Coupon,
    instance: Instance,
    choice: np.ndarray,
    commodity_pos: dict[str, int],
) -> np.ndarray:
    match coupon:
        case SkuCoupon(code=code):
            j, pos = _sku_location(instance, code)
            return choice[:, j] == pos
        case ThresholdBundle(commodities=commodities, threshold_cents=threshold):
            spend = np.zeros(choice.shape[0], dtype=np.int64)
            for commodity in commodities:
                assert commodity in commodity_pos, (
                    f'bundle names {commodity}, not on the shopping list'
                )
                spend += _nets_array(instance, commodity)[choice[:, commodity_pos[commodity]]]
            return spend >= threshold
        case ManufacturerMultiBuy(manufacturer=manufacturer, min_items=min_items):
            count = np.zeros(choice.shape[0], dtype=np.int64)
            for j, commodity in enumerate(instance.commodities):
                for pos, sku in enumerate(instance.menu[commodity]):
                    if sku.manufacturer == manufacturer:
                        count += (choice[:, j] == pos).astype(np.int64)
            return count >= min_items


def _feasibility_mask(instance: Instance, choice: np.ndarray) -> np.ndarray:
    feasible = np.ones(choice.shape[0], dtype=bool)
    for constraint in instance.constraints:
        match constraint:
            case BrandQuota(tier=tier, min_count=min_count):
                count = np.zeros(choice.shape[0], dtype=np.int64)
                for j, commodity in enumerate(instance.commodities):
                    for pos, sku in enumerate(instance.menu[commodity]):
                        if sku.brand_tier == tier:
                            count += (choice[:, j] == pos).astype(np.int64)
                feasible &= count >= min_count
            case LoyalSKU(code=code):
                j, pos = _sku_location(instance, code)
                feasible &= choice[:, j] == pos
    return feasible


def _nets_array(instance: Instance, commodity: str) -> np.ndarray:
    nets = [sku_net_cents(sku) for sku in instance.menu[commodity]]
    return np.array(nets, dtype=np.int64)


def _sku_location(instance: Instance, code: str) -> tuple[int, int]:
    for j, commodity in enumerate(instance.commodities):
        for pos, sku in enumerate(instance.menu[commodity]):
            if sku.code == code:
                return j, pos
    raise AssertionError(f'code {code} is not on the menu')
