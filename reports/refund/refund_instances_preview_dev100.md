# Refund instance preview

## dev-L1-0000 (anchor dev-0000, out-of-window: False)

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

Purchase day: 399
Claim filed: day 411

Receipt:
| line | category | sub-category | brand tier | size | qty | regular unit | loyalty disc | coupon disc | paid | reference |
| L01 | BAKING NEEDS | BAKING CUPS | National | 50 CT | 1 | $0.69 | $0.00 | $0.00 | $0.69 | $0.69 |
| L02 | ISOTONIC DRINKS | ISOTONIC DRINKS POWDERED | National | 18.4 OZ | 2 | $5.09 | $0.60 | $0.00 | $4.49 | $4.49 |
| L03 | CONVENIENT BRKFST/WHLSM SNACKS | CEREAL BARS | National | 10.4 OZ | 1 | $3.39 | $0.00 | $0.00 | $3.39 | $3.39 |
| L04 | COFFEE | GROUND COFFEE | National | 33 OZ | 1 | $7.46 | $0.00 | $0.00 | $7.46 | $7.46 |
| L05 | CONVENIENT BRKFST/WHLSM SNACKS | FRUIT SNACKS | National | 6.7 OZ | 1 | $2.69 | $0.69 | $0.00 | $2.00 | $2.00 |
| L06 | BAKING MIXES | MUFFIN & CORN BREAD MIX | National | 7 OZ | 2 | $0.76 | $0.00 | $0.00 | $0.76 | $0.82 |
| L07 | BAKING MIXES | MUFFIN & CORN BREAD MIX | National | 7.9 OZ | 2 | $0.76 | $0.00 | $0.00 | $0.76 | $0.79 |
| L08 | APPLES | APPLES RED DELICIOUS (BULK&BAG | National | 3 LB | 1 | $2.69 | $0.00 | $0.00 | $2.69 | $2.69 |
| L09 | BATH TISSUES | TOILET TISSUE | National | 430.8 SQFT | 1 | $9.99 | $1.00 | $1.00 | $7.99 | $7.99 |
| L10 | CONVENIENT BRKFST/WHLSM SNACKS | FRUIT SNACKS | National | 9 OZ | 1 | $2.79 | $0.79 | $0.00 | $2.00 | $2.00 |
| L11 | PAPER TOWELS | PAPER TOWELS & HOLDERS | National | 141.1 SQFT | 1 | $4.49 | $0.00 | $0.00 | $4.49 | $4.49 |
| L12 | BROOMS AND MOPS | SCOURING PADS & CLOTH | National | 6 CT | 1 | $1.79 | $0.00 | $0.00 | $1.79 | $1.79 |
| L13 | BROOMS AND MOPS | TREATED CLEANING CLOTHS | National | XL/3PK | 2 | $1.79 | $0.00 | $0.00 | $1.79 | $1.79 |

Live coupons on the customer's account:

(none)

Customer message:

The trash bag never made it into my groceries.


### Truth

| message | stated | line | decision | reason | refund |
|---|---|---|---|---|---|
| the trash bag never made it into my groceries | missing_item | None | reject | NOT_ON_RECEIPT | 0c |

---

## dev-L1-0001 (anchor dev-0001, out-of-window: False)

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

Purchase day: 389
Claim filed: day 400

Receipt:
| line | category | sub-category | brand tier | size | qty | regular unit | loyalty disc | coupon disc | paid | reference |
| L01 | MILK BY-PRODUCTS | SOUR CREAMS | Private | 16 OZ | 1 | $1.16 | $0.00 | $0.00 | $1.16 | $1.16 |
| L02 | CONVENIENT BRKFST/WHLSM SNACKS | TREATS | National | 6.2 OZ | 1 | $2.59 | $0.92 | $0.00 | $1.67 | $1.67 |
| L03 | CANDY - PACKAGED | CANDY & BREATH MINTS (PKGD) (N | National |   | 1 | $2.59 | $0.00 | $0.00 | $2.59 | $2.59 |
| L04 | CANDY - PACKAGED | CANDY BAGS-CHOCOCLATE W/FLOUR | National | 13 OZ | 1 | $2.79 | $0.29 | $0.00 | $2.50 | $2.50 |
| L05 | FRZN POTATOES | FRZN HASHBROWN POTATOES | National | 2 LB | 1 | $2.69 | $1.02 | $0.00 | $1.67 | $1.67 |
| L06 | BAKED SWEET GOODS | SNACK CAKE - MULTI PACK | National | 8.75 OZ | 2 | $3.79 | $1.29 | $0.00 | $2.50 | $2.50 |
| L07 | DELI MEATS | MEAT:HAM BULK | National |   | 1 | $48.58 | $8.11 | $0.00 | $40.47 | $38.32 |
| L08 | ROLLS | ROLLS: DINNER | National | 12 OZ | 2 | $2.49 | $0.49 | $0.00 | $2.00 | $2.00 |
| L09 | MARGARINES | MARGARINE  STICK | National | 16 OZ | 2 | $1.96 | $0.69 | $0.50 | $0.77 | $1.00 |
| L10 | COLD CEREAL | ADULT CEREAL | Private | 18 OZ | 1 | $1.79 | $0.00 | $0.00 | $1.79 | $1.79 |
| L11 | LUNCHMEAT | MISCELLANEOUS | National | 8 OZ | 2 | $2.00 | $0.00 | $0.00 | $2.00 | $2.00 |
| L12 | ROLLS | ROLLS: DINNER | National | 12 OZ | 1 | $2.49 | $0.49 | $0.00 | $2.00 | $2.00 |
| L13 | SPICES & EXTRACTS | SPICES & SEASONINGS | National | 4 1/2 OZ | 1 | $3.49 | $0.00 | $0.00 | $3.49 | $3.49 |
| L14 | CARROTS | CARROTS MINI PEELED | Private | 1 LB | 3 | $1.69 | $0.44 | $0.00 | $1.25 | $1.25 |
| L15 | CHEESES | CHEESE: NATURAL BULK | National |   | 1 | $6.35 | $1.06 | $0.00 | $5.29 | $2.59 |
| L16 | RICE CAKES | RICE CAKES | National | 5.46 OZ | 1 | $2.69 | $0.00 | $0.00 | $2.69 | $2.69 |
| L17 | CANDY - CHECKLANE | MISCELLANEOUS CANDY (INCLUDING | National | 6 OZ | 1 | $1.99 | $0.99 | $0.00 | $1.00 | $1.00 |
| L18 | CRACKERS/MISC BKD FD | CHEESE CRACKERS (CHEEZ-ITS/GOL | National | 16 OZ | 2 | $2.68 | $0.80 | $0.00 | $1.88 | $1.88 |
| L19 | BEERS/ALES | BEERALEMALT LIQUORS | National | 12 OZ | 2 | $11.99 | $0.00 | $0.00 | $11.99 | $11.99 |
| L20 | CRACKERS/MISC BKD FD | BUTTER SPRAY CRACKER (RITZ/CLU | National | 16 OZ | 1 | $3.39 | $1.51 | $0.00 | $1.88 | $1.88 |
| L21 | CANDY - PACKAGED | SEASONAL CANDY BAGS-CHOCOLATE | National | 13 OZ | 1 | $2.79 | $0.29 | $0.00 | $2.50 | $2.50 |
| L22 | TROPICAL FRUIT | BANANAS | National | 40 LB | 1 | $0.45 | $0.00 | $0.00 | $0.45 | $1.08 |
| L23 | COFFEE | GROUND FLVR REG COFFEE | National | 12 OZ | 1 | $8.99 | $1.00 | $1.00 | $6.99 | $7.99 |
| L24 | CRACKERS/MISC BKD FD | SNACK CRACKERS | National | 9.5 OZ | 2 | $3.09 | $1.21 | $0.00 | $1.88 | $1.88 |
| L25 | FLUID MILK PRODUCTS | REFRIGERATED COFFEE CREAMERS | National | 32 OZ | 1 | $2.39 | $0.39 | $0.00 | $2.00 | $2.00 |
| L26 | DELI MEATS | MEAT: TURKEY BULK | National |   | 1 | $3.50 | $0.25 | $0.00 | $3.25 | $4.11 |
| L27 | FLUID MILK PRODUCTS | REFRIGERATED COFFEE CREAMERS | National | 32 OZ | 1 | $3.54 | $0.30 | $1.00 | $2.24 | $2.69 |
| L28 | BAKED BREAD/BUNS/ROLLS | MAINSTREAM WHEAT/MULTIGRAIN BR | National | 20 OZ | 1 | $2.00 | $0.50 | $0.00 | $1.50 | $1.50 |
| L29 | HAIR CARE ACCESSORIES | HAIR BARRETTES TAILERS | National | 2 CT | 1 | $4.99 | $1.25 | $0.00 | $3.74 | $3.74 |
| L30 | HAIR CARE ACCESSORIES | HAIR BARRETTES TAILERS | National | 2 CT | 1 | $3.99 | $1.00 | $0.00 | $2.99 | $2.99 |
| L31 | HAIR CARE ACCESSORIES | BOBBY PINS AND ACCESSORIES | National | 2CT/5.5CM | 1 | $3.99 | $1.00 | $0.00 | $2.99 | $2.99 |
| L32 | CRACKERS/MISC BKD FD | MULTI-PACK CRACKERS | National | 6.5 OZ | 2 | $2.19 | $0.40 | $0.00 | $1.79 | $1.79 |
| L33 | CRACKERS/MISC BKD FD | MULTI-PACK CRACKERS | National | 5.58 OZ | 1 | $2.19 | $0.40 | $0.00 | $1.79 | $1.79 |

Live coupons on the customer's account:

(none)

Customer message:

I was charged for the popsicle but never received it.


### Truth

| message | stated | line | decision | reason | refund |
|---|---|---|---|---|---|
| I was charged for the popsicle but never received it | missing_item | None | reject | NOT_ON_RECEIPT | 0c |

---

## dev-L1-0002 (anchor dev-0002, out-of-window: False)

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

Purchase day: 460
Claim filed: day 462

Receipt:
| line | category | sub-category | brand tier | size | qty | regular unit | loyalty disc | coupon disc | paid | reference |
| L01 | POTATOES | POTATOES RED (BULK&BAG) | Private | 5LB BAG | 1 | $3.49 | $0.00 | $0.00 | $3.49 | $3.49 |
| L02 | BAKED BREAD/BUNS/ROLLS | RYE BREADS | National | 16 OZ | 1 | $1.89 | $0.39 | $0.00 | $1.50 | $1.50 |
| L03 | VEGETABLES - ALL OTHERS | CUCUMBERS | National | 36 CT | 1 | $0.67 | $0.00 | $0.00 | $0.67 | $0.67 |
| L04 | MILK BY-PRODUCTS | AEROSOL TOPPINGS | National | 7 OZ | 1 | $3.04 | $0.59 | $0.90 | $1.55 | $2.00 |
| L05 | VEGETABLES - ALL OTHERS | ASPARAGUS | National | 11 CT | 1 | $2.07 | $0.00 | $0.00 | $2.07 | $2.87 |
| L06 | CHEESE | NATURAL CHEESE EXACT WT SLICES | Private | 6 OZ | 1 | $1.99 | $0.74 | $0.00 | $1.25 | $1.25 |
| L07 | VEGETABLES - SHELF STABLE | TOMATO PASTE | Private | 6 OZ | 1 | $0.40 | $0.00 | $0.00 | $0.40 | $0.40 |
| L08 | BAG SNACKS | PRETZELS | National | 16 OZ | 1 | $2.50 | $0.00 | $0.00 | $2.50 | $2.50 |
| L09 | BAKING MIXES | BISCUIT FLOUR & MIXES | National | 60 OZ | 1 | $4.49 | $0.00 | $0.00 | $4.49 | $4.49 |
| L10 | BERRIES | STRAWBERRIES | National | 16 OZ | 1 | $2.99 | $0.00 | $0.00 | $2.99 | $2.99 |
| L11 | YOGURT | YOGURT MULTI-PACKS | National | 4 PK/7 OZ | 1 | $3.59 | $0.80 | $0.00 | $2.79 | $2.79 |

Live coupons on the customer's account:

| coupon | typical value | covers lines |
| C01 | $1.00 | L01, L10 |
| C02 | $1.00 | L04, L11 |

Customer message:

My coupon for the potatoes was on my account but nothing came off.


### Truth

| message | stated | line | decision | reason | refund |
|---|---|---|---|---|---|
| my coupon for the potatoes was on my account but nothing came off | coupon | L01 | approve | MISSED_COUPON | 100c |