import zlib

import numpy as np

from commgym.offer.instance import OfferCoupon, OfferInstance
from commgym.offer.lexicon import Lexicon

SYSTEM_TEMPLATE = """You write push notifications for a grocery chain. You are given a
household's purchase profile and the coupons live for that household this week. Pick the
1 to 3 coupons that best match the household and write one push message about them.

Rules:
- at most {max_words} words in the message
- no numbers, prices, or percentages of any kind
- mention only product categories covered by the coupons you select
- say an offer ends soon only if a coupon you select is flagged as ending soon
- store brand or national brand claims must match the coupon you select
- never invent brand or product names; none are known

Think briefly, then end your reply with exactly one answer block:
<answer>{{"selected": ["k03", "k11"], "message": "..."}}</answer>"""


def system_prompt(max_words: int) -> str:
    return SYSTEM_TEMPLATE.format(max_words=max_words)


def user_prompt(instance: OfferInstance, level: str, lexicon: Lexicon) -> str:
    lines = ['## Household profile']
    top = ', '.join(
        f'{lexicon.displays.get(entry.commodity, entry.commodity)} '
        f'({entry.count} purchases, {entry.store_share:.0%} store brand)'
        for entry in instance.profile.top
    )
    lines += [
        f'- top purchases: {top or "none"}',
        f'- store-brand share overall: {instance.profile.overall_store_share:.0%}',
        f'- grocery trips per week: {instance.profile.trips_per_week}',
        '',
        '## Coupons live for this household',
        '',
        '| code | covers | brand tier | ends soon |',
        '|---|---|---|---|',
    ]
    for coupon in _display_order(instance, level):
        covers = ', '.join(
            lexicon.displays.get(commodity, commodity) for commodity in coupon.top_commodities
        )
        ends = 'ends soon' if coupon.ends_soon else ''
        lines.append(f'| {coupon.code} | {covers} | {coupon.tier} | {ends} |')
    lines += ['', 'Select 1 to 3 coupons and write the message.']
    return '\n'.join(lines)


def _display_order(instance: OfferInstance, level: str) -> tuple[OfferCoupon, ...]:
    """Seeded per (instance, level): the table order is shuffled so codes carry
    no positional hint, but each rendered prompt is reproducible."""
    seed = zlib.crc32(f'{instance.instance_id}-{level}'.encode())
    shown = instance.slice_for(level)
    order = np.random.default_rng(seed).permutation(len(shown))
    return tuple(shown[i] for i in order)
