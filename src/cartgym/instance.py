from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum


class BrandTier(StrEnum):
    NATIONAL = 'National'
    PRIVATE = 'Private'


@dataclass(frozen=True, slots=True)
class MenuSKU:
    code: str
    product_id: int
    commodity: str
    brand_tier: BrandTier
    manufacturer: int
    size: str
    shelf_cents: int
    loyalty_disc_cents: int

    def __post_init__(self) -> None:
        assert self.shelf_cents > 0, f'SKU {self.code}: shelf price must be positive'
        assert 0 <= self.loyalty_disc_cents <= self.shelf_cents, (
            f'SKU {self.code}: loyalty discount must be within [0, shelf price]'
        )


@dataclass(frozen=True, slots=True)
class SkuCoupon:
    coupon_id: str
    code: str
    amount_cents: int

    def __post_init__(self) -> None:
        assert self.amount_cents > 0, f'coupon {self.coupon_id}: amount must be positive'


@dataclass(frozen=True, slots=True)
class ThresholdBundle:
    coupon_id: str
    commodities: tuple[str, ...]
    threshold_cents: int
    amount_cents: int

    def __post_init__(self) -> None:
        assert self.commodities, (
            f'coupon {self.coupon_id}: bundle must name at least one commodity'
        )
        assert self.threshold_cents > 0, f'coupon {self.coupon_id}: threshold must be positive'
        assert self.amount_cents > 0, f'coupon {self.coupon_id}: amount must be positive'


@dataclass(frozen=True, slots=True)
class ManufacturerMultiBuy:
    coupon_id: str
    manufacturer: int
    min_items: int
    amount_cents: int

    def __post_init__(self) -> None:
        assert self.min_items >= 2, f'coupon {self.coupon_id}: multi-buy needs at least 2 items'
        assert self.amount_cents > 0, f'coupon {self.coupon_id}: amount must be positive'


type Coupon = SkuCoupon | ThresholdBundle | ManufacturerMultiBuy


@dataclass(frozen=True, slots=True)
class BrandQuota:
    tier: BrandTier
    min_count: int

    def __post_init__(self) -> None:
        assert self.min_count >= 1, 'brand quota must require at least one item'


@dataclass(frozen=True, slots=True)
class LoyalSKU:
    code: str


type Constraint = BrandQuota | LoyalSKU


@dataclass(frozen=True, slots=True)
class Instance:
    commodities: tuple[str, ...]
    menu: Mapping[str, tuple[MenuSKU, ...]]
    coupons: tuple[Coupon, ...]
    constraints: tuple[Constraint, ...]

    def __post_init__(self) -> None:
        assert self.commodities, 'instance needs at least one commodity'
        assert set(self.menu) == set(self.commodities), 'menu keys must match commodities exactly'
        codes = [sku.code for skus in self.menu.values() for sku in skus]
        assert len(codes) == len(set(codes)), 'menu codes must be unique across the whole menu'
        for commodity, skus in self.menu.items():
            assert skus, f'commodity {commodity} has an empty menu'
            for sku in skus:
                assert sku.commodity == commodity, (
                    f'SKU {sku.code} listed under the wrong commodity'
                )


def is_feasible(cart: Mapping[str, str], instance: Instance) -> bool:
    """Whether a well-formed cart (one menu code per commodity) satisfies all constraints."""
    by_code = {sku.code: sku for skus in instance.menu.values() for sku in skus}
    for constraint in instance.constraints:
        match constraint:
            case BrandQuota(tier=tier, min_count=min_count):
                count = sum(1 for code in cart.values() if by_code[code].brand_tier == tier)
                if count < min_count:
                    return False
            case LoyalSKU(code=code):
                if cart[by_code[code].commodity] != code:
                    return False
    return True
