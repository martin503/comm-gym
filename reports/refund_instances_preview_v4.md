# Refund instance preview

## eval_unseen-L1-0000 (anchor eval_unseen-0000, out-of-window: False)

Policy: window 21d, tolerance 25c, cap 150c, national-only True

### System

You are a customer-support agent for a grocery chain. A customer writes in about a recent purchase. For each claim in their message, decide whether a refund is owed under the store's refund policy, and how much.

Each case carries its own policy parameters (claim window, price tolerance, price-match scope, refund cap), shown in the "Refund policy for this case" block of the message. Read that block and apply it exactly: the parameters differ from case to case.

Rules that hold for every case:
- Check the policy rules strictly in the order the block lists them; the first rule that decides determines the reason code.
- A claim phrased as a price complaint is judged under the price-match rule only, a claim phrased as a coupon complaint under the missed-coupon rule only, and a claim about a missing item under the item-on-receipt rule only. The item-on-receipt check runs before both: a claim that matches no line is NOT_ON_RECEIPT, and one that fits several lines without singling one out is NEEDS_CLARIFICATION, whatever rule the claim is phrased under.
- Amounts on the receipt always override amounts stated in the message.
- A live coupon covers a receipt line when the line matches the coupon's "covers" description (brand tier, category, size, and any exceptions).
- Approved refunds are paid in the order the claims appear. Once the case's refund cap is reached, later approved claims are refunded $0.00. If two approved claims are about the same receipt line, only the first is refunded.
- A price-match refund never exceeds what was paid for the item.

Output your reasoning, then exactly one answer block:

<answer>{"claims": [{"line": "L07" | null, "decision": "approve" | "reject", "reason": "<CODE>", "refund": 0.42}, ...]}</answer>

The claims array lists one entry per claim in the message, in the order they appear. "line" is the receipt line the claim refers to, or null when the item is not on the receipt. "refund" is 0 for every rejection. Reason codes: OUTSIDE_WINDOW, NOT_ON_RECEIPT, NEEDS_CLARIFICATION, PRICE_MATCH, WITHIN_TOLERANCE, MISSED_COUPON, NOT_ELIGIBLE, ALREADY_APPLIED.

### User

Purchase day: 677
Claim filed: day 691

Refund policy for this case (the first rule that decides determines the reason code):
1. Window: a claim filed more than 21 days after the purchase day is rejected (OUTSIDE_WINDOW).
2. Item on receipt: resolve the claim's wording against the receipt. Customers use words loosely: a word covers a receipt line when the line's category is one the word refers to ("cereal" covers hot cereal). When the wording names a specific kind ("ricotta", "greek yogurt"), it covers only lines of that kind (matching the sub-category), not every line of the broader category. If the claimed item matches no receipt line, reject with NOT_ON_RECEIPT. If the wording fits two or more receipt lines without singling one out, reject with NEEDS_CLARIFICATION (line null).
3. Price match: if the paid loyalty unit price (regular unit price minus loyalty discount) exceeds the reference price by more than $0.25 per unit, approve (PRICE_MATCH) and refund the difference times the quantity, never more than what was paid for the item. Otherwise reject (WITHIN_TOLERANCE). Price matches apply to national-brand items only; price claims about other items are rejected (NOT_ELIGIBLE).
4. Missed coupon: if no live coupon covers that receipt line, reject with NOT_ELIGIBLE. If a coupon discount was already applied on that line, reject with ALREADY_APPLIED. Otherwise approve with MISSED_COUPON and refund the coupon's typical value.
5. Refunds: Total refunds for this receipt are capped at $1.50. Approved refunds are paid in the order the claims appear; if two approved claims are about the same receipt line, only the first is refunded.

Receipt:
| line | category | sub-category | brand tier | size | qty | regular unit | loyalty disc | coupon disc | paid | reference |
| L01 | EGGS | EGGS - LARGE | Private | 1 DZ | 1 | $1.09 | $0.00 | $0.00 | $1.09 | $1.09 |
| L02 | CANDY - PACKAGED | CANDY BAGS-NON CHOCOLATE | National | 10.125 OZ | 1 | $2.19 | $0.00 | $0.00 | $2.19 | $2.19 |
| L03 | CANDY - PACKAGED | CANDY BAGS-NON CHOCOLATE | National | 11 OZ | 1 | $2.60 | $0.00 | $0.00 | $2.60 | $2.60 |
| L04 | FRZN MEAT/MEAT DINNERS | SS ECONOMY ENTREES/DINNERS ALL | National | 6.75 OZ | 1 | $1.00 | $0.00 | $0.00 | $1.00 | $1.00 |
| L05 | PET CARE SUPPLIES | DOG & CAT ACCESSORIES | National | 14 PK | 4 | $4.99 | $0.00 | $0.00 | $4.99 | $4.99 |
| L06 | BAKED BREAD/BUNS/ROLLS | MAINSTREAM WHITE BREAD | National | 22 OZ | 1 | $2.69 | $0.69 | $0.00 | $2.00 | $2.00 |
| L07 | FRZN MEAT/MEAT DINNERS | SS ECONOMY ENTREES/DINNERS ALL | National | 9.25 OZ | 4 | $1.00 | $0.00 | $0.00 | $1.00 | $1.00 |
| L08 | DRY MIX DESSERTS | PUDDINGS DRY | National | 5 OZ | 2 | $1.29 | $0.00 | $0.00 | $1.29 | $1.29 |
| L09 | FLUID MILK PRODUCTS | FLUID MILK WHITE ONLY | Private |   | 2 | $1.89 | $0.69 | $0.00 | $1.20 | $1.20 |
| L10 | CIGARETTES | CIGARETTES | National | 522797 CTN | 1 | $38.34 | $0.00 | $0.00 | $38.34 | $32.76 |
| L11 | PET CARE SUPPLIES | PET TREATS | National | 10 OZ | 1 | $4.99 | $0.00 | $0.00 | $4.99 | $4.99 |
| L12 | ORAL HYGIENE PRODUCTS | TOOTHPASTE | National | 4 OZ | 1 | $5.29 | $1.30 | $0.00 | $3.99 | $3.99 |
| L13 | COUPON/MISC ITEMS | PRODUCE DEPT KEY RING | Private |   | 1 | $3.29 | $0.00 | $0.00 | $3.29 | $1.99 |
| L14 | AIR CARE | AIR CARE - AEROSOLS | National | 9 OZ | 4 | $1.49 | $0.49 | $0.00 | $1.00 | $1.00 |
| L15 | ANTACIDS | ANTI-ACIDS | Private |   | 2 | $5.59 | $2.80 | $0.00 | $2.79 | $2.79 |
| L16 | TROPICAL FRUIT | BANANAS | National | 40 LB | 1 | $1.20 | $0.00 | $0.00 | $1.20 | $1.02 |
| L17 | DOG FOODS | DRY DOG FOOD SUPER PREM (ONE/N | National | 40 LB | 1 | $31.99 | $0.00 | $2.00 | $29.99 | $31.29 |
| L18 | FRZN MEAT/MEAT DINNERS | SS ECONOMY ENTREES/DINNERS ALL | National | L     9 OZ | 4 | $1.00 | $0.00 | $0.00 | $1.00 | $1.00 |
| L19 | DRY MIX DESSERTS | PUDDINGS DRY | National | 4.6 OZ | 2 | $1.29 | $0.00 | $0.00 | $1.29 | $1.29 |
| L20 | AIR CARE | AIR CARE - AEROSOLS | National | 9 OZ | 2 | $1.49 | $0.49 | $0.00 | $1.00 | $1.00 |
| L21 | SOAP - LIQUID & BAR | BAR SOAP | National | 4 OZ | 1 | $3.79 | $0.00 | $0.00 | $3.79 | $3.79 |
| L22 | FROZEN PIZZA | PIZZA/PREMIUM | National | 12.5 OZ | 1 | $3.29 | $0.29 | $0.00 | $3.00 | $3.00 |
| L23 | COLD CEREAL | ALL FAMILY CEREAL | Private | 6 OZ | 1 | $0.88 | $0.00 | $0.00 | $0.88 | $0.88 |
| L24 | DRY BN/VEG/POTATO/RICE | POTATOES: DRY | National | 26.7 OZ | 1 | $4.44 | $0.00 | $1.00 | $3.44 | $3.89 |
| L25 | LAUNDRY ADDITIVES | FABRIC SOFTENER SHEETS | National | 105 CT | 1 | $6.24 | $1.00 | $0.50 | $4.74 | $5.24 |
| L26 | BAKING MIXES | BROWNIE MIX | National | 19.5 OZ | 1 | $2.09 | $0.00 | $0.00 | $2.09 | $2.09 |
| L27 | CANDY - PACKAGED | CANDY BARS (MULTI PACK) | National | 8.4 OZ | 2 | $2.89 | $1.44 | $0.00 | $1.45 | $1.45 |
| L28 | DOMESTIC GOODS | PROMO | National |   | 1 | $3.50 | $0.00 | $0.00 | $3.50 | $3.50 |
| L29 | COLD CEREAL | ALL FAMILY CEREAL | National | 23 OZ | 1 | $3.99 | $0.80 | $0.00 | $3.19 | $3.19 |

Live coupons on the customer's account:

(none)

Customer message:

Somehow the paper towels never made it into my bag even though I paid for them.


### Truth

| message | stated | line | decision | reason | refund |
|---|---|---|---|---|---|
| Somehow the paper towels never made it into my bag even though I paid for them. | missing_item | None | reject | NOT_ON_RECEIPT | 0c |

---

## eval_unseen-L1-0001 (anchor eval_unseen-0001, out-of-window: False)

Policy: window 30d, tolerance 10c, cap 75c, national-only False

### System

You are a customer-support agent for a grocery chain. A customer writes in about a recent purchase. For each claim in their message, decide whether a refund is owed under the store's refund policy, and how much.

Each case carries its own policy parameters (claim window, price tolerance, price-match scope, refund cap), shown in the "Refund policy for this case" block of the message. Read that block and apply it exactly: the parameters differ from case to case.

Rules that hold for every case:
- Check the policy rules strictly in the order the block lists them; the first rule that decides determines the reason code.
- A claim phrased as a price complaint is judged under the price-match rule only, a claim phrased as a coupon complaint under the missed-coupon rule only, and a claim about a missing item under the item-on-receipt rule only. The item-on-receipt check runs before both: a claim that matches no line is NOT_ON_RECEIPT, and one that fits several lines without singling one out is NEEDS_CLARIFICATION, whatever rule the claim is phrased under.
- Amounts on the receipt always override amounts stated in the message.
- A live coupon covers a receipt line when the line matches the coupon's "covers" description (brand tier, category, size, and any exceptions).
- Approved refunds are paid in the order the claims appear. Once the case's refund cap is reached, later approved claims are refunded $0.00. If two approved claims are about the same receipt line, only the first is refunded.
- A price-match refund never exceeds what was paid for the item.

Output your reasoning, then exactly one answer block:

<answer>{"claims": [{"line": "L07" | null, "decision": "approve" | "reject", "reason": "<CODE>", "refund": 0.42}, ...]}</answer>

The claims array lists one entry per claim in the message, in the order they appear. "line" is the receipt line the claim refers to, or null when the item is not on the receipt. "refund" is 0 for every rejection. Reason codes: OUTSIDE_WINDOW, NOT_ON_RECEIPT, NEEDS_CLARIFICATION, PRICE_MATCH, WITHIN_TOLERANCE, MISSED_COUPON, NOT_ELIGIBLE, ALREADY_APPLIED.

### User

Purchase day: 609
Claim filed: day 630

Refund policy for this case (the first rule that decides determines the reason code):
1. Window: a claim filed more than 30 days after the purchase day is rejected (OUTSIDE_WINDOW).
2. Item on receipt: resolve the claim's wording against the receipt. Customers use words loosely: a word covers a receipt line when the line's category is one the word refers to ("cereal" covers hot cereal). When the wording names a specific kind ("ricotta", "greek yogurt"), it covers only lines of that kind (matching the sub-category), not every line of the broader category. If the claimed item matches no receipt line, reject with NOT_ON_RECEIPT. If the wording fits two or more receipt lines without singling one out, reject with NEEDS_CLARIFICATION (line null).
3. Price match: if the paid loyalty unit price (regular unit price minus loyalty discount) exceeds the reference price by more than $0.10 per unit, approve (PRICE_MATCH) and refund the difference times the quantity, never more than what was paid for the item. Otherwise reject (WITHIN_TOLERANCE).
4. Missed coupon: if no live coupon covers that receipt line, reject with NOT_ELIGIBLE. If a coupon discount was already applied on that line, reject with ALREADY_APPLIED. Otherwise approve with MISSED_COUPON and refund the coupon's typical value.
5. Refunds: Total refunds for this receipt are capped at $0.75. Approved refunds are paid in the order the claims appear; if two approved claims are about the same receipt line, only the first is refunded.

Receipt:
| line | category | sub-category | brand tier | size | qty | regular unit | loyalty disc | coupon disc | paid | reference |
| L01 | SALD DRSNG/SNDWCH SPRD | POURABLE SALAD DRESSINGS | Private |   | 1 | $1.22 | $0.22 | $0.00 | $1.00 | $1.00 |
| L02 | MILK BY-PRODUCTS | SOUR CREAMS | Private | 16 OZ | 1 | $1.05 | $0.05 | $0.00 | $1.00 | $1.00 |
| L03 | VEGETABLES - ALL OTHERS | CUCUMBERS | National | 36 CT | 1 | $0.79 | $0.00 | $0.00 | $0.79 | $0.79 |
| L04 | BROCCOLI/CAULIFLOWER | BROCCOLI WHOLE&CROWNS | National |   | 1 | $1.99 | $0.32 | $0.00 | $1.67 | $1.67 |
| L05 | CHEESE | CREAM CHEESE | National | L      8OZ | 2 | $2.09 | $0.99 | $0.20 | $0.90 | $1.00 |
| L06 | PICKLE/RELISH/PKLD VEG | PICKLES | National | 24 OZ | 1 | $3.49 | $0.99 | $1.00 | $1.50 | $2.25 |
| L07 | VEGETABLES - ALL OTHERS | CELERY | National |   | 1 | $1.89 | $0.90 | $0.00 | $0.99 | $0.99 |
| L08 | SPICES & EXTRACTS | SPICES & SEASONINGS | Private | 1.75 OZ | 1 | $1.99 | $0.66 | $0.00 | $1.33 | $1.33 |
| L09 | EGGS | EGGS - MEDIUM | Private | 1 DZ | 2 | $0.64 | $0.00 | $0.00 | $0.64 | $0.69 |
| L10 | BAG SNACKS | SALAD DRESSING MIXES | National | 1 OZ | 1 | $1.49 | $0.00 | $0.00 | $1.49 | $1.49 |
| L11 | SOFT DRINKS | SFT DRNK 2 LITER BTL CARB INCL | National | 2LTR | 2 | $1.59 | $0.71 | $0.00 | $0.88 | $0.88 |
| L12 | SPICES & EXTRACTS | SPICES & SEASONINGS | Private | 3.75 OZ | 1 | $2.79 | $0.92 | $0.00 | $1.87 | $1.87 |
| L13 | PAPER TOWELS | PAPER TOWELS & HOLDERS | National | 376.4 SQFT | 1 | $9.99 | $1.00 | $0.00 | $8.99 | $8.99 |
| L14 | CHEESE | IWS SINGLE CHEESE | Private | 12 OZ | 1 | $1.74 | $0.24 | $0.00 | $1.50 | $1.50 |
| L15 | CONDIMENTS/SAUCES | STEAK & WORCHESTER SAUCE | Private | 10 OZ | 1 | $1.19 | $0.19 | $0.00 | $1.00 | $1.00 |
| L16 | BROCCOLI/CAULIFLOWER | CAULIFLOWER WHOLE | National |   | 1 | $2.50 | $0.00 | $0.00 | $2.50 | $2.50 |
| L17 | CRACKERS/MISC BKD FD | BUTTER SPRAY CRACKER (RITZ/CLU | National | 16 OZ | 1 | $3.94 | $1.51 | $1.00 | $1.43 | $1.88 |
| L18 | LUNCHMEAT | MISCELLANEOUS | Private | 2.0 OZ | 2 | $0.69 | $0.19 | $0.00 | $0.50 | $0.50 |

Live coupons on the customer's account:

(none)

Customer message:

I paid for the oatmeal and it never made it home with me.


### Truth

| message | stated | line | decision | reason | refund |
|---|---|---|---|---|---|
| I paid for the oatmeal and it never made it home with me. | missing_item | None | reject | NOT_ON_RECEIPT | 0c |

---

## eval_unseen-L1-0002 (anchor eval_unseen-0002, out-of-window: False)

Policy: window 14d, tolerance 50c, cap 150c, national-only True

### System

You are a customer-support agent for a grocery chain. A customer writes in about a recent purchase. For each claim in their message, decide whether a refund is owed under the store's refund policy, and how much.

Each case carries its own policy parameters (claim window, price tolerance, price-match scope, refund cap), shown in the "Refund policy for this case" block of the message. Read that block and apply it exactly: the parameters differ from case to case.

Rules that hold for every case:
- Check the policy rules strictly in the order the block lists them; the first rule that decides determines the reason code.
- A claim phrased as a price complaint is judged under the price-match rule only, a claim phrased as a coupon complaint under the missed-coupon rule only, and a claim about a missing item under the item-on-receipt rule only. The item-on-receipt check runs before both: a claim that matches no line is NOT_ON_RECEIPT, and one that fits several lines without singling one out is NEEDS_CLARIFICATION, whatever rule the claim is phrased under.
- Amounts on the receipt always override amounts stated in the message.
- A live coupon covers a receipt line when the line matches the coupon's "covers" description (brand tier, category, size, and any exceptions).
- Approved refunds are paid in the order the claims appear. Once the case's refund cap is reached, later approved claims are refunded $0.00. If two approved claims are about the same receipt line, only the first is refunded.
- A price-match refund never exceeds what was paid for the item.

Output your reasoning, then exactly one answer block:

<answer>{"claims": [{"line": "L07" | null, "decision": "approve" | "reject", "reason": "<CODE>", "refund": 0.42}, ...]}</answer>

The claims array lists one entry per claim in the message, in the order they appear. "line" is the receipt line the claim refers to, or null when the item is not on the receipt. "refund" is 0 for every rejection. Reason codes: OUTSIDE_WINDOW, NOT_ON_RECEIPT, NEEDS_CLARIFICATION, PRICE_MATCH, WITHIN_TOLERANCE, MISSED_COUPON, NOT_ELIGIBLE, ALREADY_APPLIED.

### User

Purchase day: 623
Claim filed: day 629

Refund policy for this case (the first rule that decides determines the reason code):
1. Window: a claim filed more than 14 days after the purchase day is rejected (OUTSIDE_WINDOW).
2. Item on receipt: resolve the claim's wording against the receipt. Customers use words loosely: a word covers a receipt line when the line's category is one the word refers to ("cereal" covers hot cereal). When the wording names a specific kind ("ricotta", "greek yogurt"), it covers only lines of that kind (matching the sub-category), not every line of the broader category. If the claimed item matches no receipt line, reject with NOT_ON_RECEIPT. If the wording fits two or more receipt lines without singling one out, reject with NEEDS_CLARIFICATION (line null).
3. Price match: if the paid loyalty unit price (regular unit price minus loyalty discount) exceeds the reference price by more than $0.50 per unit, approve (PRICE_MATCH) and refund the difference times the quantity, never more than what was paid for the item. Otherwise reject (WITHIN_TOLERANCE). Price matches apply to national-brand items only; price claims about other items are rejected (NOT_ELIGIBLE).
4. Missed coupon: if no live coupon covers that receipt line, reject with NOT_ELIGIBLE. If a coupon discount was already applied on that line, reject with ALREADY_APPLIED. Otherwise approve with MISSED_COUPON and refund the coupon's typical value.
5. Refunds: Total refunds for this receipt are capped at $1.50. Approved refunds are paid in the order the claims appear; if two approved claims are about the same receipt line, only the first is refunded.

Receipt:
| line | category | sub-category | brand tier | size | qty | regular unit | loyalty disc | coupon disc | paid | reference |
| L01 | ONIONS | ONIONS YELLOW (BULK&BAG) | Private | 3 LB | 1 | $2.49 | $1.00 | $0.00 | $1.49 | $1.49 |
| L02 | SOUP | CONDENSED SOUP | Private | 10.5OZ | 1 | $0.69 | $0.10 | $0.00 | $0.59 | $0.59 |
| L03 | HISPANIC | MEXICAN SAUCESSALSAPICANTEE | Private | 10 OZ | 1 | $0.99 | $0.00 | $0.00 | $0.99 | $0.99 |
| L04 | SHORTENING/OIL | COOKING SPRAYS | Private | 8.0 OZ | 1 | $1.62 | $0.12 | $0.00 | $1.50 | $1.50 |
| L05 | BEANS - CANNED GLASS & MW | VARIETY BEANS - KIDNEY PINTO | Private | 15 OZ | 1 | $0.48 | $0.08 | $0.00 | $0.40 | $0.40 |
| L06 | BEEF | LEAN | National |   | 1 | $3.20 | $1.02 | $0.00 | $2.18 | $2.74 |
| L07 | HISPANIC | MEXICAN SEASONING MIXES | National | 1 OZ | 2 | $1.27 | $0.00 | $0.50 | $0.77 | $1.13 |
| L08 | HISPANIC | MEXICAN SAUCESSALSAPICANTEE | National | 8 OZ | 1 | $1.49 | $0.30 | $0.00 | $1.19 | $1.19 |
| L09 | MISC. DAIRY | REFRIGERATED MEXICAN PRODUCTS | Private | 11.5 OZ | 2 | $1.19 | $0.00 | $0.00 | $1.19 | $1.19 |
| L10 | BEEF | LEAN | Private | 1 LB | 1 | $1.99 | $0.50 | $0.00 | $1.49 | $1.49 |
| L11 | HISPANIC | MEXICAN PEPPERS CHILIES | National | 4 OZ | 1 | $1.19 | $0.00 | $0.00 | $1.19 | $1.19 |
| L12 | MILK BY-PRODUCTS | SOUR CREAMS | Private | 12 OZ | 1 | $1.16 | $0.00 | $0.00 | $1.16 | $1.16 |
| L13 | CHEESE | SHREDDED CHEESE | Private | 16 OZ | 1 | $3.99 | $1.00 | $0.00 | $2.99 | $2.99 |
| L14 | BREAKFAST SWEETS | SW GDS:DONUTS | National | 30 OZ | 1 | $1.85 | $0.00 | $0.00 | $1.85 | $1.85 |

Live coupons on the customer's account:

| coupon | typical value | covers |
| C01 | $1.00 | store-brand onions |
| C02 | $0.35 | store-brand cheese, store-brand milk by-products, store-brand misc. dairy |
| C03 | $1.00 | national-brand beef, store-brand beef |

Customer message:

My digital coupon never came off the sour cream when I checked out.


### Truth

| message | stated | line | decision | reason | refund |
|---|---|---|---|---|---|
| My digital coupon never came off the sour cream when I checked out. | coupon | L12 | approve | MISSED_COUPON | 35c |

---

## eval_unseen-L1-0003 (anchor eval_unseen-0003, out-of-window: False)

Policy: window 21d, tolerance 5c, cap 150c, national-only False

### System

You are a customer-support agent for a grocery chain. A customer writes in about a recent purchase. For each claim in their message, decide whether a refund is owed under the store's refund policy, and how much.

Each case carries its own policy parameters (claim window, price tolerance, price-match scope, refund cap), shown in the "Refund policy for this case" block of the message. Read that block and apply it exactly: the parameters differ from case to case.

Rules that hold for every case:
- Check the policy rules strictly in the order the block lists them; the first rule that decides determines the reason code.
- A claim phrased as a price complaint is judged under the price-match rule only, a claim phrased as a coupon complaint under the missed-coupon rule only, and a claim about a missing item under the item-on-receipt rule only. The item-on-receipt check runs before both: a claim that matches no line is NOT_ON_RECEIPT, and one that fits several lines without singling one out is NEEDS_CLARIFICATION, whatever rule the claim is phrased under.
- Amounts on the receipt always override amounts stated in the message.
- A live coupon covers a receipt line when the line matches the coupon's "covers" description (brand tier, category, size, and any exceptions).
- Approved refunds are paid in the order the claims appear. Once the case's refund cap is reached, later approved claims are refunded $0.00. If two approved claims are about the same receipt line, only the first is refunded.
- A price-match refund never exceeds what was paid for the item.

Output your reasoning, then exactly one answer block:

<answer>{"claims": [{"line": "L07" | null, "decision": "approve" | "reject", "reason": "<CODE>", "refund": 0.42}, ...]}</answer>

The claims array lists one entry per claim in the message, in the order they appear. "line" is the receipt line the claim refers to, or null when the item is not on the receipt. "refund" is 0 for every rejection. Reason codes: OUTSIDE_WINDOW, NOT_ON_RECEIPT, NEEDS_CLARIFICATION, PRICE_MATCH, WITHIN_TOLERANCE, MISSED_COUPON, NOT_ELIGIBLE, ALREADY_APPLIED.

### User

Purchase day: 494
Claim filed: day 503

Refund policy for this case (the first rule that decides determines the reason code):
1. Window: a claim filed more than 21 days after the purchase day is rejected (OUTSIDE_WINDOW).
2. Item on receipt: resolve the claim's wording against the receipt. Customers use words loosely: a word covers a receipt line when the line's category is one the word refers to ("cereal" covers hot cereal). When the wording names a specific kind ("ricotta", "greek yogurt"), it covers only lines of that kind (matching the sub-category), not every line of the broader category. If the claimed item matches no receipt line, reject with NOT_ON_RECEIPT. If the wording fits two or more receipt lines without singling one out, reject with NEEDS_CLARIFICATION (line null).
3. Price match: if the paid loyalty unit price (regular unit price minus loyalty discount) exceeds the reference price by more than $0.05 per unit, approve (PRICE_MATCH) and refund the difference times the quantity, never more than what was paid for the item. Otherwise reject (WITHIN_TOLERANCE).
4. Missed coupon: if no live coupon covers that receipt line, reject with NOT_ELIGIBLE. If a coupon discount was already applied on that line, reject with ALREADY_APPLIED. Otherwise approve with MISSED_COUPON and refund the coupon's typical value.
5. Refunds: Total refunds for this receipt are capped at $1.50. Approved refunds are paid in the order the claims appear; if two approved claims are about the same receipt line, only the first is refunded.

Receipt:
| line | category | sub-category | brand tier | size | qty | regular unit | loyalty disc | coupon disc | paid | reference |
| L01 | BERRIES | BLUEBERRIES | National | PT | 2 | $2.99 | $1.32 | $0.00 | $1.67 | $1.67 |
| L02 | PNT BTR/JELLY/JAMS | JELLY | Private | 18 OZ | 1 | $1.49 | $0.10 | $0.00 | $1.39 | $1.39 |
| L03 | DIAPERS & DISPOSABLES | BABY DIAPERS | National | 40 CT | 1 | $9.99 | $0.00 | $0.00 | $9.99 | $9.99 |
| L04 | GRAPES | GRAPES RED | National | 18 LB | 1 | $5.98 | $0.00 | $0.00 | $5.98 | $5.03 |
| L05 | BAKED BREAD/BUNS/ROLLS | PREMIUM BREAD | National | 24 OZ | 2 | $3.19 | $0.69 | $0.00 | $2.50 | $2.50 |
| L06 | DELI MEATS | MEAT: BEEF BULK | National |   | 1 | $3.50 | $0.00 | $0.00 | $3.50 | $3.50 |
| L07 | FRUIT - SHELF STABLE | FRUIT BOWL AND CUPS | National | 6 PK/4 OZ | 1 | $2.49 | $0.49 | $0.00 | $2.00 | $2.00 |
| L08 | STONE FRUIT | PEACHES YELLOW FLESH | National |   | 1 | $2.83 | $0.00 | $0.00 | $2.83 | $2.28 |
| L09 | FITNESS&DIET | FITNESS&DIET - BARS | National | 2.4 OZ | 1 | $1.49 | $0.49 | $0.00 | $1.00 | $1.00 |
| L10 | CRACKERS/MISC BKD FD | SOUP CRACKERS (SALTINE/OYSTER) | Private | 12 OZ | 1 | $1.15 | $0.00 | $0.00 | $1.15 | $1.09 |
| L11 | FEMININE HYGIENE | FEM. HYGN.NAPKINS | National |   | 2 | $3.39 | $0.60 | $0.00 | $2.79 | $2.79 |
| L12 | FLUID MILK PRODUCTS | REFRIGERATED COFFEE CREAMERS | National | 32 OZ | 1 | $3.49 | $0.00 | $0.00 | $3.49 | $3.49 |
| L13 | WATER - CARBONATED/FLVRD DRINK | SPRING WATER | National | .5 LTR | 1 | $7.99 | $1.00 | $0.00 | $6.99 | $6.99 |
| L14 | COOKIES/CONES | GRAHAM CRACKERS | National | 13 OZ | 1 | $3.59 | $0.60 | $0.00 | $2.99 | $2.99 |
| L15 | CHEESES | CHEESE: NATURAL BULK | National |   | 1 | $4.05 | $1.02 | $1.00 | $2.03 | $2.57 |
| L16 | SOAP - LIQUID & BAR | LIQUID SOAP | National |   | 2 | $1.99 | $1.00 | $0.00 | $0.99 | $0.99 |
| L17 | FRUIT - SHELF STABLE | FRUIT BOWL AND CUPS | National | 6 PK/4 OZ | 1 | $3.04 | $0.49 | $1.00 | $1.55 | $2.00 |
| L18 | FLUID MILK PRODUCTS | FLUID MILK WHITE ONLY | Private | 1 GA | 1 | $2.69 | $0.00 | $0.00 | $2.69 | $2.69 |
| L19 | YOGURT | YOGURT NOT MULTI-PACKS | National | 32 OZ | 1 | $2.99 | $0.30 | $0.00 | $2.69 | $2.69 |
| L20 | WATER - CARBONATED/FLVRD DRINK | SPRING WATER | Private | GAL | 2 | $0.89 | $0.00 | $0.00 | $0.89 | $0.89 |
| L21 | FLUID MILK PRODUCTS | FLUID MILK WHITE ONLY | Private | 1 GA | 1 | $2.69 | $0.00 | $0.00 | $2.69 | $2.69 |
| L22 | DELI MEATS | MEAT: TURKEY BULK | National |   | 1 | $3.36 | $0.48 | $0.00 | $2.88 | $5.90 |
| L23 | COLD CEREAL | ADULT CEREAL | National | 20 OZ | 1 | $3.29 | $0.00 | $0.00 | $3.29 | $3.29 |
| L24 | TROPICAL FRUIT | BANANAS | National | 40 LB | 1 | $1.21 | $0.00 | $0.00 | $1.21 | $1.02 |
| L25 | BEERS/ALES | BEERALEMALT LIQUORS | National | 12 OZ | 1 | $6.99 | $0.00 | $0.00 | $6.99 | $6.99 |
| L26 | BERRIES | STRAWBERRIES | National | 16 OZ | 1 | $2.99 | $0.00 | $0.00 | $2.99 | $2.99 |
| L27 | CHEESES | CHEESE: NATURAL BULK | National |   | 1 | $3.05 | $1.02 | $0.00 | $2.03 | $2.19 |
| L28 | BROOMS AND MOPS | SPONGES: BATH HOUSEHOLD | National |   | 1 | $2.49 | $0.00 | $0.00 | $2.49 | $2.49 |
| L29 | BROOMS AND MOPS | BRUSHES | National |   | 1 | $2.49 | $0.00 | $0.00 | $2.49 | $2.49 |
| L30 | BABY HBC | BABY WIPES | Private |   | 2 | $2.19 | $0.19 | $0.00 | $2.00 | $2.00 |
| L31 | CHEESE | STRING CHEESE | National | 8 OZ | 1 | $3.09 | $0.00 | $0.00 | $3.09 | $3.09 |
| L32 | BEERS/ALES | BEERALEMALT LIQUORS | National | 12PK/12OZ | 1 | $8.49 | $0.00 | $0.00 | $8.49 | $8.49 |
| L33 | CRACKERS/MISC BKD FD | CHEESE CRACKERS (CHEEZ-ITS/GOL | National | 6.6 OZ | 1 | $1.99 | $0.20 | $0.00 | $1.79 | $1.64 |
| L34 | BAG SNACKS | MISC BAG SNACKS | National | 10.5 OZ | 1 | $3.49 | $0.00 | $0.00 | $3.49 | $3.49 |
| L35 | HOUSEHOLD CLEANG NEEDS | TOOLS - FLOOR & FURNITURE | Private | 1 CT | 1 | $2.99 | $0.49 | $0.00 | $2.50 | $2.50 |
| L36 | DIAPERS & DISPOSABLES | BABY DIAPERS | National | 112 CT | 1 | $30.49 | $0.00 | $1.50 | $28.99 | $30.49 |
| L37 | PNT BTR/JELLY/JAMS | PEANUT BUTTER | National | 16 OZ | 1 | $3.99 | $0.30 | $1.00 | $2.69 | $3.19 |

Live coupons on the customer's account:

| coupon | typical value | covers |
| C01 | $2.00 | national-brand diapers & disposables 112 ct and larger |
| C02 | $2.00 | national-brand diapers & disposables 40 ct and smaller |

Customer message:

My coupon never applied to the brush at checkout, so I paid full price for it.


### Truth

| message | stated | line | decision | reason | refund |
|---|---|---|---|---|---|
| My coupon never applied to the brush at checkout, so I paid full price for it. | coupon | L29 | reject | NOT_ELIGIBLE | 0c |

---

## eval_unseen-L1-0004 (anchor eval_unseen-0004, out-of-window: False)

Policy: window 7d, tolerance 50c, cap 50c, national-only False

### System

You are a customer-support agent for a grocery chain. A customer writes in about a recent purchase. For each claim in their message, decide whether a refund is owed under the store's refund policy, and how much.

Each case carries its own policy parameters (claim window, price tolerance, price-match scope, refund cap), shown in the "Refund policy for this case" block of the message. Read that block and apply it exactly: the parameters differ from case to case.

Rules that hold for every case:
- Check the policy rules strictly in the order the block lists them; the first rule that decides determines the reason code.
- A claim phrased as a price complaint is judged under the price-match rule only, a claim phrased as a coupon complaint under the missed-coupon rule only, and a claim about a missing item under the item-on-receipt rule only. The item-on-receipt check runs before both: a claim that matches no line is NOT_ON_RECEIPT, and one that fits several lines without singling one out is NEEDS_CLARIFICATION, whatever rule the claim is phrased under.
- Amounts on the receipt always override amounts stated in the message.
- A live coupon covers a receipt line when the line matches the coupon's "covers" description (brand tier, category, size, and any exceptions).
- Approved refunds are paid in the order the claims appear. Once the case's refund cap is reached, later approved claims are refunded $0.00. If two approved claims are about the same receipt line, only the first is refunded.
- A price-match refund never exceeds what was paid for the item.

Output your reasoning, then exactly one answer block:

<answer>{"claims": [{"line": "L07" | null, "decision": "approve" | "reject", "reason": "<CODE>", "refund": 0.42}, ...]}</answer>

The claims array lists one entry per claim in the message, in the order they appear. "line" is the receipt line the claim refers to, or null when the item is not on the receipt. "refund" is 0 for every rejection. Reason codes: OUTSIDE_WINDOW, NOT_ON_RECEIPT, NEEDS_CLARIFICATION, PRICE_MATCH, WITHIN_TOLERANCE, MISSED_COUPON, NOT_ELIGIBLE, ALREADY_APPLIED.

### User

Purchase day: 606
Claim filed: day 608

Refund policy for this case (the first rule that decides determines the reason code):
1. Window: a claim filed more than 7 days after the purchase day is rejected (OUTSIDE_WINDOW).
2. Item on receipt: resolve the claim's wording against the receipt. Customers use words loosely: a word covers a receipt line when the line's category is one the word refers to ("cereal" covers hot cereal). When the wording names a specific kind ("ricotta", "greek yogurt"), it covers only lines of that kind (matching the sub-category), not every line of the broader category. If the claimed item matches no receipt line, reject with NOT_ON_RECEIPT. If the wording fits two or more receipt lines without singling one out, reject with NEEDS_CLARIFICATION (line null).
3. Price match: if the paid loyalty unit price (regular unit price minus loyalty discount) exceeds the reference price by more than $0.50 per unit, approve (PRICE_MATCH) and refund the difference times the quantity, never more than what was paid for the item. Otherwise reject (WITHIN_TOLERANCE).
4. Missed coupon: if no live coupon covers that receipt line, reject with NOT_ELIGIBLE. If a coupon discount was already applied on that line, reject with ALREADY_APPLIED. Otherwise approve with MISSED_COUPON and refund the coupon's typical value.
5. Refunds: Total refunds for this receipt are capped at $0.50. Approved refunds are paid in the order the claims appear; if two approved claims are about the same receipt line, only the first is refunded.

Receipt:
| line | category | sub-category | brand tier | size | qty | regular unit | loyalty disc | coupon disc | paid | reference |
| L01 | CHEESE | GRATED CHEESE | National | 8 OZ | 1 | $2.99 | $0.00 | $0.00 | $2.99 | $2.99 |
| L02 | VEGETABLES - ALL OTHERS | VEGETABLES ALL OTHER | National | 1 LB | 1 | $1.99 | $0.00 | $0.00 | $1.99 | $1.99 |
| L03 | BEANS - CANNED GLASS & MW | VARIETY BEANS - KIDNEY PINTO | National | 30 OZ | 1 | $1.69 | $0.30 | $0.00 | $1.39 | $1.39 |
| L04 | BAKED BREAD/BUNS/ROLLS | MAINSTREAM WHEAT/MULTIGRAIN BR | National | 20 OZ | 1 | $2.49 | $0.70 | $0.00 | $1.79 | $1.79 |
| L05 | VEGETABLES - SHELF STABLE | CORN | National | 15.25 OZ | 4 | $0.75 | $0.00 | $0.00 | $0.75 | $0.77 |
| L06 | PICKLE/RELISH/PKLD VEG | PICKLES | National | 16OZ | 2 | $3.29 | $1.29 | $0.00 | $2.00 | $2.00 |
| L07 | APPLES | APPLES GALA (BULK&BAG) | National |   | 1 | $3.80 | $0.00 | $0.00 | $3.80 | $2.88 |
| L08 | BAKED BREAD/BUNS/ROLLS | DINNER ROLLS | National | 12CT | 2 | $1.99 | $0.49 | $0.00 | $1.50 | $1.50 |
| L09 | CHEESE | CREAM CHEESE | National | L      8OZ | 1 | $1.45 | $0.45 | $0.00 | $1.00 | $1.00 |
| L10 | BAKING NEEDS | PIE FILLING MINCEMEAT GLAZES | National | 29 OZ | 1 | $2.19 | $0.60 | $0.00 | $1.59 | $1.59 |
| L11 | FLUID MILK PRODUCTS | BUTTERMILK | National | .5 GAL | 1 | $2.19 | $0.00 | $0.00 | $2.19 | $2.19 |
| L12 | SUGARS/SWEETNERS | SUGAR | National | 1 LB | 1 | $0.99 | $0.10 | $0.00 | $0.89 | $0.89 |
| L13 | SEAFOOD - SHELF STABLE | TUNA | National | 2.6 OZ | 1 | $1.19 | $0.00 | $0.00 | $1.19 | $1.19 |
| L14 | CANNED MILK | CANNED MILK | National | 12 OZ | 1 | $1.39 | $0.39 | $0.00 | $1.00 | $1.00 |
| L15 | BAKING NEEDS | PIE FILLING MINCEMEAT GLAZES | National | 30 OZ | 1 | $2.19 | $0.30 | $0.00 | $1.89 | $1.89 |
| L16 | REFRGRATD DOUGH PRODUCTS | REFRIGERATED SPECILATY ROLLS | National | 13.9 OZ | 2 | $2.19 | $0.61 | $0.40 | $1.18 | $1.58 |
| L17 | VEGETABLES - ALL OTHERS | CABBAGE | National | 14-18 CT | 1 | $0.94 | $0.00 | $0.00 | $0.94 | $1.07 |
| L18 | DRY NOODLES/PASTA | MACARONI DRY | National | 1LB | 1 | $1.19 | $0.19 | $0.00 | $1.00 | $1.00 |
| L19 | VEGETABLES SALAD | HEAD LETTUCE | National | 24CT | 1 | $0.99 | $0.00 | $0.00 | $0.99 | $0.99 |
| L20 | FLOUR & MEALS | CORNMEAL | National | 2 LB | 1 | $1.05 | $0.00 | $0.00 | $1.05 | $1.05 |
| L21 | VEGETABLES - SHELF STABLE | LIMA BEANS | National | 15.25 OZ | 1 | $1.29 | $0.00 | $0.00 | $1.29 | $1.29 |
| L22 | VEGETABLES - ALL OTHERS | CELERY | National |   | 1 | $1.89 | $0.60 | $0.00 | $1.29 | $1.29 |
| L23 | BROCCOLI/CAULIFLOWER | CAULIFLOWER WHOLE | National |   | 1 | $2.50 | $0.00 | $0.00 | $2.50 | $2.50 |
| L24 | NUTS | WALNUTS SHELLED | National | 1 LB | 1 | $5.99 | $1.00 | $0.00 | $4.99 | $4.99 |
| L25 | BAG SNACKS | PRETZELS | National | 16 OZ | 1 | $2.49 | $0.00 | $0.00 | $2.49 | $2.49 |

Live coupons on the customer's account:

| coupon | typical value | covers |
| C01 | $1.00 | national-brand apples, national-brand broccoli/cauliflower, national-brand nuts, national-brand vegetables - all others, national-brand vegetables salad |
| C02 | $0.35 | national-brand cheese, national-brand fluid milk products, national-brand refrgratd dough products |
| C03 | $0.50 | national-brand refrgratd dough products |
| C04 | $0.50 | national-brand cheese, except grated cheese |
| C05 | $1.00 | national-brand pickle/relish/pkld veg |

Customer message:

My gala apples rang up higher than the shelf tag said, and it feels like I got overcharged.


### Truth

| message | stated | line | decision | reason | refund |
|---|---|---|---|---|---|
| My gala apples rang up higher than the shelf tag said, and it feels like I got overcharged. | price | L07 | approve | PRICE_MATCH | 50c |

---

## eval_unseen-L1-0005 (anchor eval_unseen-0005, out-of-window: True)

Policy: window 21d, tolerance 25c, cap 50c, national-only True

### System

You are a customer-support agent for a grocery chain. A customer writes in about a recent purchase. For each claim in their message, decide whether a refund is owed under the store's refund policy, and how much.

Each case carries its own policy parameters (claim window, price tolerance, price-match scope, refund cap), shown in the "Refund policy for this case" block of the message. Read that block and apply it exactly: the parameters differ from case to case.

Rules that hold for every case:
- Check the policy rules strictly in the order the block lists them; the first rule that decides determines the reason code.
- A claim phrased as a price complaint is judged under the price-match rule only, a claim phrased as a coupon complaint under the missed-coupon rule only, and a claim about a missing item under the item-on-receipt rule only. The item-on-receipt check runs before both: a claim that matches no line is NOT_ON_RECEIPT, and one that fits several lines without singling one out is NEEDS_CLARIFICATION, whatever rule the claim is phrased under.
- Amounts on the receipt always override amounts stated in the message.
- A live coupon covers a receipt line when the line matches the coupon's "covers" description (brand tier, category, size, and any exceptions).
- Approved refunds are paid in the order the claims appear. Once the case's refund cap is reached, later approved claims are refunded $0.00. If two approved claims are about the same receipt line, only the first is refunded.
- A price-match refund never exceeds what was paid for the item.

Output your reasoning, then exactly one answer block:

<answer>{"claims": [{"line": "L07" | null, "decision": "approve" | "reject", "reason": "<CODE>", "refund": 0.42}, ...]}</answer>

The claims array lists one entry per claim in the message, in the order they appear. "line" is the receipt line the claim refers to, or null when the item is not on the receipt. "refund" is 0 for every rejection. Reason codes: OUTSIDE_WINDOW, NOT_ON_RECEIPT, NEEDS_CLARIFICATION, PRICE_MATCH, WITHIN_TOLERANCE, MISSED_COUPON, NOT_ELIGIBLE, ALREADY_APPLIED.

### User

Purchase day: 582
Claim filed: day 629

Refund policy for this case (the first rule that decides determines the reason code):
1. Window: a claim filed more than 21 days after the purchase day is rejected (OUTSIDE_WINDOW).
2. Item on receipt: resolve the claim's wording against the receipt. Customers use words loosely: a word covers a receipt line when the line's category is one the word refers to ("cereal" covers hot cereal). When the wording names a specific kind ("ricotta", "greek yogurt"), it covers only lines of that kind (matching the sub-category), not every line of the broader category. If the claimed item matches no receipt line, reject with NOT_ON_RECEIPT. If the wording fits two or more receipt lines without singling one out, reject with NEEDS_CLARIFICATION (line null).
3. Price match: if the paid loyalty unit price (regular unit price minus loyalty discount) exceeds the reference price by more than $0.25 per unit, approve (PRICE_MATCH) and refund the difference times the quantity, never more than what was paid for the item. Otherwise reject (WITHIN_TOLERANCE). Price matches apply to national-brand items only; price claims about other items are rejected (NOT_ELIGIBLE).
4. Missed coupon: if no live coupon covers that receipt line, reject with NOT_ELIGIBLE. If a coupon discount was already applied on that line, reject with ALREADY_APPLIED. Otherwise approve with MISSED_COUPON and refund the coupon's typical value.
5. Refunds: Total refunds for this receipt are capped at $0.50. Approved refunds are paid in the order the claims appear; if two approved claims are about the same receipt line, only the first is refunded.

Receipt:
| line | category | sub-category | brand tier | size | qty | regular unit | loyalty disc | coupon disc | paid | reference |
| L01 | BAKED SWEET GOODS | SNACK CAKE - MULTI PACK | National | 12 OZ | 2 | $1.29 | $0.00 | $0.00 | $1.29 | $1.29 |
| L02 | FROZEN PIZZA | SNACKS/APPETIZERS | National | 11 OZ | 1 | $3.99 | $0.30 | $1.00 | $2.69 | $4.54 |
| L03 | CHEESE | SHREDDED CHEESE | Private | 8 OZ | 1 | $1.78 | $0.53 | $0.00 | $1.25 | $1.25 |
| L04 | CAT LITTER | SCOOP LITTER | National | 14 LB | 1 | $6.69 | $2.40 | $0.00 | $4.29 | $4.29 |
| L05 | BAKED SWEET GOODS | SNACK CAKE - MULTI PACK | National | 10.6 OZ | 1 | $1.29 | $0.00 | $0.00 | $1.29 | $1.29 |
| L06 | FROZEN PIZZA | PIZZA/SINGLE SERVE/MICROWAVE | National | 12 OZ | 1 | $3.82 | $0.00 | $1.00 | $2.82 | $3.82 |
| L07 | BAKED SWEET GOODS | SNACK CAKE - MULTI PACK | National | 9.5 OZ | 2 | $1.09 | $0.00 | $0.00 | $1.09 | $1.09 |
| L08 | FRZN VEGETABLE/VEG DSH | FRZN BAGGED VEGETABLES - PLAIN | Private | 16 OZ | 2 | $1.59 | $0.59 | $0.00 | $1.00 | $1.00 |
| L09 | FROZEN PIZZA | PIZZA/SINGLE SERVE/MICROWAVE | National | 11 OZ | 2 | $3.82 | $0.00 | $1.00 | $2.82 | $3.58 |
| L10 | BAKED SWEET GOODS | SWEET GOODS - FULL SIZE | Private | 10 OZ | 1 | $1.69 | $0.44 | $0.00 | $1.25 | $1.25 |
| L11 | FLUID MILK PRODUCTS | FLUID MILK WHITE ONLY | Private | 1 GA | 1 | $2.27 | $0.00 | $0.00 | $2.27 | $2.79 |
| L12 | CRACKERS/MISC BKD FD | BUTTER SPRAY CRACKER (RITZ/CLU | National | 16 OZ | 1 | $3.39 | $0.70 | $0.00 | $2.69 | $2.69 |
| L13 | CHEESE | CREAM CHEESE | Private | L     8 OZ | 2 | $1.22 | $0.22 | $0.00 | $1.00 | $1.00 |
| L14 | TROPICAL FRUIT | BANANAS | National | 40 LB | 2 | $1.01 | $0.00 | $0.00 | $1.01 | $0.99 |
| L15 | FROZEN PIZZA | PIZZA/SINGLE SERVE/MICROWAVE | National | 12 OZ | 3 | $3.82 | $0.00 | $1.00 | $2.82 | $3.41 |
| L16 | MARGARINES | MARGARINE: TUBS AND BOWLS | National | 3 LB | 1 | $2.99 | $0.99 | $0.00 | $2.00 | $2.00 |
| L17 | CRACKERS/MISC BKD FD | BUTTER SPRAY CRACKER (RITZ/CLU | Private | 16 OZ | 1 | $2.99 | $1.32 | $0.00 | $1.67 | $1.67 |
| L18 | ROLLS | ROLLS: BAGELS | National | 4 OZ | 4 | $0.50 | $0.00 | $0.00 | $0.50 | $0.50 |
| L19 | PLASTIC HOUSEWARES | DISPOSABLE FD STORAGE CONTAINR | National | 24 OZ | 1 | $3.39 | $0.00 | $0.40 | $2.99 | $3.39 |
| L20 | BAKED SWEET GOODS | SWEET GOODS - FULL SIZE | Private | 6CT/15OZ | 1 | $1.79 | $0.54 | $0.00 | $1.25 | $1.25 |
| L21 | COLD CEREAL | KIDS CEREAL | National | 17.2 OZ | 1 | $3.69 | $0.70 | $0.00 | $2.99 | $2.99 |
| L22 | LUNCHMEAT | MISCELLANEOUS | Private | 2.0 OZ | 2 | $0.69 | $0.19 | $0.00 | $0.50 | $0.50 |
| L23 | FRZN VEGETABLE/VEG DSH | FRZN BOXED VEGETABLES - PLAIN | National | 12 OZ | 2 | $2.89 | $0.56 | $1.00 | $1.33 | $1.59 |
| L24 | BAKED BREAD/BUNS/ROLLS | MAINSTREAM WHITE BREAD | Private | 16 OZ | 1 | $0.75 | $0.00 | $0.00 | $0.75 | $0.75 |

Live coupons on the customer's account:

(none)

Customer message:

My digital coupon for the CREAM CHEESE didn't come off at the register, so I paid full price for it.


### Truth

| message | stated | line | decision | reason | refund |
|---|---|---|---|---|---|
| My digital coupon for the CREAM CHEESE didn't come off at the register, so I paid full price for it. | coupon | L13 | reject | OUTSIDE_WINDOW | 0c |

---

## eval_unseen-L1-0006 (anchor eval_unseen-0006, out-of-window: False)

Policy: window 30d, tolerance 50c, cap 50c, national-only False

### System

You are a customer-support agent for a grocery chain. A customer writes in about a recent purchase. For each claim in their message, decide whether a refund is owed under the store's refund policy, and how much.

Each case carries its own policy parameters (claim window, price tolerance, price-match scope, refund cap), shown in the "Refund policy for this case" block of the message. Read that block and apply it exactly: the parameters differ from case to case.

Rules that hold for every case:
- Check the policy rules strictly in the order the block lists them; the first rule that decides determines the reason code.
- A claim phrased as a price complaint is judged under the price-match rule only, a claim phrased as a coupon complaint under the missed-coupon rule only, and a claim about a missing item under the item-on-receipt rule only. The item-on-receipt check runs before both: a claim that matches no line is NOT_ON_RECEIPT, and one that fits several lines without singling one out is NEEDS_CLARIFICATION, whatever rule the claim is phrased under.
- Amounts on the receipt always override amounts stated in the message.
- A live coupon covers a receipt line when the line matches the coupon's "covers" description (brand tier, category, size, and any exceptions).
- Approved refunds are paid in the order the claims appear. Once the case's refund cap is reached, later approved claims are refunded $0.00. If two approved claims are about the same receipt line, only the first is refunded.
- A price-match refund never exceeds what was paid for the item.

Output your reasoning, then exactly one answer block:

<answer>{"claims": [{"line": "L07" | null, "decision": "approve" | "reject", "reason": "<CODE>", "refund": 0.42}, ...]}</answer>

The claims array lists one entry per claim in the message, in the order they appear. "line" is the receipt line the claim refers to, or null when the item is not on the receipt. "refund" is 0 for every rejection. Reason codes: OUTSIDE_WINDOW, NOT_ON_RECEIPT, NEEDS_CLARIFICATION, PRICE_MATCH, WITHIN_TOLERANCE, MISSED_COUPON, NOT_ELIGIBLE, ALREADY_APPLIED.

### User

Purchase day: 498
Claim filed: day 505

Refund policy for this case (the first rule that decides determines the reason code):
1. Window: a claim filed more than 30 days after the purchase day is rejected (OUTSIDE_WINDOW).
2. Item on receipt: resolve the claim's wording against the receipt. Customers use words loosely: a word covers a receipt line when the line's category is one the word refers to ("cereal" covers hot cereal). When the wording names a specific kind ("ricotta", "greek yogurt"), it covers only lines of that kind (matching the sub-category), not every line of the broader category. If the claimed item matches no receipt line, reject with NOT_ON_RECEIPT. If the wording fits two or more receipt lines without singling one out, reject with NEEDS_CLARIFICATION (line null).
3. Price match: if the paid loyalty unit price (regular unit price minus loyalty discount) exceeds the reference price by more than $0.50 per unit, approve (PRICE_MATCH) and refund the difference times the quantity, never more than what was paid for the item. Otherwise reject (WITHIN_TOLERANCE).
4. Missed coupon: if no live coupon covers that receipt line, reject with NOT_ELIGIBLE. If a coupon discount was already applied on that line, reject with ALREADY_APPLIED. Otherwise approve with MISSED_COUPON and refund the coupon's typical value.
5. Refunds: Total refunds for this receipt are capped at $0.50. Approved refunds are paid in the order the claims appear; if two approved claims are about the same receipt line, only the first is refunded.

Receipt:
| line | category | sub-category | brand tier | size | qty | regular unit | loyalty disc | coupon disc | paid | reference |
| L01 | SOFT DRINKS | SFT DRNK 2 LITER BTL CARB INCL | National | 2 LTR | 1 | $1.59 | $0.59 | $0.00 | $1.00 | $1.00 |
| L02 | DELI MEATS | MEAT: SAUS DRY BULK | National |   | 1 | $3.17 | $0.00 | $0.00 | $3.17 | $2.96 |
| L03 | BAKED BREAD/BUNS/ROLLS | MAINSTREAM WHITE BREAD | National | 20 OZ | 2 | $1.99 | $0.00 | $0.00 | $1.99 | $1.99 |
| L04 | DELI MEATS | MEAT:HAM BULK | National |   | 1 | $3.50 | $0.50 | $0.00 | $3.00 | $4.46 |
| L05 | BLEACH | LIQUID BLEACH | National | 96 OZ | 1 | $1.99 | $0.00 | $0.00 | $1.99 | $1.99 |
| L06 | DISHWASH DETERGENTS | LIQUID DISH DETERGENT | National | 25 OZ | 1 | $1.76 | $0.00 | $0.00 | $1.76 | $1.76 |
| L07 | TROPICAL FRUIT | BANANAS | National | 40 LB | 1 | $1.36 | $0.00 | $0.00 | $1.36 | $1.02 |
| L08 | DELI MEATS | MEAT: CHICKEN BULK | National |   | 1 | $3.77 | $0.54 | $0.00 | $3.23 | $3.14 |
| L09 | DELI MEATS | MEAT: TURKEY BULK | National |   | 1 | $4.05 | $0.58 | $0.00 | $3.47 | $5.71 |
| L10 | SOFT DRINKS | SFT DRNK 2 LITER BTL CARB INCL | National | 2 LTR | 1 | $1.59 | $0.59 | $0.00 | $1.00 | $1.00 |
| L11 | CHEESES | CHEESE: NATURAL BULK | National |   | 1 | $4.53 | $1.18 | $1.00 | $2.35 | $2.41 |
| L12 | SALD DRSNG/SNDWCH SPRD | SEMI-SOLID SALAD DRESSING MAY | National | 32 OZ | 1 | $3.15 | $0.00 | $0.00 | $3.15 | $3.15 |

Live coupons on the customer's account:

(none)

Customer message:

I think I got overcharged on my 2 liter soda, since the price on the shelf was lower than what rang up at the register.


### Truth

| message | stated | line | decision | reason | refund |
|---|---|---|---|---|---|
| I think I got overcharged on my 2 liter soda, since the price on the shelf was lower than what rang up at the register. | price | None | reject | NEEDS_CLARIFICATION | 0c |

---

## eval_unseen-L1-0007 (anchor eval_unseen-0007, out-of-window: False)

Policy: window 7d, tolerance 25c, cap 75c, national-only False

### System

You are a customer-support agent for a grocery chain. A customer writes in about a recent purchase. For each claim in their message, decide whether a refund is owed under the store's refund policy, and how much.

Each case carries its own policy parameters (claim window, price tolerance, price-match scope, refund cap), shown in the "Refund policy for this case" block of the message. Read that block and apply it exactly: the parameters differ from case to case.

Rules that hold for every case:
- Check the policy rules strictly in the order the block lists them; the first rule that decides determines the reason code.
- A claim phrased as a price complaint is judged under the price-match rule only, a claim phrased as a coupon complaint under the missed-coupon rule only, and a claim about a missing item under the item-on-receipt rule only. The item-on-receipt check runs before both: a claim that matches no line is NOT_ON_RECEIPT, and one that fits several lines without singling one out is NEEDS_CLARIFICATION, whatever rule the claim is phrased under.
- Amounts on the receipt always override amounts stated in the message.
- A live coupon covers a receipt line when the line matches the coupon's "covers" description (brand tier, category, size, and any exceptions).
- Approved refunds are paid in the order the claims appear. Once the case's refund cap is reached, later approved claims are refunded $0.00. If two approved claims are about the same receipt line, only the first is refunded.
- A price-match refund never exceeds what was paid for the item.

Output your reasoning, then exactly one answer block:

<answer>{"claims": [{"line": "L07" | null, "decision": "approve" | "reject", "reason": "<CODE>", "refund": 0.42}, ...]}</answer>

The claims array lists one entry per claim in the message, in the order they appear. "line" is the receipt line the claim refers to, or null when the item is not on the receipt. "refund" is 0 for every rejection. Reason codes: OUTSIDE_WINDOW, NOT_ON_RECEIPT, NEEDS_CLARIFICATION, PRICE_MATCH, WITHIN_TOLERANCE, MISSED_COUPON, NOT_ELIGIBLE, ALREADY_APPLIED.

### User

Purchase day: 648
Claim filed: day 650

Refund policy for this case (the first rule that decides determines the reason code):
1. Window: a claim filed more than 7 days after the purchase day is rejected (OUTSIDE_WINDOW).
2. Item on receipt: resolve the claim's wording against the receipt. Customers use words loosely: a word covers a receipt line when the line's category is one the word refers to ("cereal" covers hot cereal). When the wording names a specific kind ("ricotta", "greek yogurt"), it covers only lines of that kind (matching the sub-category), not every line of the broader category. If the claimed item matches no receipt line, reject with NOT_ON_RECEIPT. If the wording fits two or more receipt lines without singling one out, reject with NEEDS_CLARIFICATION (line null).
3. Price match: if the paid loyalty unit price (regular unit price minus loyalty discount) exceeds the reference price by more than $0.25 per unit, approve (PRICE_MATCH) and refund the difference times the quantity, never more than what was paid for the item. Otherwise reject (WITHIN_TOLERANCE).
4. Missed coupon: if no live coupon covers that receipt line, reject with NOT_ELIGIBLE. If a coupon discount was already applied on that line, reject with ALREADY_APPLIED. Otherwise approve with MISSED_COUPON and refund the coupon's typical value.
5. Refunds: Total refunds for this receipt are capped at $0.75. Approved refunds are paid in the order the claims appear; if two approved claims are about the same receipt line, only the first is refunded.

Receipt:
| line | category | sub-category | brand tier | size | qty | regular unit | loyalty disc | coupon disc | paid | reference |
| L01 | EGGS | EGGS - LARGE | Private | 1 DZ | 1 | $1.09 | $0.00 | $0.00 | $1.09 | $1.09 |
| L02 | CHEESES | CHEESE: NATURAL PREPORTND | National | 8 OZ | 1 | $4.54 | $0.00 | $1.00 | $3.54 | $4.54 |
| L03 | SOAP - LIQUID & BAR | BODY WASH | National | 18 OZ | 1 | $4.74 | $0.00 | $1.00 | $3.74 | $4.74 |
| L04 | CHEESES | CHEESE: NATURAL PREPORTND | National | 8 OZ | 1 | $3.99 | $0.00 | $0.00 | $3.99 | $3.99 |
| L05 | SALAD MIX | BLENDS | National | 10 OZ | 1 | $3.54 | $0.00 | $1.00 | $2.54 | $3.54 |
| L06 | SYRUPS/TOPPINGS | ICE CREAM TOPPINGS | National | 15 OZ | 1 | $1.99 | $0.00 | $0.00 | $1.99 | $1.99 |
| L07 | SUGARS/SWEETNERS | SWEETENERS | National | 7 OZ | 1 | $7.99 | $0.00 | $0.00 | $7.99 | $7.99 |
| L08 | CITRUS | ORANGES NAVELS ALL | National |   | 2 | $0.67 | $0.00 | $0.00 | $0.67 | $0.69 |
| L09 | MARGARINES | MARGARINE: TUBS AND BOWLS | National | 24 OZ | 1 | $2.54 | $0.00 | $0.70 | $1.84 | $2.54 |
| L10 | SHORTENING/OIL | VEGETABLE/SALAD OIL | National | 48 OZ | 1 | $3.99 | $1.69 | $0.60 | $1.70 | $2.30 |
| L11 | SALAD MIX | COLESLAW | National | 16 OZ | 1 | $1.69 | $0.69 | $0.00 | $1.00 | $1.00 |
| L12 | BREAKFAST SAUSAGE/SANDWICHES | ROLLS - FLAVORED/OTHER | National | 16 OZ | 2 | $3.92 | $1.29 | $0.25 | $2.38 | $2.50 |
| L13 | OLIVES | RIPE OLIVES | Private | 6 OZ | 2 | $1.07 | $0.07 | $0.00 | $1.00 | $1.00 |
| L14 | SALAD MIX | BLENDS | National | 5 OZ | 1 | $3.99 | $0.00 | $1.00 | $2.99 | $3.99 |
| L15 | FLUID MILK PRODUCTS | REFRIGERATED COFFEE CREAMERS | National | 16 OZ | 3 | $1.99 | $0.20 | $0.00 | $1.79 | $1.79 |
| L16 | GREETING CARDS/WRAP/PARTY SPLY | CARDS EVERYDAY | National |   | 1 | $0.99 | $0.00 | $0.00 | $0.99 | $0.99 |
| L17 | CONDIMENTS/SAUCES | SALAD MUSTARD | Private | 16 OZ | 1 | $0.79 | $0.10 | $0.00 | $0.69 | $0.69 |
| L18 | SALAD MIX | REGULAR GARDEN | National | 10 OZ | 1 | $2.99 | $0.00 | $0.00 | $2.99 | $2.99 |
| L19 | SOAP - LIQUID & BAR | BAR SOAP | National | 32 OZ | 1 | $4.09 | $0.00 | $0.60 | $3.49 | $4.09 |
| L20 | CANNED JUICES | BLENDED JUICE&COMBINATIONS (OV | National | 64 OZ | 1 | $2.78 | $0.00 | $0.80 | $1.98 | $2.58 |

Live coupons on the customer's account:

| coupon | typical value | covers |
| C01 | $1.00 | national-brand greeting cards/wrap/party sply |
| C02 | $0.75 | national-brand canned juices |

Customer message:

The digital coupon I clipped for the soap got skipped at checkout even though it was active on my phone.


### Truth

| message | stated | line | decision | reason | refund |
|---|---|---|---|---|---|
| The digital coupon I clipped for the soap got skipped at checkout even though it was active on my phone. | coupon | None | reject | NEEDS_CLARIFICATION | 0c |

---

## eval_unseen-L1-0008 (anchor eval_unseen-0008, out-of-window: False)

Policy: window 21d, tolerance 15c, cap 50c, national-only True

### System

You are a customer-support agent for a grocery chain. A customer writes in about a recent purchase. For each claim in their message, decide whether a refund is owed under the store's refund policy, and how much.

Each case carries its own policy parameters (claim window, price tolerance, price-match scope, refund cap), shown in the "Refund policy for this case" block of the message. Read that block and apply it exactly: the parameters differ from case to case.

Rules that hold for every case:
- Check the policy rules strictly in the order the block lists them; the first rule that decides determines the reason code.
- A claim phrased as a price complaint is judged under the price-match rule only, a claim phrased as a coupon complaint under the missed-coupon rule only, and a claim about a missing item under the item-on-receipt rule only. The item-on-receipt check runs before both: a claim that matches no line is NOT_ON_RECEIPT, and one that fits several lines without singling one out is NEEDS_CLARIFICATION, whatever rule the claim is phrased under.
- Amounts on the receipt always override amounts stated in the message.
- A live coupon covers a receipt line when the line matches the coupon's "covers" description (brand tier, category, size, and any exceptions).
- Approved refunds are paid in the order the claims appear. Once the case's refund cap is reached, later approved claims are refunded $0.00. If two approved claims are about the same receipt line, only the first is refunded.
- A price-match refund never exceeds what was paid for the item.

Output your reasoning, then exactly one answer block:

<answer>{"claims": [{"line": "L07" | null, "decision": "approve" | "reject", "reason": "<CODE>", "refund": 0.42}, ...]}</answer>

The claims array lists one entry per claim in the message, in the order they appear. "line" is the receipt line the claim refers to, or null when the item is not on the receipt. "refund" is 0 for every rejection. Reason codes: OUTSIDE_WINDOW, NOT_ON_RECEIPT, NEEDS_CLARIFICATION, PRICE_MATCH, WITHIN_TOLERANCE, MISSED_COUPON, NOT_ELIGIBLE, ALREADY_APPLIED.

### User

Purchase day: 489
Claim filed: day 501

Refund policy for this case (the first rule that decides determines the reason code):
1. Window: a claim filed more than 21 days after the purchase day is rejected (OUTSIDE_WINDOW).
2. Item on receipt: resolve the claim's wording against the receipt. Customers use words loosely: a word covers a receipt line when the line's category is one the word refers to ("cereal" covers hot cereal). When the wording names a specific kind ("ricotta", "greek yogurt"), it covers only lines of that kind (matching the sub-category), not every line of the broader category. If the claimed item matches no receipt line, reject with NOT_ON_RECEIPT. If the wording fits two or more receipt lines without singling one out, reject with NEEDS_CLARIFICATION (line null).
3. Price match: if the paid loyalty unit price (regular unit price minus loyalty discount) exceeds the reference price by more than $0.15 per unit, approve (PRICE_MATCH) and refund the difference times the quantity, never more than what was paid for the item. Otherwise reject (WITHIN_TOLERANCE). Price matches apply to national-brand items only; price claims about other items are rejected (NOT_ELIGIBLE).
4. Missed coupon: if no live coupon covers that receipt line, reject with NOT_ELIGIBLE. If a coupon discount was already applied on that line, reject with ALREADY_APPLIED. Otherwise approve with MISSED_COUPON and refund the coupon's typical value.
5. Refunds: Total refunds for this receipt are capped at $0.50. Approved refunds are paid in the order the claims appear; if two approved claims are about the same receipt line, only the first is refunded.

Receipt:
| line | category | sub-category | brand tier | size | qty | regular unit | loyalty disc | coupon disc | paid | reference |
| L01 | MEAT - MISC | BREAST - BONELESS(IQF) | Private | 3 LB | 1 | $8.99 | $4.00 | $0.00 | $4.99 | $4.99 |
| L02 | CARROTS | CARROTS MINI PEELED | Private | 2 LB | 1 | $2.99 | $0.00 | $0.00 | $2.99 | $2.99 |
| L03 | CHICKEN/POULTRY | CHIX: VALUE ADDED (HOT) | Private |   | 1 | $1.69 | $0.69 | $0.00 | $1.00 | $1.69 |
| L04 | CHEESE | GRATED CHEESE | Private | 8 OZ | 1 | $2.38 | $0.38 | $0.00 | $2.00 | $2.00 |
| L05 | SALADS/DIPS | SAL: SALSA/DIPS BULK | National |   | 1 | $2.83 | $0.00 | $0.00 | $2.83 | $4.67 |
| L06 | CHEESE | IWS SINGLE CHEESE | National | 16 OZ | 1 | $2.99 | $0.00 | $0.00 | $2.99 | $2.99 |
| L07 | ROLLS | ROLLS: DINNER | National | 12 OZ | 1 | $2.49 | $0.00 | $0.00 | $2.49 | $2.49 |
| L08 | HOT DOGS | PREMIUM - MEAT | National | 1 LB | 2 | $3.29 | $0.00 | $0.00 | $3.29 | $3.29 |
| L09 | BAG SNACKS | TORTILLA/NACHO CHIPS | Private | 13.5OZ | 1 | $2.59 | $0.59 | $0.00 | $2.00 | $2.00 |
| L10 | BUTTER | BUTTER | Private | 1 LB | 1 | $3.15 | $1.16 | $0.00 | $1.99 | $1.99 |
| L11 | BREAD | BREAD:LOAF/SNACK | Private |   | 1 | $1.79 | $0.00 | $0.00 | $1.79 | $1.79 |
| L12 | SALAD MIX | GARDEN PLUS | National | 12 OZ | 2 | $2.99 | $0.99 | $0.00 | $2.00 | $2.00 |
| L13 | HISPANIC | MEXICAN SAUCESSALSAPICANTEE | National | 15.5 OZ | 1 | $2.89 | $0.00 | $0.00 | $2.89 | $2.89 |
| L14 | SOFT DRINKS | SFT DRNK SNGL SRV BTL CARB (EX | National | 20 OZ | 1 | $1.29 | $0.30 | $0.00 | $0.99 | $0.99 |
| L15 | SOFT DRINKS | SFT DRNK SNGL SRV BTL CARB (EX | National | 20 OZ | 1 | $1.29 | $0.30 | $0.00 | $0.99 | $0.99 |
| L16 | TOMATOES | TOMATOES VINE RIPE BULK | National | 15 LB | 1 | $3.24 | $0.00 | $0.00 | $3.24 | $1.97 |
| L17 | TROPICAL FRUIT | BANANAS | National | 40 LB | 1 | $1.12 | $0.00 | $0.00 | $1.12 | $1.02 |
| L18 | BAKED BREAD/BUNS/ROLLS | HOT DOG BUNS | Private | 11 OZ | 2 | $1.29 | $0.41 | $0.00 | $0.88 | $0.88 |
| L19 | CHEESES | CHEESE: NATURAL BULK | National |   | 1 | $4.00 | $1.00 | $1.00 | $2.00 | $2.35 |
| L20 | DINNER SAUSAGE | RED | National | 1 LB | 1 | $3.99 | $0.00 | $0.00 | $3.99 | $1.99 |
| L21 | DELI MEATS | MEAT: TURKEY BULK | National |   | 1 | $6.92 | $0.99 | $0.00 | $5.93 | $5.93 |
| L22 | SOFT DRINKS | SOFT DRINKS 12/18&15PK CAN CAR | National | 12 OZ | 1 | $4.69 | $1.69 | $0.00 | $3.00 | $3.00 |
| L23 | SOFT DRINKS | SOFT DRINKS 12/18&15PK CAN CAR | National | 12 OZ | 1 | $4.69 | $1.69 | $0.00 | $3.00 | $3.00 |
| L24 | SOFT DRINKS | SOFT DRINKS 12/18&15PK CAN CAR | National | 12 OZ | 1 | $4.69 | $1.69 | $0.00 | $3.00 | $3.00 |
| L25 | BEEF | PATTIES | National |   | 2 | $4.07 | $0.55 | $0.00 | $3.52 | $3.80 |
| L26 | BAKED BREAD/BUNS/ROLLS | HAMBURGER BUNS | Private | 16 OZ | 2 | $1.39 | $0.51 | $0.00 | $0.88 | $0.88 |

Live coupons on the customer's account:

(none)

Customer message:

My digital coupon never came off the loaf of bread, even though it was loaded in my app before I checked out.


### Truth

| message | stated | line | decision | reason | refund |
|---|---|---|---|---|---|
| My digital coupon never came off the loaf of bread, even though it was loaded in my app before I checked out. | coupon | L11 | reject | NOT_ELIGIBLE | 0c |

---

## eval_unseen-L1-0009 (anchor eval_unseen-0009, out-of-window: False)

Policy: window 21d, tolerance 50c, cap 50c, national-only True

### System

You are a customer-support agent for a grocery chain. A customer writes in about a recent purchase. For each claim in their message, decide whether a refund is owed under the store's refund policy, and how much.

Each case carries its own policy parameters (claim window, price tolerance, price-match scope, refund cap), shown in the "Refund policy for this case" block of the message. Read that block and apply it exactly: the parameters differ from case to case.

Rules that hold for every case:
- Check the policy rules strictly in the order the block lists them; the first rule that decides determines the reason code.
- A claim phrased as a price complaint is judged under the price-match rule only, a claim phrased as a coupon complaint under the missed-coupon rule only, and a claim about a missing item under the item-on-receipt rule only. The item-on-receipt check runs before both: a claim that matches no line is NOT_ON_RECEIPT, and one that fits several lines without singling one out is NEEDS_CLARIFICATION, whatever rule the claim is phrased under.
- Amounts on the receipt always override amounts stated in the message.
- A live coupon covers a receipt line when the line matches the coupon's "covers" description (brand tier, category, size, and any exceptions).
- Approved refunds are paid in the order the claims appear. Once the case's refund cap is reached, later approved claims are refunded $0.00. If two approved claims are about the same receipt line, only the first is refunded.
- A price-match refund never exceeds what was paid for the item.

Output your reasoning, then exactly one answer block:

<answer>{"claims": [{"line": "L07" | null, "decision": "approve" | "reject", "reason": "<CODE>", "refund": 0.42}, ...]}</answer>

The claims array lists one entry per claim in the message, in the order they appear. "line" is the receipt line the claim refers to, or null when the item is not on the receipt. "refund" is 0 for every rejection. Reason codes: OUTSIDE_WINDOW, NOT_ON_RECEIPT, NEEDS_CLARIFICATION, PRICE_MATCH, WITHIN_TOLERANCE, MISSED_COUPON, NOT_ELIGIBLE, ALREADY_APPLIED.

### User

Purchase day: 545
Claim filed: day 561

Refund policy for this case (the first rule that decides determines the reason code):
1. Window: a claim filed more than 21 days after the purchase day is rejected (OUTSIDE_WINDOW).
2. Item on receipt: resolve the claim's wording against the receipt. Customers use words loosely: a word covers a receipt line when the line's category is one the word refers to ("cereal" covers hot cereal). When the wording names a specific kind ("ricotta", "greek yogurt"), it covers only lines of that kind (matching the sub-category), not every line of the broader category. If the claimed item matches no receipt line, reject with NOT_ON_RECEIPT. If the wording fits two or more receipt lines without singling one out, reject with NEEDS_CLARIFICATION (line null).
3. Price match: if the paid loyalty unit price (regular unit price minus loyalty discount) exceeds the reference price by more than $0.50 per unit, approve (PRICE_MATCH) and refund the difference times the quantity, never more than what was paid for the item. Otherwise reject (WITHIN_TOLERANCE). Price matches apply to national-brand items only; price claims about other items are rejected (NOT_ELIGIBLE).
4. Missed coupon: if no live coupon covers that receipt line, reject with NOT_ELIGIBLE. If a coupon discount was already applied on that line, reject with ALREADY_APPLIED. Otherwise approve with MISSED_COUPON and refund the coupon's typical value.
5. Refunds: Total refunds for this receipt are capped at $0.50. Approved refunds are paid in the order the claims appear; if two approved claims are about the same receipt line, only the first is refunded.

Receipt:
| line | category | sub-category | brand tier | size | qty | regular unit | loyalty disc | coupon disc | paid | reference |
| L01 | FROZEN PIZZA | SNACKS/APPETIZERS | National | 44.5 OZ | 1 | $8.19 | $0.00 | $0.00 | $8.19 | $8.19 |
| L02 | COFFEE FILTERS | WATER FILTER | National |   | 1 | $16.99 | $0.00 | $0.00 | $16.99 | $16.99 |
| L03 | WATER - CARBONATED/FLVRD DRINK | NON-CRBNTD DRNKING/MNERAL WATE | Private | 405.6 OZ | 1 | $3.99 | $0.00 | $0.00 | $3.99 | $3.99 |
| L04 | PASTA SAUCE | MAINSTREAM | National | 26 OZ | 1 | $2.39 | $0.10 | $0.00 | $2.29 | $2.29 |
| L05 | CHEESE | SHREDDED CHEESE | Private | 8 OZ | 3 | $1.78 | $0.53 | $0.00 | $1.25 | $1.25 |
| L06 | BEANS - CANNED GLASS & MW | PEAS FRESH PACK CROWDER | National | 15 OZ | 1 | $1.29 | $0.00 | $0.00 | $1.29 | $1.29 |
| L07 | DOG FOODS | CAN DOGFD GOURMET/SUPER PREM ( | National | 3.5 OZ | 12 | $0.79 | $0.00 | $0.00 | $0.79 | $0.79 |
| L08 | BEANS - CANNED GLASS & MW | VARIETY BEANS - KIDNEY PINTO | Private | 15.5 OZ | 1 | $0.52 | $0.00 | $0.00 | $0.52 | $0.52 |
| L09 | FROZEN PIZZA | PIZZA/PREMIUM | National | 30.5 OZ | 1 | $5.48 | $0.98 | $0.00 | $4.50 | $4.50 |
| L10 | BEANS - CANNED GLASS & MW | VARIETY BEANS - KIDNEY PINTO | National | 15.5 OZ | 2 | $0.99 | $0.00 | $0.00 | $0.99 | $0.99 |
| L11 | WATER - CARBONATED/FLVRD DRINK | NON-CRBNTD DRNKING/MNERAL WATE | Private | GAL | 4 | $0.79 | $0.00 | $0.00 | $0.79 | $0.79 |
| L12 | DOG FOODS | DOG BISCUITS (HARD BISCUIT) | Private | 5 LB | 1 | $3.69 | $0.00 | $0.00 | $3.69 | $3.69 |
| L13 | CAT LITTER | CONVENTIONAL LITTER | National | 20 LB | 1 | $4.69 | $0.70 | $0.00 | $3.99 | $3.99 |
| L14 | FROZEN PIZZA | PIZZA/PREMIUM | National | 32.7 OZ | 1 | $5.48 | $0.98 | $0.00 | $4.50 | $4.50 |
| L15 | CRACKERS/MISC BKD FD | SOUP CRACKERS (SALTINE/OYSTER) | Private | 16 OZ | 2 | $1.39 | $0.39 | $0.00 | $1.00 | $1.00 |
| L16 | SPICES & EXTRACTS | SPICES & SEASONINGS | Private | 2.5 OZ | 1 | $2.49 | $0.00 | $0.00 | $2.49 | $2.49 |
| L17 | SOUP | CONDENSED SOUP | National | 10.5 OZ | 1 | $1.49 | $0.49 | $0.00 | $1.00 | $1.00 |
| L18 | BLEACH | LIQUID BLEACH | National | 82 OZ | 1 | $1.99 | $0.20 | $0.00 | $1.79 | $1.79 |
| L19 | BEEF | LEAN | National |   | 2 | $4.02 | $0.00 | $0.00 | $4.02 | $3.90 |
| L20 | TEAS | TEA BAGS & BULK TEA | Private | 24 CT | 1 | $2.29 | $0.00 | $0.00 | $2.29 | $2.29 |
| L21 | SOUP | BOUILLON | Private | 25 CT | 1 | $1.39 | $0.00 | $0.00 | $1.39 | $1.39 |
| L22 | CANNED JUICES | TOMATO JUICE (OVER 50% JCE) | National | 46 OZ | 1 | $1.49 | $0.24 | $0.00 | $1.25 | $1.25 |
| L23 | SOUP | CONDENSED SOUP | National | 10.5OZ | 1 | $1.49 | $0.49 | $0.00 | $1.00 | $1.00 |
| L24 | HOUSEHOLD CLEANG NEEDS | GLASS CLEANERS | National | 28 CT | 1 | $2.99 | $0.00 | $0.00 | $2.99 | $2.99 |
| L25 | SOUP | CONDENSED SOUP | National | 10.5 OZ | 1 | $1.49 | $0.49 | $0.00 | $1.00 | $1.00 |
| L26 | LAUNDRY ADDITIVES | FABRIC SOFTENER SHEETS | National | 70 CT | 1 | $4.59 | $0.00 | $0.00 | $4.59 | $4.59 |
| L27 | YOGURT | YOGURT MULTI-PACKS | National | 20 OZ | 1 | $3.29 | $0.60 | $0.00 | $2.69 | $2.69 |
| L28 | VEGETABLES - SHELF STABLE | TOMATOES: STEWED/DICED/CRMD | National | 14.5 OZ | 2 | $1.59 | $0.59 | $0.00 | $1.00 | $1.00 |
| L29 | YOGURT | YOGURT MULTI-PACKS | National | 16 OZ | 1 | $2.49 | $0.20 | $0.00 | $2.29 | $2.29 |
| L30 | DRY NOODLES/PASTA | MACARONI DRY | Private | 12 OZ | 1 | $0.89 | $0.00 | $0.00 | $0.89 | $0.89 |
| L31 | CANNED JUICES | ASEPTIC PACK JUICE AND DRINKS | National | 67.5 OZ | 1 | $2.08 | $0.00 | $0.00 | $2.08 | $1.96 |
| L32 | DRY NOODLES/PASTA | SPAGHETTI DRY | National | 13.25 OZ | 2 | $1.99 | $0.99 | $0.00 | $1.00 | $1.00 |
| L33 | LAUNDRY ADDITIVES | FABRIC SOFTENER LIQUID | National | 32 LD | 1 | $5.59 | $0.60 | $1.00 | $3.99 | $4.99 |

Live coupons on the customer's account:

(none)

Customer message:

I paid for the bug spray but never got it in my bag.


### Truth

| message | stated | line | decision | reason | refund |
|---|---|---|---|---|---|
| I paid for the bug spray but never got it in my bag. | missing_item | None | reject | NOT_ON_RECEIPT | 0c |