from commgym.cartopt.instance import (
    BrandQuota,
    Constraint,
    Coupon,
    Instance,
    LoyalSKU,
    ManufacturerMultiBuy,
    MenuSKU,
    SkuCoupon,
    ThresholdBundle,
)

MENU_HEADER = '| code | category | brand | manufacturer | size | shelf price | loyalty disc |'
MENU_RULE = '|---|---|---|---|---|---|---|'


def messages(instance: Instance) -> list[dict[str, str]]:
    """Chat messages for one instance, ready for an OpenAI-compatible client."""
    return [
        {'role': 'system', 'content': system_prompt()},
        {'role': 'user', 'content': user_prompt(instance)},
    ]


def system_prompt() -> str:
    return (
        'You are a careful grocery shopper optimizing a shopping basket.\n'
        '\n'
        "Pricing: every item has a shelf price and a loyalty discount; an item's net price is\n"
        'shelf price minus loyalty discount. Coupons stack — each coupon whose condition is met\n'
        'applies exactly once, subtracted from the sum of net prices. Bundle thresholds count\n'
        'the net prices of the named categories before any coupon. All amounts are in dollars;\n'
        'round to cents only at the end.\n'
        '\n'
        'Pick exactly one item per category on the shopping list to minimize your total\n'
        'out-of-pocket cost while respecting every stated constraint.\n'
        '\n'
        'Think briefly, then end your reply with exactly one answer block:\n'
        '<answer>{"cart": {"<category>": "<code>", ...}, "total": <dollars>}</answer>\n'
        'The cart must cover every listed category exactly once; total is your final\n'
        'out-of-pocket total in dollars.'
    )


def user_prompt(instance: Instance) -> str:
    lines = [
        'Shopping list (pick exactly one item per category):',
        *[f'- {commodity}' for commodity in instance.commodities],
        '',
        'Menu:',
        MENU_HEADER,
        MENU_RULE,
        *[_menu_row(sku) for skus in instance.menu.values() for sku in skus],
    ]
    if instance.coupons:
        lines += ['', 'Coupons:', *[f'- {_coupon_line(coupon)}' for coupon in instance.coupons]]
    if instance.constraints:
        lines += [
            '',
            'Constraints:',
            *[f'- {_constraint_line(constraint)}' for constraint in instance.constraints],
        ]
    lines += ['', 'Choose the cheapest valid cart.']
    return '\n'.join(lines)


def _menu_row(sku: MenuSKU) -> str:
    size = sku.size or '-'
    return (
        f'| {sku.code} | {sku.commodity} | {sku.brand_tier.value} | {sku.manufacturer} '
        f'| {size} | {_dollars(sku.shelf_cents)} | {_dollars(sku.loyalty_disc_cents)} |'
    )


def _coupon_line(coupon: Coupon) -> str:
    match coupon:
        case SkuCoupon(coupon_id=coupon_id, code=code, amount_cents=amount):
            return f'{coupon_id}: {_dollars(amount)} off item {code}'
        case ThresholdBundle(
            coupon_id=coupon_id,
            commodities=commodities,
            threshold_cents=threshold,
            amount_cents=amount,
        ):
            scope = ', '.join(commodities)
            return (
                f'{coupon_id}: {_dollars(amount)} off when the combined net spend '
                f'on {scope} reaches {_dollars(threshold)}'
            )
        case ManufacturerMultiBuy(
            coupon_id=coupon_id,
            manufacturer=manufacturer,
            min_items=min_items,
            amount_cents=amount,
        ):
            item = 'item' if min_items == 1 else 'items'
            return (
                f'{coupon_id}: {_dollars(amount)} off when buying at least {min_items} {item} '
                f'from manufacturer {manufacturer}'
            )


def _constraint_line(constraint: Constraint) -> str:
    match constraint:
        case BrandQuota(tier=tier, min_count=min_count):
            item = 'item' if min_count == 1 else 'items'
            return f'buy at least {min_count} {tier.value}-brand {item}'
        case LoyalSKU(code=code):
            return f'item {code} must be in the cart (loyalty program requirement)'


def _dollars(cents: int) -> str:
    return f'${cents / 100:.2f}'
