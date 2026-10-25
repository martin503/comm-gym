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

---

## dev-L1-0003 (anchor dev-0003, out-of-window: False)

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

Purchase day: 240
Claim filed: day 249

Receipt:
| line | category | sub-category | brand tier | size | qty | regular unit | loyalty disc | coupon disc | paid | reference |
| L01 | CHEESE | CREAM CHEESE | National | 8 OZ | 2 | $1.99 | $0.99 | $0.00 | $1.00 | $1.00 |
| L02 | COLD CEREAL | ALL FAMILY CEREAL | National | 14 OZ | 1 | $3.99 | $1.49 | $0.00 | $2.50 | $2.50 |
| L03 | CHEESE | NATURAL CHEESE EXACT WT CHUNKS | National | 6 OZ | 1 | $2.69 | $1.19 | $0.00 | $1.50 | $1.50 |
| L04 | HAIR CARE PRODUCTS | WOMENS  HAIR SPRAYS | National |   | 1 | $3.39 | $1.39 | $0.00 | $2.00 | $2.00 |
| L05 | HAIR CARE PRODUCTS | SHAMPOO | National | 13 OZ | 1 | $3.89 | $1.39 | $1.00 | $1.50 | $2.50 |
| L06 | SUGARS/SWEETNERS | SUGAR | Private | 32 OZ | 1 | $1.49 | $0.20 | $0.00 | $1.29 | $1.29 |
| L07 | CHEESES | CHEESE:SPECIALTY BULK | National |   | 1 | $3.16 | $0.00 | $0.00 | $3.16 | $3.16 |
| L08 | EGGS | EGGS - LARGE | Private | 18 CT | 1 | $1.42 | $0.00 | $0.00 | $1.42 | $1.42 |
| L09 | SPICES & EXTRACTS | SPICES & SEASONINGS | Private | 1.72 OZ | 1 | $4.49 | $1.48 | $0.00 | $3.01 | $3.01 |
| L10 | CRACKERS/MISC BKD FD | SNACK CRACKERS | National | 9 OZ | 2 | $3.49 | $1.11 | $0.50 | $1.88 | $1.88 |
| L11 | BABY FOODS | BABY JUICES | National | 6 OZ | 1 | $2.30 | $0.00 | $1.00 | $1.30 | $1.55 |
| L12 | TURKEY | WHOLE - HENS (15 LBS & UNDER F | National |   | 1 | $27.61 | $13.00 | $0.00 | $14.61 | $16.26 |
| L13 | FROZEN PIE/DESSERTS | FRZN PIE SHELLS PASTRY SHELL | National | 16 OZ | 1 | $3.29 | $0.79 | $0.00 | $2.50 | $2.50 |
| L14 | FRZN VEGETABLE/VEG DSH | FRZN BAGGED VEGETABLES - PLAIN | Private | 16 OZ | 2 | $1.19 | $0.19 | $0.00 | $1.00 | $1.00 |
| L15 | FROZEN MEAT | FRZN BREADED PREPARED CHICK | National | 12.25 OZ | 1 | $3.29 | $0.30 | $0.00 | $2.99 | $2.99 |
| L16 | SOAP - LIQUID & BAR | BODY WASH | National | 12 OZ | 1 | $2.29 | $0.62 | $0.00 | $1.67 | $1.67 |
| L17 | HAIR CARE PRODUCTS | SHAMPOO | National | 15 OZ | 2 | $4.59 | $1.59 | $1.00 | $2.00 | $3.00 |
| L18 | HAIR CARE PRODUCTS | HAIR CONDITIONERS AND RINSES | National | 13 OZ | 1 | $3.39 | $1.39 | $0.00 | $2.00 | $2.00 |
| L19 | SOUP | BROTH | National | 14.0 OZ | 2 | $1.12 | $0.49 | $0.25 | $0.38 | $0.50 |
| L20 | DISPOSIBLE FOILWARE | DISPOSABLE FOILWARE | National |   | 1 | $2.99 | $1.00 | $0.00 | $1.99 | $1.99 |
| L21 | DRY SAUCES/GRAVY | GRAVY CAN/GLASS | National | 14.5 OZ | 2 | $1.64 | $0.64 | $0.50 | $0.50 | $0.75 |
| L22 | COLD CEREAL | ADULT CEREAL | National | 12.8 OZ | 1 | $3.99 | $1.49 | $0.00 | $2.50 | $2.50 |
| L23 | ROLLS | ROLLS: BAGELS | National | 4 OZ | 1 | $0.50 | $0.00 | $0.00 | $0.50 | $0.50 |
| L24 | BUTTER | BUTTER | Private | 1 LB | 2 | $3.59 | $1.09 | $0.00 | $2.50 | $2.50 |
| L25 | FLUID MILK PRODUCTS | FLUID MILK WHITE ONLY | Private |   | 1 | $1.99 | $0.99 | $0.00 | $1.00 | $1.00 |
| L26 | CHEESES | CHEESE:SPECIALTY PREPACK | National | 8 OZ | 1 | $5.99 | $0.00 | $0.00 | $5.99 | $5.99 |
| L27 | CHEESES | CHEESE:SPECIALTY PREPACK | National | 5 OZ | 1 | $3.99 | $0.00 | $0.00 | $3.99 | $3.99 |
| L28 | BABY FOODS | BABY FOOD JUNIOR ALL BRANDS | National | 1 OZ | 1 | $3.99 | $0.00 | $1.00 | $2.99 | $3.99 |
| L29 | SHORTENING/OIL | OLIVE OIL | National | 17 OZ | 1 | $6.49 | $0.90 | $1.00 | $4.59 | $5.59 |
| L30 | FLOUR & MEALS | FLOUR: WHITE & SELF RISING | National | 5 LB | 2 | $2.69 | $1.69 | $0.00 | $1.00 | $1.00 |
| L31 | COLD CEREAL | ALL FAMILY CEREAL | National | 16.9 OZ | 1 | $6.09 | $0.00 | $2.00 | $4.09 | $6.09 |
| L32 | COLD CEREAL | KIDS CEREAL | National | 13 OZ | 1 | $3.09 | $0.00 | $0.00 | $3.09 | $3.09 |

Live coupons on the customer's account:

(none)

Customer message:

I did not receive the popsicle I ordered.


### Truth

| message | stated | line | decision | reason | refund |
|---|---|---|---|---|---|
| I did not receive the popsicle I ordered | missing_item | None | reject | NOT_ON_RECEIPT | 0c |

---

## dev-L1-0004 (anchor dev-0004, out-of-window: False)

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

Purchase day: 459
Claim filed: day 463

Receipt:
| line | category | sub-category | brand tier | size | qty | regular unit | loyalty disc | coupon disc | paid | reference |
| L01 | BAKED BREAD/BUNS/ROLLS | HOT DOG BUNS | Private | 16 OZ | 1 | $1.39 | $0.51 | $0.00 | $0.88 | $0.88 |
| L02 | CAT LITTER | LITTER ACCESSORIES | National | 5 CT | 2 | $2.64 | $0.30 | $1.00 | $1.34 | $2.07 |
| L03 | CAT LITTER | CONVENTIONAL LITTER | National | 20 LB | 1 | $4.69 | $0.70 | $0.00 | $3.99 | $3.99 |
| L04 | BAKED BREAD/BUNS/ROLLS | HOT DOG BUNS | Private | 11 OZ | 1 | $1.29 | $0.41 | $0.00 | $0.88 | $0.88 |
| L05 | CONDIMENTS/SAUCES | CATSUP | National | 32 OZ | 2 | $2.69 | $1.02 | $0.00 | $1.67 | $1.67 |
| L06 | BAKED BREAD/BUNS/ROLLS | HAMBURGER BUNS | Private | 21 OZ | 1 | $1.49 | $0.10 | $0.00 | $1.39 | $1.39 |
| L07 | HOT DOGS | PREMIUM - MEAT | National | 1LB | 2 | $3.29 | $1.64 | $0.00 | $1.65 | $1.65 |
| L08 | CHARCOAL AND LIGHTER FLUID | CHARCOAL | Private | 9 LBS | 1 | $4.19 | $0.20 | $0.00 | $3.99 | $3.99 |

Live coupons on the customer's account:

| coupon | typical value | covers lines |
| C01 | $0.55 | L07 |

Customer message:

The coupon savings for the hot dog are missing from my total.


### Truth

| message | stated | line | decision | reason | refund |
|---|---|---|---|---|---|
| the coupon savings for the hot dog are missing from my total | coupon | L07 | approve | MISSED_COUPON | 55c |

---

## dev-L1-0005 (anchor dev-0005, out-of-window: False)

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
Claim filed: day 465

Receipt:
| line | category | sub-category | brand tier | size | qty | regular unit | loyalty disc | coupon disc | paid | reference |
| L01 | CITRUS | LEMONS | National |   | 5 | $0.59 | $0.00 | $0.00 | $0.59 | $0.59 |
| L02 | HERBS | GARLIC JAR | National | 4.5 OZ | 1 | $1.49 | $0.20 | $0.00 | $1.29 | $1.29 |
| L03 | PAPER TOWELS | PAPER TOWELS & HOLDERS | National | 70.5 SQ FT | 1 | $2.54 | $0.00 | $0.50 | $2.04 | $2.29 |
| L04 | COUPON/MISC ITEMS | BULK CANDY | National |   | 2 | $6.02 | $0.00 | $0.00 | $6.02 | $4.11 |
| L05 | IMPORTED WINE | AUSTRALIAN/NZ WINES | National | 750 ML | 1 | $10.99 | $0.00 | $0.00 | $10.99 | $10.99 |
| L06 | SOFT DRINKS | MIXERS(TONIC WTR/GNGR ALE)FLAV | National | 1 LTR | 1 | $1.39 | $0.00 | $0.00 | $1.39 | $1.39 |
| L07 | REFRIGERATED | YOGURT | National | 6 OZ | 1 | $0.99 | $0.00 | $0.00 | $0.99 | $0.99 |
| L08 | HERBS | GARLIC WHOLE CLOVES | National | 10LB | 1 | $0.34 | $0.00 | $0.00 | $0.34 | $0.35 |
| L09 | CRACKERS/MISC BKD FD | BUTTER SPRAY CRACKER (RITZ/CLU | National | 16 OZ | 1 | $3.39 | $0.00 | $0.00 | $3.39 | $3.39 |
| L10 | REFRIGERATED | FLUID MILK | National | 64 OZ | 1 | $3.89 | $0.00 | $0.00 | $3.89 | $3.89 |
| L11 | REFRIGERATED | YOGURT | National | 6 OZ | 1 | $0.99 | $0.00 | $0.00 | $0.99 | $0.99 |
| L12 | IMPORTED WINE | AUSTRALIAN/NZ WINES | National | 750 ML | 1 | $6.99 | $0.00 | $0.00 | $6.99 | $6.99 |
| L13 | IMPORTED WINE | AUSTRALIAN/NZ WINES | National | 750 ML | 1 | $6.99 | $0.00 | $0.00 | $6.99 | $6.99 |
| L14 | DISHWASH DETERGENTS | AUTO DISH DETERGENT - GEL | National | 75 OZ | 1 | $3.49 | $0.00 | $0.00 | $3.49 | $3.49 |
| L15 | FRZN VEGETABLE/VEG DSH | FRZN BOXED VEGETABLES- VALUE A | Private | 10 OZ | 1 | $1.49 | $0.24 | $0.00 | $1.25 | $1.25 |
| L16 | FRZN VEGETABLE/VEG DSH | FRZN BOXED VEGETABLES- VALUE A | Private | 10 OZ | 1 | $1.49 | $0.24 | $0.00 | $1.25 | $1.25 |
| L17 | DOMESTIC WINE | POPULAR 750ML WINES | National | 750 ML | 1 | $5.99 | $0.00 | $0.00 | $5.99 | $5.99 |
| L18 | WATER - CARBONATED/FLVRD DRINK | CARBONATED WATER - FLVRD SWEET | National | 101.4 OZ | 1 | $2.99 | $0.20 | $0.00 | $2.79 | $2.79 |
| L19 | EGGS | EGGS - LARGE | National | 12 CT | 1 | $2.79 | $0.00 | $1.00 | $1.79 | $2.79 |
| L20 | MAGAZINE | TV/MOVIE-MAGAZINE | National |   | 1 | $3.49 | $0.00 | $0.00 | $3.49 | $3.49 |
| L21 | FRZN VEGETABLE/VEG DSH | FRZN BAGGED VEGETABLES- VALUE | National | 10 OZ | 3 | $2.99 | $0.49 | $0.00 | $2.50 | $2.50 |
| L22 | SNKS/CKYS/CRKR/CNDY | CANDY/CHOCOLATE | National | 3.90 OZ | 1 | $5.84 | $0.00 | $1.00 | $4.84 | $5.84 |
| L23 | SNKS/CKYS/CRKR/CNDY | CANDY/CHOCOLATE | National | 3.90 OZ | 1 | $5.84 | $0.00 | $1.00 | $4.84 | $5.84 |

Live coupons on the customer's account:

| coupon | typical value | covers lines |
| C01 | $1.00 | L15, L16, L21 |
| C02 | $1.00 | L02, L08 |
| C03 | $1.00 | L19 |

Customer message:

The name-brand frozen vegetables coupon did not deduct anything.


### Truth

| message | stated | line | decision | reason | refund |
|---|---|---|---|---|---|
| the name-brand frozen vegetables coupon did not deduct anything | coupon | L21 | approve | MISSED_COUPON | 100c |

---

## dev-L1-0006 (anchor dev-0006, out-of-window: False)

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

Purchase day: 463
Claim filed: day 471

Receipt:
| line | category | sub-category | brand tier | size | qty | regular unit | loyalty disc | coupon disc | paid | reference |
| L01 | BAKED BREAD/BUNS/ROLLS | HOT DOG BUNS | National | 12 CT | 1 | $1.79 | $0.70 | $0.00 | $1.09 | $1.09 |
| L02 | CHEESE | LOAF CHEESE | National | L     2 LB | 1 | $4.54 | $0.00 | $1.00 | $3.54 | $3.99 |
| L03 | HOT DOGS | PREMIUM - MEAT | National | 1 LB | 8 | $3.29 | $2.04 | $0.00 | $1.25 | $1.25 |
| L04 | CANNED JUICES | ASEPTIC PACK JUICE AND DRINKS | National | 200 ML | 4 | $1.62 | $0.00 | $0.00 | $1.62 | $1.62 |
| L05 | COOKIES/CONES | SANDWICH COOKIES | National | 18 OZ | 2 | $2.68 | $0.00 | $0.00 | $2.68 | $2.68 |
| L06 | BACON | PREMIUM | Private | 16OZ | 2 | $3.79 | $1.79 | $0.00 | $2.00 | $2.00 |
| L07 | BEEF | LEAN | National |   | 5 | $4.42 | $2.42 | $0.00 | $2.00 | $2.12 |
| L08 | ISOTONIC DRINKS | ISOTONIC DRINKS SINGLE SERVE | National | 32 OZ | 2 | $1.00 | $0.12 | $0.00 | $0.88 | $0.88 |
| L09 | DINNER SAUSAGE | RED | National | 1 LB | 5 | $3.99 | $2.74 | $0.00 | $1.25 | $1.25 |
| L10 | BAG SNACKS | TORTILLA/NACHO CHIPS | National | 12.5 OZ | 2 | $3.75 | $1.08 | $1.00 | $1.67 | $1.67 |
| L11 | SOFT DRINKS | SOFT DRINKS 12/18&15PK CAN CAR | National | 12 OZ | 5 | $5.19 | $2.19 | $0.50 | $2.50 | $2.50 |
| L12 | ISOTONIC DRINKS | ISOTONIC DRINKS SINGLE SERVE | National | 32 OZ | 2 | $1.00 | $0.12 | $0.00 | $0.88 | $0.88 |
| L13 | DINNER SAUSAGE | SMOKED/COOKED | National | 16 OZ | 3 | $3.99 | $2.74 | $0.00 | $1.25 | $1.25 |
| L14 | BAG SNACKS | POTATO CHIPS | National | 11.5 OZ | 1 | $2.00 | $0.33 | $0.00 | $1.67 | $1.67 |
| L15 | HOT DOGS | KOSHER/SPECIALTY | National | 14 OZ | 2 | $2.99 | $0.99 | $0.00 | $2.00 | $2.00 |
| L16 | LUNCHMEAT | POULTRY | Private | 10 OZ | 2 | $2.50 | $1.25 | $0.00 | $1.25 | $1.88 |
| L17 | BEEF | PATTIES | National |   | 1 | $5.50 | $2.65 | $0.00 | $2.85 | $2.39 |
| L18 | BAG SNACKS | DIPS (NON-REFRIGERATED) | National | 15.50 OZ | 1 | $3.19 | $0.00 | $0.00 | $3.19 | $3.19 |
| L19 | ISOTONIC DRINKS | ISOTONIC DRINKS SINGLE SERVE | National | 32 OZ | 4 | $1.00 | $0.12 | $0.00 | $0.88 | $0.88 |
| L20 | ISOTONIC DRINKS | ISOTONIC DRINKS SINGLE SERVE | National | 32 OZ | 2 | $1.00 | $0.12 | $0.00 | $0.88 | $0.88 |

Live coupons on the customer's account:

(none)

Customer message:

My coupon for the juice was on my account but nothing came off.


### Truth

| message | stated | line | decision | reason | refund |
|---|---|---|---|---|---|
| my coupon for the juice was on my account but nothing came off | coupon | L04 | reject | NOT_ELIGIBLE | 0c |

---

## dev-L1-0007 (anchor dev-0007, out-of-window: False)

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

Purchase day: 259
Claim filed: day 269

Receipt:
| line | category | sub-category | brand tier | size | qty | regular unit | loyalty disc | coupon disc | paid | reference |
| L01 | ONIONS | ONIONS OTHER | National | 48 CT | 1 | $0.50 | $0.00 | $0.00 | $0.50 | $0.50 |
| L02 | EGGS | EGGS - LARGE | Private | 1 DZ | 1 | $1.09 | $0.00 | $0.00 | $1.09 | $1.09 |
| L03 | REFRGRATD DOUGH PRODUCTS | REFRIGERATED SPECILATY ROLLS | Private | 12.4 OZ | 2 | $1.99 | $0.99 | $0.00 | $1.00 | $1.00 |
| L04 | PNT BTR/JELLY/JAMS | PEANUT BUTTER | National | 13 OZ | 1 | $3.09 | $0.50 | $0.00 | $2.59 | $2.59 |
| L05 | APPLES | APPLES GRANNY SMITH (BULK&BAG) | National | 3 LB | 1 | $2.99 | $0.00 | $0.00 | $2.99 | $2.99 |
| L06 | GRAPES | GRAPES WHITE | National | 18 LB | 1 | $4.81 | $0.00 | $0.00 | $4.81 | $3.74 |
| L07 | LUNCHMEAT | HAM - STEAKS/SLICES/CUBES | National | 12 OZ | 1 | $3.79 | $0.00 | $0.00 | $3.79 | $3.79 |
| L08 | VEGETABLES - SHELF STABLE | CORN | National | 14.75 OZ | 1 | $1.09 | $0.00 | $0.00 | $1.09 | $1.09 |
| L09 | CONVENIENT BRKFST/WHLSM SNACKS | CEREAL BARS | National | 6CT/4.65OZ | 1 | $2.89 | $0.00 | $0.00 | $2.89 | $2.89 |
| L10 | CONDIMENTS/SAUCES | STEAK & WORCHESTER SAUCE | Private | 15 OZ | 1 | $1.39 | $0.10 | $0.00 | $1.29 | $1.29 |
| L11 | HOT CEREAL | STANDARD OATMEAL | National | 42 OZ | 1 | $3.99 | $0.00 | $0.00 | $3.99 | $3.99 |
| L12 | CHEESES | CHEESE:SPECIALTY PREPACK | National | 7 OZ | 1 | $2.99 | $0.00 | $0.00 | $2.99 | $2.99 |
| L13 | REFRIGERATED | FLUID MILK | Private | 64 OZ | 1 | $3.29 | $0.79 | $0.00 | $2.50 | $2.50 |
| L14 | CHEESE | CREAM CHEESE | Private | 8 OZ | 1 | $1.69 | $0.19 | $0.00 | $1.50 | $1.50 |
| L15 | CANDY - PACKAGED | CANDY BAGS-CHOCOCLATE | National | 5.05 OZ | 1 | $0.99 | $0.00 | $0.00 | $0.99 | $0.99 |
| L16 | COLD CEREAL | ALL FAMILY CEREAL | National | 14 OZ | 1 | $3.99 | $1.49 | $0.00 | $2.50 | $2.50 |
| L17 | VEGETABLES - SHELF STABLE | CORN | National | 15.25 OZ | 1 | $1.09 | $0.00 | $0.00 | $1.09 | $1.09 |
| L18 | COOKIES/CONES | PREMIUM COOKIES (EX: PEPPERIDG | National | 8.64 OZ | 2 | $3.49 | $0.00 | $0.50 | $2.99 | $3.49 |
| L19 | BREAD | BREAD:SAVORY/SPECIALTY | National |   | 1 | $2.99 | $0.00 | $0.00 | $2.99 | $2.99 |
| L20 | APPLES | APPLES GALA (BULK&BAG) | National | 3 LB | 1 | $2.99 | $0.00 | $0.00 | $2.99 | $2.99 |
| L21 | COOKIES/CONES | SPECIALTY COOKIES | National | 16 OZ | 1 | $3.79 | $0.00 | $0.00 | $3.79 | $3.79 |
| L22 | DRIED FRUIT | RAISINS | National | 15 OZ | 1 | $2.29 | $0.00 | $0.00 | $2.29 | $2.29 |
| L23 | CANDY - PACKAGED | CANDY BAGS-NON CHOCOLATE | National | 9 OZ | 1 | $1.49 | $0.00 | $0.00 | $1.49 | $1.49 |
| L24 | SPICES & EXTRACTS | SPICES & SEASONINGS | Private | 8 OZ | 1 | $1.79 | $0.59 | $0.00 | $1.20 | $1.20 |
| L25 | SOUP | CONDENSED SOUP | Private | 10.75 OZ | 1 | $0.99 | $0.39 | $0.00 | $0.60 | $0.60 |
| L26 | CANDY - PACKAGED | MISCELLANEOUS CANDY (INCLUDING | National |   | 2 | $0.59 | $0.00 | $0.00 | $0.59 | $0.59 |
| L27 | BAKED BREAD/BUNS/ROLLS | PREMIUM BREAD | Private | 24 OZ | 1 | $1.89 | $0.10 | $0.00 | $1.79 | $1.79 |
| L28 | COLD CEREAL | ALL FAMILY CEREAL | National | 16 OZ | 1 | $3.99 | $0.00 | $0.00 | $3.99 | $3.99 |
| L29 | TROPICAL FRUIT | BANANAS | National | 40 LB | 1 | $0.84 | $0.34 | $0.00 | $0.50 | $0.61 |
| L30 | COLD CEREAL | ADULT CEREAL | National | 14 OZ | 1 | $3.99 | $0.00 | $0.00 | $3.99 | $3.99 |
| L31 | DRIED FRUIT | DRIED FRUIT - OTHER | National | 6 OZ | 1 | $2.49 | $0.00 | $0.00 | $2.49 | $2.49 |
| L32 | CANDY - PACKAGED | CANDY BAGS-NON CHOCOLATE | Private | 20 OZ | 1 | $1.50 | $0.00 | $0.00 | $1.50 | $1.50 |
| L33 | DRY NOODLES/PASTA | MACARONI DRY | National | 12 OZ | 1 | $1.99 | $0.49 | $0.00 | $1.50 | $1.50 |
| L34 | SPICES & EXTRACTS | SPICES & SEASONINGS | Private | 1.6 OZ | 1 | $3.99 | $1.32 | $0.00 | $2.67 | $2.67 |
| L35 | BAG SNACKS | PRETZELS | National | 16 OZ | 1 | $2.49 | $0.49 | $0.00 | $2.00 | $2.00 |
| L36 | REFRGRATD DOUGH PRODUCTS | MISC REFRIG DOUGH PRODUCTS | National | 15 OZ | 1 | $2.69 | $0.19 | $0.00 | $2.50 | $2.50 |
| L37 | BREAKFAST SAUSAGE/SANDWICHES | ROLLS - PORK | National | 16 OZ | 1 | $3.99 | $0.49 | $0.00 | $3.50 | $3.50 |
| L38 | CANDY - PACKAGED | CANDY BAGS-NON CHOCOLATE | National | 16 OZ | 1 | $2.50 | $0.00 | $0.00 | $2.50 | $2.50 |
| L39 | SOFT DRINKS | SOFT DRINKS 12/18&15PK CAN CAR | National | 144 OUNCE | 1 | $4.69 | $1.35 | $0.00 | $3.34 | $3.34 |
| L40 | REFRGRATD DOUGH PRODUCTS | REFRIGERATED COOKIES-SEASONAL | National | 16 OZ | 1 | $2.99 | $0.99 | $0.00 | $2.00 | $2.00 |

Live coupons on the customer's account:

(none)

Customer message:

I was overcharged for the grapes.


### Truth

| message | stated | line | decision | reason | refund |
|---|---|---|---|---|---|
| I was overcharged for the grapes | price | L06 | approve | PRICE_MATCH | 107c |

---

## dev-L1-0008 (anchor dev-0008, out-of-window: True)

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

Purchase day: 227
Claim filed: day 258

Receipt:
| line | category | sub-category | brand tier | size | qty | regular unit | loyalty disc | coupon disc | paid | reference |
| L01 | REFRGRATD JUICES/DRNKS | DAIRY CASE 100% PURE JUICE - O | National | 64 OZ | 2 | $3.59 | $1.82 | $0.00 | $1.77 | $1.77 |
| L02 | PAPER HOUSEWARES | DESIGNER PAPER: MEDIUM WEIGHT | Private | 48CT | 2 | $1.99 | $0.00 | $0.00 | $1.99 | $1.99 |
| L03 | AIR CARE | AIR CARE - CONTINUOUS ACTION | National | 2 CT | 1 | $6.49 | $1.00 | $1.50 | $3.99 | $5.49 |
| L04 | HOUSEHOLD CLEANG NEEDS | GLASS CLEANERS | Private | 32 OZ | 1 | $1.99 | $0.52 | $0.00 | $1.47 | $1.47 |
| L05 | FRZN ICE | ICE - CRUSHED/CUBED | National | 7 LB | 1 | $1.49 | $0.00 | $0.00 | $1.49 | $1.49 |
| L06 | BABY HBC | BABY LOTIONS & OILS | Private |   | 1 | $2.79 | $0.00 | $0.00 | $2.79 | $2.79 |
| L07 | DISHWASH DETERGENTS | LIQUID DISH DETERGENT | Private | 28 OZ | 1 | $1.79 | $0.12 | $0.00 | $1.67 | $1.67 |
| L08 | HOUSEHOLD CLEANG NEEDS | TOOLS - BATHROOM & TOILET | National | 6 CT | 1 | $3.19 | $0.20 | $0.00 | $2.99 | $2.99 |
| L09 | AIR CARE | AIR CARE - CONTINUOUS ACTION | National | 1 CT | 2 | $6.49 | $0.50 | $1.50 | $4.49 | $5.99 |

Live coupons on the customer's account:

| coupon | typical value | covers lines |
| C01 | $1.00 | L01 |

Customer message:

That juice was supposed to be on sale but I paid full price.


### Truth

| message | stated | line | decision | reason | refund |
|---|---|---|---|---|---|
| that juice was supposed to be on sale but I paid full price | price | L01 | reject | OUTSIDE_WINDOW | 0c |

---

## dev-L1-0009 (anchor dev-0009, out-of-window: True)

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

Purchase day: 237
Claim filed: day 254

Receipt:
| line | category | sub-category | brand tier | size | qty | regular unit | loyalty disc | coupon disc | paid | reference |
| L01 | SOFT DRINKS | SFT DRNK 2 LITER BTL CARB INCL | Private | 2 LTR | 1 | $0.59 | $0.00 | $0.00 | $0.59 | $0.59 |
| L02 | CRACKERS/MISC BKD FD | CHEESE CRACKERS (CHEEZ-ITS/GOL | National | 13.5 OZ | 1 | $2.68 | $0.68 | $0.00 | $2.00 | $2.00 |
| L03 | COOKIES/CONES | SANDWICH COOKIES | National | 5.29 OZ | 1 | $2.99 | $0.80 | $0.00 | $2.19 | $2.19 |
| L04 | TEAS | TEA BAGS HERBAL & FLAVORED | National | 20 CT | 1 | $2.29 | $0.62 | $0.00 | $1.67 | $1.67 |
| L05 | COLD AND FLU | COUGH SYRP/LOZNG-DRP/XPCTRNT | National |   | 1 | $1.99 | $0.49 | $0.00 | $1.50 | $1.50 |
| L06 | AIR CARE | AIR CARE - CONTINUOUS ACTION | National |   | 1 | $8.99 | $1.00 | $2.00 | $5.99 | $7.99 |

Live coupons on the customer's account:

(none)

Customer message:

The coupon savings for the cookie are missing from my total.


### Truth

| message | stated | line | decision | reason | refund |
|---|---|---|---|---|---|
| the coupon savings for the cookie are missing from my total | coupon | L03 | reject | OUTSIDE_WINDOW | 0c |
