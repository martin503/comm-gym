# Refund instance preview

## train-L1-0000 (anchor train-0000, out-of-window: False)

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

Purchase day: 397
Claim filed: day 406

Receipt:
| line | category | sub-category | brand tier | size | qty | regular unit | loyalty disc | coupon disc | paid | reference |
| L01 | FOOT CARE PRODUCTS | FOOT CARE - SHOE INSOLE/PADS | Private |   | 2 | $1.79 | $0.00 | $0.00 | $1.79 | $1.79 |
| L02 | VEGETABLES SALAD | VARIETY LETTUCE | National |   | 1 | $0.99 | $0.00 | $0.00 | $0.99 | $0.99 |
| L03 | BAKED BREAD/BUNS/ROLLS | HAMBURGER BUNS | Private | 12 OZ | 1 | $1.29 | $0.41 | $0.00 | $0.88 | $0.88 |
| L04 | TOMATOES | TOMATOES HOTHOUSE ON THE VINE | National | 13 LB | 1 | $2.93 | $0.00 | $0.00 | $2.93 | $2.63 |
| L05 | FROZEN PIE/DESSERTS | FRZN PASTRY&COOKIES | National | 18 OZ | 1 | $2.99 | $0.00 | $0.00 | $2.99 | $2.99 |
| L06 | FD WRAPS/BAGS/TRSH BG | SANDWICH BAGS | National | 100 CT | 1 | $3.94 | $0.60 | $1.00 | $2.34 | $2.79 |
| L07 | SOFT DRINKS | SOFT DRINKS 12/18&15PK CAN CAR | Private | 12 PK | 1 | $2.00 | $0.00 | $0.00 | $2.00 | $2.00 |
| L08 | CHEESE | GRATED CHEESE | Private | 8 OZ | 1 | $2.38 | $0.38 | $0.00 | $2.00 | $2.00 |
| L09 | FRZN MEAT/MEAT DINNERS | FRZN SS PREMIUM ENTREES/DNRS/T | National | 13.35 OZ | 1 | $3.79 | $1.29 | $0.00 | $2.50 | $2.50 |
| L10 | CHICKEN | CHICKEN BREAST BONELESS | National |   | 1 | $11.40 | $6.93 | $0.00 | $4.47 | $3.28 |
| L11 | FRZN VEGETABLE/VEG DSH | FRZN BAGGED VEGETABLES- VALUE | National | 24 OZ | 1 | $3.39 | $0.39 | $0.00 | $3.00 | $3.00 |
| L12 | BAKED BREAD/BUNS/ROLLS | MAINSTREAM WHITE BREAD | National | 20 OZ | 1 | $1.99 | $0.00 | $0.00 | $1.99 | $1.99 |
| L13 | ICE CREAM/MILK/SHERBTS | TRADITIONAL | Private | 56 OZ | 1 | $1.99 | $0.00 | $0.00 | $1.99 | $1.99 |
| L14 | FRZN MEAT/MEAT DINNERS | FRZN SS PREMIUM ENTREES/DNRS/T | National | 13.35 OZ | 1 | $3.79 | $1.29 | $0.00 | $2.50 | $2.50 |
| L15 | FLUID MILK PRODUCTS | FLUID MILK WHITE ONLY | Private | 1 GA | 1 | $2.69 | $1.02 | $0.00 | $1.67 | $1.67 |
| L16 | BAG SNACKS | BAGGED POPPED POPCORN | National | 10 OZ | 1 | $2.29 | $0.00 | $0.00 | $2.29 | $2.29 |
| L17 | HOUSEHOLD CLEANG NEEDS | FLOOR - DILUTABLES | National | 40 OZ | 1 | $2.99 | $0.00 | $0.00 | $2.99 | $2.99 |
| L18 | DELI MEATS | MEAT: LUNCHMEAT BULK | National |   | 1 | $3.14 | $0.00 | $0.00 | $3.14 | $2.82 |
| L19 | MARGARINES | MARGARINE: TUBS AND BOWLS | National | 15 OZ | 1 | $2.69 | $0.29 | $0.80 | $1.60 | $2.00 |
| L20 | DELI MEATS | MEAT: TURKEY BULK | National |   | 1 | $2.35 | $0.00 | $0.00 | $2.35 | $2.91 |
| L21 | GRAPES | GRAPES RED | National | 18 LB | 1 | $4.00 | $2.01 | $0.00 | $1.99 | $2.05 |
| L22 | MOLASSES/SYRUP/PANCAKE MIXS | PANCAKE MIXES | National | 5 OZ | 1 | $1.09 | $0.20 | $0.00 | $0.89 | $0.89 |
| L23 | HISPANIC | MEXICAN DINNERS AND FOODS | National | 13.4 OZ | 1 | $2.99 | $0.00 | $0.00 | $2.99 | $2.99 |
| L24 | BAKED SWEET GOODS | SWEET GOODS - FULL SIZE | National | 12 OZ | 1 | $3.89 | $0.00 | $0.60 | $3.29 | $3.74 |
| L25 | CRACKERS/MISC BKD FD | CHEESE CRACKERS (CHEEZ-ITS/GOL | National | 6.6 OZ | 1 | $1.99 | $0.00 | $0.00 | $1.99 | $1.99 |
| L26 | CANNED JUICES | BLENDED JUICE&COMBINATIONS (OV | National | 60 OZ | 1 | $4.79 | $0.70 | $1.00 | $3.09 | $4.09 |
| L27 | PORK | ENHANCED | National |   | 2 | $4.56 | $1.97 | $0.00 | $2.59 | $2.67 |
| L28 | REFRGRATD DOUGH PRODUCTS | REFRIGERATED COOKIES-CHUB | Private | 9 OZ | 2 | $1.00 | $0.00 | $0.00 | $1.00 | $1.00 |
| L29 | YOGURT | YOGURT MULTI-PACKS | National | 16 OZ | 1 | $2.49 | $0.20 | $0.00 | $2.29 | $2.29 |
| L30 | CONVENIENT BRKFST/WHLSM SNACKS | CEREAL BARS | National | 10.1 OZ | 1 | $3.29 | $0.00 | $0.00 | $3.29 | $3.29 |
| L31 | FLORAL- HARD GOODS | HOME DECOR | National | 22 INCH | 1 | $9.99 | $0.00 | $0.00 | $9.99 | $9.99 |

Live coupons on the customer's account:

(none)

Customer message:

I was in a rush that day, so I was charged for the orange but never received it.


### Truth

| message | stated | line | decision | reason | refund |
|---|---|---|---|---|---|
| I was in a rush that day, so I was charged for the orange but never received it | missing_item | None | reject | NOT_ON_RECEIPT | 0c |

---

## train-L1-0001 (anchor train-0001, out-of-window: False)

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

Purchase day: 438
Claim filed: day 451

Receipt:
| line | category | sub-category | brand tier | size | qty | regular unit | loyalty disc | coupon disc | paid | reference |
| L01 | GRAPES | GRAPES RED | National | 18 LB | 1 | $2.77 | $1.41 | $0.00 | $1.36 | $1.78 |
| L02 | VEGETABLES - SHELF STABLE | TOMATO PASTE | National | 12 OZ | 2 | $1.39 | $0.46 | $0.00 | $0.93 | $0.93 |
| L03 | POTATOES | POTATOES RUSSET (BULK&BAG) | Private | 5 LB | 2 | $2.99 | $1.50 | $0.00 | $1.49 | $1.49 |
| L04 | COLD CEREAL | ADULT CEREAL | Private | 17.3 OZ | 1 | $1.89 | $0.39 | $0.00 | $1.50 | $1.50 |
| L05 | TROPICAL FRUIT | BANANAS | National | 40 LB | 1 | $0.70 | $0.00 | $0.00 | $0.70 | $0.98 |
| L06 | ICE CREAM/MILK/SHERBTS | SUPER PREMIUM PINTS | National | 15.1 OZ | 1 | $4.54 | $0.00 | $1.00 | $3.54 | $4.54 |

Live coupons on the customer's account:

| coupon | typical value | covers lines |
| C01 | $1.00 | L01, L03, L05 |

Customer message:

My coupon for the cereal was on my account but nothing came off.


### Truth

| message | stated | line | decision | reason | refund |
|---|---|---|---|---|---|
| my coupon for the cereal was on my account but nothing came off | coupon | L04 | reject | NOT_ELIGIBLE | 0c |

---

## train-L1-0002 (anchor train-0002, out-of-window: False)

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

Purchase day: 316
Claim filed: day 321

Receipt:
| line | category | sub-category | brand tier | size | qty | regular unit | loyalty disc | coupon disc | paid | reference |
| L01 | ONIONS | ONIONS OTHER | National | 48 CT | 1 | $0.50 | $0.00 | $0.00 | $0.50 | $0.50 |
| L02 | FRZN POTATOES | FRZN HASHBROWN POTATOES | Private | 28 OZ | 1 | $2.29 | $0.62 | $0.00 | $1.67 | $1.67 |
| L03 | DOG FOODS | CAN DOGFD GOURMET/SUPER PREM ( | National | 5.5 OZ | 1 | $0.69 | $0.15 | $0.00 | $0.54 | $0.54 |
| L04 | BEANS - CANNED GLASS & MW | VARIETY BEANS - KIDNEY PINTO | Private | 15 OZ | 1 | $0.52 | $0.00 | $0.00 | $0.52 | $0.52 |
| L05 | BEERS/ALES | BEERALE -NON ALCOHOLIC | National | 12 OZ | 1 | $6.29 | $0.00 | $0.00 | $6.29 | $6.29 |
| L06 | SINUS AND ALLERGY | SINUS/ALLERGY - PSE | Private |   | 1 | $5.39 | $0.00 | $0.00 | $5.39 | $5.39 |
| L07 | VALUE ADDED FRUIT | INSTORE CUT FRUIT | National |   | 1 | $1.09 | $0.00 | $0.00 | $1.09 | $1.42 |
| L08 | DOG FOODS | CAN DOGFD GOURMET/SUPER PREM ( | National | 5.5 OZ | 2 | $0.69 | $0.15 | $0.00 | $0.54 | $0.54 |
| L09 | BAKING NEEDS | BAKING POWDER & SODA | Private | 16OZ | 1 | $0.59 | $0.00 | $0.00 | $0.59 | $0.59 |
| L10 | CRACKERS/MISC BKD FD | CROUTONS SALAD TOPPERS BREAD | National | 6 OZ | 1 | $1.19 | $0.20 | $0.00 | $0.99 | $0.99 |
| L11 | ONIONS | ONIONS WHITE (BULK&BAG) | National | 20 LB | 1 | $1.51 | $0.00 | $0.00 | $1.51 | $1.75 |
| L12 | FLUID MILK PRODUCTS | FLUID MILK WHITE ONLY | Private |   | 1 | $1.79 | $0.00 | $0.00 | $1.79 | $1.99 |
| L13 | PEPPERS-ALL | PEPPERS GREEN BELL | National | 48-54 CT | 1 | $0.99 | $0.00 | $0.00 | $0.99 | $0.99 |
| L14 | SEAFOOD - SHELF STABLE | SALMON | National | 3 OZ POUCH | 2 | $1.39 | $0.00 | $0.00 | $1.39 | $1.39 |
| L15 | FRZN VEGETABLE/VEG DSH | FRZN BAGGED VEGETABLES - PLAIN | Private | 16 OZ | 1 | $1.29 | $0.29 | $0.00 | $1.00 | $1.00 |
| L16 | CHEESE | CREAM CHEESE | National | 8 OZ | 1 | $2.09 | $0.20 | $0.00 | $1.89 | $1.89 |
| L17 | SUGARS/SWEETNERS | SWEETENERS | Private | 100 CT | 1 | $1.29 | $0.40 | $0.00 | $0.89 | $0.89 |
| L18 | CAT FOOD | CANNED CAT FOOD (9 LIVES/FRISK | Private | 5.5 OZ | 2 | $0.29 | $0.04 | $0.00 | $0.25 | $0.25 |
| L19 | DINNER MXS:DRY | MEAT INCLUDED | National | 36.6 OZ | 1 | $3.47 | $0.00 | $0.00 | $3.47 | $3.47 |
| L20 | DOG FOODS | CAN DOGFD GOURMET/SUPER PREM ( | National | 5.5 OZ | 1 | $0.69 | $0.14 | $0.00 | $0.55 | $0.55 |
| L21 | CAT FOOD | CANNED CAT FOOD (9 LIVES/FRISK | Private | 5.5 OZ | 2 | $0.29 | $0.04 | $0.00 | $0.25 | $0.25 |
| L22 | BAKED BREAD/BUNS/ROLLS | PREMIUM BREAD | National | 32 OZ | 1 | $3.19 | $1.10 | $0.00 | $2.09 | $2.09 |
| L23 | STATIONERY & SCHOOL SUPPLIES | SCHOOL SUPPLIES | Private | 5 OZ | 1 | $0.99 | $0.00 | $0.00 | $0.99 | $0.99 |
| L24 | TROPICAL FRUIT | BANANAS | National | 40 LB | 1 | $0.84 | $0.00 | $0.00 | $0.84 | $0.98 |
| L25 | FEMININE HYGIENE | FEM. HYGN.NAPKINS | National |   | 1 | $2.68 | $0.18 | $0.00 | $2.50 | $2.50 |
| L26 | HOUSEHOLD CLEANG NEEDS | TOILET BOWL MANUAL | National | 32 OZ | 1 | $1.89 | $0.39 | $0.00 | $1.50 | $1.50 |
| L27 | CAT FOOD | CAN CATFD GOURMET/SUP PREM (GR | National | 3 OZ | 5 | $0.45 | $0.05 | $0.00 | $0.40 | $0.40 |
| L28 | PORK | ENHANCED | National |   | 2 | $3.00 | $1.29 | $0.00 | $1.71 | $2.27 |
| L29 | CHEESE | NATURAL CHEESE EXACT WT CHUNKS | Private | 8 OZ | 1 | $2.99 | $1.49 | $0.00 | $1.50 | $1.50 |
| L30 | TOMATOES | TOMATOES VINE RIPE PKG | Private | 4 CT | 1 | $3.99 | $0.00 | $0.00 | $3.99 | $3.99 |
| L31 | AIR CARE | AIR CARE - CONTINUOUS ACTION | National | .71 OZ | 2 | $3.49 | $0.00 | $0.50 | $2.99 | $3.49 |
| L32 | FROZEN PIZZA | PIZZA/SINGLE SERVE/MICROWAVE | National | 10.81 OZ | 1 | $3.39 | $0.00 | $0.00 | $3.39 | $3.39 |
| L33 | DINNER MXS:DRY | SKILLET DINNERS | National | 7.4 OZ | 1 | $2.59 | $0.59 | $0.00 | $2.00 | $2.00 |
| L34 | ORAL HYGIENE PRODUCTS | TOOTHPASTE | National | 5.6 OZ | 1 | $2.89 | $0.00 | $0.00 | $2.89 | $2.89 |
| L35 | SOUP | RTS SOUP: CHUNKY/HOMESTYLE ET | National | 18.3 OZ | 2 | $2.99 | $0.99 | $0.00 | $2.00 | $2.00 |
| L36 | FEMININE HYGIENE | FEM. HYGN.NAPKINS | National |   | 1 | $2.68 | $0.18 | $0.00 | $2.50 | $2.50 |

Live coupons on the customer's account:

(none)

Customer message:

We really rely on that item, there is a pricing error on the cleaning supplies.


### Truth

| message | stated | line | decision | reason | refund |
|---|---|---|---|---|---|
| we really rely on that item, there is a pricing error on the cleaning supplies | price | L26 | reject | WITHIN_TOLERANCE | 0c |