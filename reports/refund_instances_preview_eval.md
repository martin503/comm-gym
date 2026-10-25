# Refund instance preview

## eval_unseen-L1-0000 (anchor eval_unseen-0000, out-of-window: False)

### System

You are a customer-support agent for a grocery chain. A customer writes in about a recent purchase. For each claim in their message, decide whether a refund is owed under the store's refund policy, and how much.

Refund policy, checked strictly in this order for each claim (the first rule that decides determines the reason code):

1. Window: a claim filed more than 14 days after the purchase day is rejected with OUTSIDE_WINDOW.
2. Item on receipt: if the claimed item does not appear on the receipt, reject with NOT_ON_RECEIPT.
3. Price match (the customer says they were overcharged): if the paid loyalty unit price (regular unit price minus loyalty discount) exceeds the reference price by more than $0.05 per unit, approve with PRICE_MATCH and refund the difference times the quantity. Otherwise reject with WITHIN_TOLERANCE.
4. Missed coupon (the customer says a coupon did not apply): if no live coupon on the customer's account covers that receipt line, reject with NOT_ELIGIBLE. If a coupon discount was already applied on that line, reject with ALREADY_APPLIED. Otherwise approve with MISSED_COUPON and refund the coupon's typical value.

Each claim is adjudicated exactly as stated: a claim phrased as a price complaint is judged under rule 3 only, and a claim phrased as a coupon complaint under rule 4 only. Adjudicate claims independently of each other.

Output your reasoning, then exactly one answer block:

<answer>{"claims": [{"line": "L07" | null, "decision": "approve" | "reject", "reason": "<CODE>", "refund": 0.42}, ...]}</answer>

The claims array lists one entry per claim in the message, in the order they appear. "line" is the receipt line the claim refers to, or null when the item is not on the receipt. "refund" is 0 for every rejection. Reason codes: OUTSIDE_WINDOW, NOT_ON_RECEIPT, PRICE_MATCH, WITHIN_TOLERANCE, MISSED_COUPON, NOT_ELIGIBLE, ALREADY_APPLIED.

### User

Purchase day: 677
Claim filed: day 679

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

I was billed extra for the banana.


### Truth

| message | stated | line | decision | reason | refund |
|---|---|---|---|---|---|
| I was billed extra for the banana | price | L16 | approve | PRICE_MATCH | 18c |

---

## eval_unseen-L1-0001 (anchor eval_unseen-0001, out-of-window: False)

### System

You are a customer-support agent for a grocery chain. A customer writes in about a recent purchase. For each claim in their message, decide whether a refund is owed under the store's refund policy, and how much.

Refund policy, checked strictly in this order for each claim (the first rule that decides determines the reason code):

1. Window: a claim filed more than 14 days after the purchase day is rejected with OUTSIDE_WINDOW.
2. Item on receipt: if the claimed item does not appear on the receipt, reject with NOT_ON_RECEIPT.
3. Price match (the customer says they were overcharged): if the paid loyalty unit price (regular unit price minus loyalty discount) exceeds the reference price by more than $0.05 per unit, approve with PRICE_MATCH and refund the difference times the quantity. Otherwise reject with WITHIN_TOLERANCE.
4. Missed coupon (the customer says a coupon did not apply): if no live coupon on the customer's account covers that receipt line, reject with NOT_ELIGIBLE. If a coupon discount was already applied on that line, reject with ALREADY_APPLIED. Otherwise approve with MISSED_COUPON and refund the coupon's typical value.

Each claim is adjudicated exactly as stated: a claim phrased as a price complaint is judged under rule 3 only, and a claim phrased as a coupon complaint under rule 4 only. Adjudicate claims independently of each other.

Output your reasoning, then exactly one answer block:

<answer>{"claims": [{"line": "L07" | null, "decision": "approve" | "reject", "reason": "<CODE>", "refund": 0.42}, ...]}</answer>

The claims array lists one entry per claim in the message, in the order they appear. "line" is the receipt line the claim refers to, or null when the item is not on the receipt. "refund" is 0 for every rejection. Reason codes: OUTSIDE_WINDOW, NOT_ON_RECEIPT, PRICE_MATCH, WITHIN_TOLERANCE, MISSED_COUPON, NOT_ELIGIBLE, ALREADY_APPLIED.

### User

Purchase day: 609
Claim filed: day 610

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

I already threw the packaging out, I paid for the soap but it was not there.


### Truth

| message | stated | line | decision | reason | refund |
|---|---|---|---|---|---|
| I already threw the packaging out, I paid for the soap but it was not there | missing_item | None | reject | NOT_ON_RECEIPT | 0c |

---

## eval_unseen-L1-0002 (anchor eval_unseen-0002, out-of-window: False)

### System

You are a customer-support agent for a grocery chain. A customer writes in about a recent purchase. For each claim in their message, decide whether a refund is owed under the store's refund policy, and how much.

Refund policy, checked strictly in this order for each claim (the first rule that decides determines the reason code):

1. Window: a claim filed more than 14 days after the purchase day is rejected with OUTSIDE_WINDOW.
2. Item on receipt: if the claimed item does not appear on the receipt, reject with NOT_ON_RECEIPT.
3. Price match (the customer says they were overcharged): if the paid loyalty unit price (regular unit price minus loyalty discount) exceeds the reference price by more than $0.05 per unit, approve with PRICE_MATCH and refund the difference times the quantity. Otherwise reject with WITHIN_TOLERANCE.
4. Missed coupon (the customer says a coupon did not apply): if no live coupon on the customer's account covers that receipt line, reject with NOT_ELIGIBLE. If a coupon discount was already applied on that line, reject with ALREADY_APPLIED. Otherwise approve with MISSED_COUPON and refund the coupon's typical value.

Each claim is adjudicated exactly as stated: a claim phrased as a price complaint is judged under rule 3 only, and a claim phrased as a coupon complaint under rule 4 only. Adjudicate claims independently of each other.

Output your reasoning, then exactly one answer block:

<answer>{"claims": [{"line": "L07" | null, "decision": "approve" | "reject", "reason": "<CODE>", "refund": 0.42}, ...]}</answer>

The claims array lists one entry per claim in the message, in the order they appear. "line" is the receipt line the claim refers to, or null when the item is not on the receipt. "refund" is 0 for every rejection. Reason codes: OUTSIDE_WINDOW, NOT_ON_RECEIPT, PRICE_MATCH, WITHIN_TOLERANCE, MISSED_COUPON, NOT_ELIGIBLE, ALREADY_APPLIED.

### User

Purchase day: 623
Claim filed: day 635

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

| coupon | typical value | covers lines |
| C01 | $1.00 | L01 |
| C02 | $0.35 | L09, L12, L13 |
| C03 | $1.00 | L06, L10 |

Customer message:

I never got the pork even though I was told it was included.


### Truth

| message | stated | line | decision | reason | refund |
|---|---|---|---|---|---|
| I never got the pork even though I was told it was included | missing_item | None | reject | NOT_ON_RECEIPT | 0c |