from collections.abc import Mapping
from dataclasses import dataclass

from cartgym.instance import (
    Coupon,
    Instance,
    ManufacturerMultiBuy,
    MenuSKU,
    SkuCoupon,
    ThresholdBundle,
)


def sku_net_cents(sku: MenuSKU) -> int:
    """Net unit price after the loyalty discount, before any coupon."""
    return sku.shelf_cents - sku.loyalty_disc_cents


@dataclass(frozen=True, slots=True)
class CostResult:
    total_cents: int
    sku_nets: tuple[tuple[str, int], ...]
    applied_coupon_ids: tuple[str, ...]
    coupon_total_cents: int


def cost(cart: Mapping[str, str], instance: Instance) -> CostResult:
    """Price a full cart: shelf - loyalty - coupons (all stack, each applies once)."""
    chosen = _chosen_skus(cart, instance)
    nets = tuple((sku.code, sku_net_cents(sku)) for sku in chosen)
    base = sum(net for _, net in nets)
    applied: list[str] = []
    coupon_total = 0
    for coupon in instance.coupons:
        amount = _coupon_amount_cents(coupon, chosen)
        if amount:
            applied.append(coupon.coupon_id)
            coupon_total += amount
    total = base - coupon_total
    assert total >= 0, f'cart prices negative ({total}c): coupon amounts exceed the basket value'
    return CostResult(total, nets, tuple(applied), coupon_total)


def _chosen_skus(cart: Mapping[str, str], instance: Instance) -> tuple[MenuSKU, ...]:
    by_code = {sku.code: sku for skus in instance.menu.values() for sku in skus}
    chosen = []
    for commodity in instance.commodities:
        sku = by_code[cart[commodity]]
        assert sku.commodity == commodity, f'code {sku.code} does not belong to {commodity}'
        chosen.append(sku)
    return tuple(chosen)


def _coupon_amount_cents(coupon: Coupon, chosen: tuple[MenuSKU, ...]) -> int:
    """Discount owed by one coupon; bundle spend counts pre-coupon net totals."""
    match coupon:
        case SkuCoupon(code=code, amount_cents=amount):
            return amount if any(sku.code == code for sku in chosen) else 0
        case ThresholdBundle(
            commodities=commodities, threshold_cents=threshold, amount_cents=amount
        ):
            spend = sum(sku_net_cents(sku) for sku in chosen if sku.commodity in commodities)
            return amount if spend >= threshold else 0
        case ManufacturerMultiBuy(
            manufacturer=manufacturer, min_items=min_items, amount_cents=amount
        ):
            count = sum(1 for sku in chosen if sku.manufacturer == manufacturer)
            return amount if count >= min_items else 0
