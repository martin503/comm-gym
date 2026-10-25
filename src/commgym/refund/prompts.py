from commgym.refund.config import PolicyParams
from commgym.refund.instance import RefundInstance


def system_prompt() -> str:
    return """You are a customer-support agent for a grocery chain. A customer writes in about \
a recent purchase. For each claim in their message, decide whether a refund is owed under the \
store's refund policy, and how much.

Each case carries its own policy parameters (claim window, price tolerance, price-match scope, \
refund cap), shown in the "Refund policy for this case" block of the message. Read that block \
and apply it exactly: the parameters differ from case to case.

Rules that hold for every case:
- Check the policy rules strictly in the order the block lists them; the first rule that \
decides determines the reason code.
- A claim phrased as a price complaint is judged under the price-match rule only, a claim \
phrased as a coupon complaint under the missed-coupon rule only, and a claim about a missing \
item under the item-on-receipt rule only. The item-on-receipt check runs before both: a claim \
that matches no line is NOT_ON_RECEIPT, and one that fits several lines without singling one \
out is NEEDS_CLARIFICATION, whatever rule the claim is phrased under.
- Amounts on the receipt always override amounts stated in the message.
- A live coupon covers a receipt line when the line matches the coupon's "covers" description \
(brand tier, category, size, and any exceptions).
- Approved refunds are paid in the order the claims appear. Once the case's refund cap is \
reached, later approved claims are refunded $0.00. If two approved claims are about the same \
receipt line, only the first is refunded.
- A price-match refund never exceeds what was paid for the item.

Output your reasoning, then exactly one answer block:

<answer>{"claims": [{"line": "L07" | null, "decision": "approve" | "reject", "reason": \
"<CODE>", "refund": 0.42}, ...]}</answer>

The claims array lists one entry per claim in the message, in the order they appear. "line" is \
the receipt line the claim refers to, or null when the item is not on the receipt. "refund" is \
0 for every rejection. Reason codes: OUTSIDE_WINDOW, NOT_ON_RECEIPT, \
NEEDS_CLARIFICATION, PRICE_MATCH, WITHIN_TOLERANCE, MISSED_COUPON, NOT_ELIGIBLE, \
ALREADY_APPLIED."""


def policy_block(policy: PolicyParams) -> str:
    """The per-case policy, rendered so every parameter is readable back from the text."""
    tolerance = policy.price_tolerance_cents / 100
    national_only = ''
    if policy.price_match_national_only:
        national_only = (
            ' Price matches apply to national-brand items only; price claims about other '
            'items are rejected (NOT_ELIGIBLE).'
        )
    if policy.refund_cap_cents is None:
        cap_rule = 'There is no cap on total refunds for this receipt.'
    else:
        cap_rule = (
            f'Total refunds for this receipt are capped at ${policy.refund_cap_cents / 100:.2f}.'
        )
    header = (
        'Refund policy for this case (the first rule that decides determines the reason code):'
    )
    return f"""{header}
1. Window: a claim filed more than {policy.claim_window_days} days after the purchase day is \
rejected (OUTSIDE_WINDOW).
2. Item on receipt: resolve the claim's wording against the receipt. Customers use words \
loosely: a word covers a receipt line when the line's category is one the word refers to \
("cereal" covers hot cereal). When the wording names a specific kind ("ricotta", "greek \
yogurt"), it covers only lines of that kind (matching the sub-category), not every line of \
the broader category. If the claimed item matches no receipt line, reject with \
NOT_ON_RECEIPT. If the wording fits two or more receipt lines without singling one out, \
reject with NEEDS_CLARIFICATION (line null).
3. Price match: if the paid loyalty unit price (regular unit price minus loyalty discount) \
exceeds the reference price by more than ${tolerance:.2f} per unit, approve (PRICE_MATCH) and \
refund the difference times the quantity, never more than what was paid for the item. \
Otherwise reject (WITHIN_TOLERANCE).{national_only}
4. Missed coupon: if no live coupon covers that receipt line, reject with NOT_ELIGIBLE. If a \
coupon discount was already applied on that line, reject with ALREADY_APPLIED. Otherwise \
approve with MISSED_COUPON and refund the coupon's typical value.
5. Refunds: {cap_rule} Approved refunds are paid in the order the claims appear; if two \
approved claims are about the same receipt line, only the first is refunded."""


def user_prompt(instance: RefundInstance) -> str:
    lines = [
        f'Purchase day: {instance.purchase_day}',
        f'Claim filed: day {instance.claim_day}',
        '',
        policy_block(instance.policy),
        '',
        'Receipt:',
        '| line | category | sub-category | brand tier | size | qty | regular unit |'
        ' loyalty disc | coupon disc | paid | reference |',
    ]
    for line in instance.lines:
        lines.append(
            f'| {line.code} | {line.commodity} | {line.sub_commodity} |'
            f' {line.brand_tier.value} | {line.size} | {line.quantity} |'
            f' {_cents(line.regular_unit_cents)} | {_cents(line.loyalty_disc_unit_cents)} |'
            f' {_cents(line.coupon_disc_unit_cents)} | {_cents(line.paid_unit_cents)} |'
            f' {_cents(line.reference_cents)} |'
        )
    lines += ['', "Live coupons on the customer's account:", '']
    if instance.coupons:
        lines.append('| coupon | typical value | covers |')
        for coupon in instance.coupons:
            lines.append(
                f'| {coupon.coupon_id} | {_cents(coupon.typical_value_cents)} |'
                f' {coupon.coverage} |'
            )
    else:
        lines.append('(none)')
    lines += ['', 'Customer message:', '', instance.message, '']
    return '\n'.join(lines)


def messages(instance: RefundInstance) -> list[dict[str, str]]:
    return [
        {'role': 'system', 'content': system_prompt()},
        {'role': 'user', 'content': user_prompt(instance)},
    ]


def _cents(value: int) -> str:
    return f'${value / 100:.2f}'
