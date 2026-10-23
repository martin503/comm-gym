from collections.abc import Callable

import pytest

from commgym.cartopt.instance import BrandTier, Constraint, Coupon, Instance, MenuSKU


@pytest.fixture
def make_sku() -> Callable[..., MenuSKU]:
    def _make(
        code: str,
        commodity: str,
        *,
        shelf_cents: int,
        loyalty_disc_cents: int = 0,
        brand_tier: BrandTier = BrandTier.PRIVATE,
        manufacturer: int = 1,
    ) -> MenuSKU:
        return MenuSKU(
            code=code,
            product_id=0,
            commodity=commodity,
            brand_tier=brand_tier,
            manufacturer=manufacturer,
            size='',
            shelf_cents=shelf_cents,
            loyalty_disc_cents=loyalty_disc_cents,
        )

    return _make


@pytest.fixture
def make_instance() -> Callable[..., Instance]:
    def _make(
        menu: dict[str, list[MenuSKU]],
        coupons: tuple[Coupon, ...] = (),
        constraints: tuple[Constraint, ...] = (),
    ) -> Instance:
        return Instance(
            commodities=tuple(menu),
            menu={commodity: tuple(skus) for commodity, skus in menu.items()},
            coupons=coupons,
            constraints=constraints,
        )

    return _make
