# Instance preview

### dev-L1-0 — trap=False C*=$4.90 greedy=$4.90 (gap 0c)

**COOKIES/CONES** (VANILLA WAFER/KIDS COOKIES)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| T4 | Private | 69 | 12 OZ | $2.49 | $0.61 | $1.88 |
| W7 | National | 1075 | 10 OZ | $2.79 | $0.60 | $2.19 ←bought |
| M2 | National | 1075 | 8 OZ | $3.09 | $0.00 | $3.09 |

**FLUID MILK PRODUCTS** (FLUID MILK WHITE ONLY)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| N6 | National | 5423 |   | $0.50 | $0.00 | $0.50 |
| M3 | National | 1543 | 1/2 GAL | $2.19 | $0.00 | $2.19 |
| E1 | Private | 69 |   | $1.85 | $0.85 | $1.00 ←bought |

**CANNED JUICES** (CRANAPPLE CRAN GRAPE JUICE (5)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| N7 | National | 612 | 64 OZ | $3.89 | $0.40 | $3.49 |
| N2 | National | 2044 | 64 OZ | $2.29 | $0.79 | $1.50 |
| H6 | Private | 69 | 64 OZ | $2.00 | $0.00 | $2.00 ←bought |

**ONIONS** (ONIONS SWEET (BULK&BAG))
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| Y3 | National | 2 |   | $1.55 | $0.00 | $1.55 |
| D4 | National | 2 | 40 LB | $1.56 | $0.00 | $1.56 |
| J9 | National | 2 | 40 LB | $1.02 | $0.00 | $1.02 ←bought |
- coupon K0: $0.50 off SKU M3 (real)

- n_carts=81, feasible=81, optimal=1, binding=[]
- real cart {'COOKIES/CONES': 'W7', 'FLUID MILK PRODUCTS': 'E1', 'CANNED JUICES': 'H6', 'ONIONS': 'J9'} → $6.21 (feasible=True)

---

### dev-L1-1 — trap=True C*=$2.11 greedy=$2.61 (gap 50c)

**GREETING CARDS/WRAP/PARTY SPLY** (CARDS SEASONAL)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| L7 | National | 1407 |   | $0.99 | $0.00 | $0.99 |
| N5 | National | 1407 |   | $0.99 | $0.50 | $0.49 |
| V8 | National | 5143 |   | $3.69 | $0.00 | $3.69 ←bought |

**BLEACH** (LIQUID BLEACH)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| S1 | National | 1091 | 96 OZ | $1.99 | $0.49 | $1.50 ←bought |
| P0 | National | 1091 | 60 OUNCE | $1.49 | $0.00 | $1.49 |
| T0 | Private | 69 | 96 OZ | $1.59 | $0.59 | $1.00 |

**BAKED BREAD/BUNS/ROLLS** (HAMBURGER BUNS)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| D0 | National | 910 |   | $2.49 | $0.00 | $2.49 |
| M9 | Private | 69 | 12 OZ | $1.29 | $0.30 | $0.99 ←bought |
| R1 | Private | 69 | 12 OZ | $1.49 | $0.00 | $1.49 |

**DISHWASH DETERGENTS** (LIQUID DISH DETERGENT)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| M6 | Private | 69 | 25 OZ | $1.29 | $0.00 | $1.29 |
| V3 | National | 720 | 16 OZ | $1.13 | $0.00 | $1.13 ←bought |
| K3 | National | 764 | 22 OZ | $2.59 | $0.00 | $2.59 |
- coupon K0: $1.00 off SKU N5 (synthetic)
- coupon K1: $1.00 off SKU S1 (synthetic)

- n_carts=81, feasible=81, optimal=1, binding=['K0', 'K1']
- real cart {'GREETING CARDS/WRAP/PARTY SPLY': 'V8', 'BLEACH': 'S1', 'BAKED BREAD/BUNS/ROLLS': 'M9', 'DISHWASH DETERGENTS': 'V3'} → $6.31 (feasible=True)

---

### dev-L1-2 — trap=False C*=$6.53 greedy=$6.53 (gap 0c)

**PWDR/CRYSTL DRNK MX** (SOFT DRINK CANISTERS)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| Y4 | National | 1046 | 19 OZ | $3.39 | $0.00 | $3.39 ←bought |
| N0 | National | 1782 | 14 QT | $2.99 | $0.00 | $2.99 |
| P4 | Private | 69 | 20 OZ | $1.99 | $0.00 | $1.99 |

**PASTA SAUCE** (PREMIUM)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| M9 | Private | 69 | 56 OZ | $4.79 | $1.80 | $2.99 |
| W7 | National | 874 | 26 OZ | $2.89 | $0.89 | $2.00 ←bought |
| D5 | National | 2193 | 48 OZ | $5.19 | $2.69 | $2.50 |

**SOUP** (CONDENSED SOUP)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| K5 | Private | 69 | 10.5OZ | $0.55 | $0.00 | $0.55 |
| R5 | National | 1251 | 10.75 OZ | $1.39 | $0.00 | $1.39 |
| D2 | National | 1251 | 10.5 OZ | $1.29 | $0.54 | $0.75 ←bought |

**FLUID MILK PRODUCTS** (FLUID MILK WHITE ONLY)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| F3 | Private | 69 |   | $1.99 | $0.00 | $1.99 ←bought |
| W0 | Private | 69 | 1 GA | $2.69 | $0.00 | $2.69 |
| T8 | National | 926 | 1/2 GAL | $3.79 | $0.00 | $3.79 |
- coupon K0: $0.50 off SKU M9 (real)

- n_carts=81, feasible=81, optimal=1, binding=[]
- real cart {'PWDR/CRYSTL DRNK MX': 'Y4', 'PASTA SAUCE': 'W7', 'SOUP': 'D2', 'FLUID MILK PRODUCTS': 'F3'} → $8.13 (feasible=True)

---

### dev-L1-4 — trap=True C*=$7.31 greedy=$7.66 (gap 35c)

**DRY NOODLES/PASTA** (NOODLES DRY)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| M5 | Private | 69 | 16 OZ | $1.19 | $0.20 | $0.99 |
| Z4 | National | 179 | 1 LB | $1.19 | $0.39 | $0.80 ←bought |
| A9 | Private | 69 | 16OZ | $1.29 | $0.30 | $0.99 |

**BAG SNACKS** (POTATO CHIPS)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| U6 | National | 780 | 9 OZ | $2.99 | $0.49 | $2.50 ←bought |
| P8 | Private | 69 | 11.5 OZ | $1.58 | $0.08 | $1.50 |
| A8 | National | 2150 | 3.5 OZ | $1.09 | $0.10 | $0.99 |

**SINUS AND ALLERGY** (SINUS/ALLERGY - PSE)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| V9 | National | 4940 | 24 CT | $5.99 | $0.00 | $5.99 ←bought |
| H1 | National | 870 | 30 CT | $28.99 | $0.00 | $28.99 |
| U1 | Private | 69 | 10 CT | $7.67 | $0.77 | $6.90 |

**BAKED BREAD/BUNS/ROLLS** (HOT DOG BUNS)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| D4 | Private | 69 | 10 OZ | $1.39 | $0.51 | $0.88 |
| X5 | National | 1882 | 12 OZ | $2.49 | $0.49 | $2.00 |
| X2 | Private | 69 | 10 OZ | $1.39 | $0.51 | $0.88 ←bought |
- coupon K0: $0.35 off SKU X2 (synthetic)
- coupon K1: $1.00 off SKU A8 (synthetic)

- n_carts=81, feasible=81, optimal=1, binding=['K0', 'K1']
- real cart {'DRY NOODLES/PASTA': 'Z4', 'BAG SNACKS': 'U6', 'SINUS AND ALLERGY': 'V9', 'BAKED BREAD/BUNS/ROLLS': 'X2'} → $9.82 (feasible=True)

---

### dev-L1-6 — trap=False C*=$4.98 greedy=$4.98 (gap 0c)

**FROZEN PIZZA** (PIZZA/ECONOMY)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| B1 | National | 1039 | 10.4 OZ | $1.00 | $0.00 | $1.00 |
| G3 | Private | 69 | 6.5 OZ | $0.79 | $0.00 | $0.79 |
| T7 | National | 1039 | 10.7 OZ | $1.00 | $0.00 | $1.00 ←bought |

**FLUID MILK PRODUCTS** (FLUID MILK WHITE ONLY)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| W1 | Private | 69 | 1 GA | $2.69 | $0.00 | $2.69 ←bought |
| T9 | National | 1543 | .5 GAL | $2.19 | $0.00 | $2.19 |
| R2 | National | 926 | 1/2 GAL | $3.79 | $0.20 | $3.59 |

**BAKED SWEET GOODS** (SNACK CAKE - MULTI PACK)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| Z8 | National | 418 | 27.96 OZ | $2.63 | $0.00 | $2.63 |
| V5 | National | 418 | 16 OZ | $1.09 | $0.09 | $1.00 ←bought |
| Y5 | National | 1733 | 10.6 OZ | $3.69 | $1.19 | $2.50 |

**CANDY - PACKAGED** (CANDY BARS (MULTI PACK))
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| Y4 | National | 693 | 6 PK | $2.99 | $0.00 | $2.99 |
| P3 | National | 531 | 4.5 OZ | $1.39 | $0.39 | $1.00 ←bought |
| W3 | National | 531 | 6.5 OZ | $1.39 | $0.39 | $1.00 |
- coupon K0: $0.35 off SKU Y5 (synthetic)

- n_carts=81, feasible=81, optimal=2, binding=[]
- real cart {'FROZEN PIZZA': 'T7', 'FLUID MILK PRODUCTS': 'W1', 'BAKED SWEET GOODS': 'V5', 'CANDY - PACKAGED': 'P3'} → $5.69 (feasible=True)

---

### dev-L1-7 — trap=False C*=$4.40 greedy=$4.40 (gap 0c)

**MARGARINES** (MARGARINE: TUBS AND BOWLS)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| Z9 | Private | 69 | 2/8 OZ | $0.79 | $0.20 | $0.59 |
| D5 | National | 560 | 3 LB | $2.99 | $0.99 | $2.00 ←bought |
| S4 | National | 516 | 45 OZ | $2.34 | $0.00 | $2.34 |

**FLUID MILK PRODUCTS** (FLUID MILK WHITE ONLY)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| F6 | Private | 69 | 1 PT | $0.89 | $0.00 | $0.89 |
| J5 | National | 926 | 1/2 GAL | $3.79 | $0.20 | $3.59 |
| R2 | Private | 69 | 1 GA | $2.69 | $0.00 | $2.69 ←bought |

**LUNCHMEAT** (LUNCH COMBO)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| B1 | National | 1094 | 4.5 OZ | $1.99 | $0.32 | $1.67 |
| A2 | National | 1094 | 4.2 OZ | $1.99 | $0.32 | $1.67 ←bought |
| E6 | National | 1094 | 4.5OZ | $1.99 | $0.32 | $1.67 |

**COLD CEREAL** (ALL FAMILY CEREAL)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| Q8 | National | 794 | 18 OZ | $3.27 | $0.00 | $3.27 ←bought |
| Z1 | Private | 69 | 12.8 OZ | $2.39 | $0.39 | $2.00 |
| M5 | National | 194 | 17 OZ | $5.29 | $0.80 | $4.49 |
- coupon K0: $0.75 off SKU Z1 (real)
- coupon K1: $1.00 off SKU J5 (real)

- n_carts=81, feasible=81, optimal=3, binding=['K0']
- real cart {'MARGARINES': 'D5', 'FLUID MILK PRODUCTS': 'R2', 'LUNCHMEAT': 'A2', 'COLD CEREAL': 'Q8'} → $9.63 (feasible=True)

---

### dev-L1-8 — trap=False C*=$9.66 greedy=$9.66 (gap 0c)

**BAKING MIXES** (BROWNIE MIX)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| G4 | National | 194 | 18.3 OZ | $2.39 | $1.39 | $1.00 ←bought |
| S7 | National | 1266 | 19.5 OZ | $2.09 | $0.00 | $2.09 |
| D3 | Private | 69 | 10.25 OZ | $0.89 | $0.00 | $0.89 |

**BAKED BREAD/BUNS/ROLLS** (HOT DOG BUNS)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| R5 | Private | 69 | 11 OZ | $1.29 | $0.41 | $0.88 ←bought |
| J8 | National | 1102 | 12 OZ | $2.19 | $0.80 | $1.39 |
| C7 | Private | 69 | 16CT/22 OZ | $1.79 | $0.29 | $1.50 |

**SHORTENING/OIL** (OLIVE OIL)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| C9 | Private | 69 | 25.5 OZ | $7.99 | $0.00 | $7.99 ←bought |
| Y2 | National | 1863 | 17 OZ | $7.69 | $1.80 | $5.89 |
| G2 | Private | 69 | 25.5 OZ | $7.99 | $0.00 | $7.99 |

**SOFT DRINKS** (SOFT DRINKS 12/18&15PK CAN CAR)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| S6 | Private | 69 | 12 OZ | $2.00 | $0.00 | $2.00 |
| Q8 | National | 103 | 12 OZ | $4.59 | $0.00 | $4.59 ←bought |
| Q5 | Private | 69 | 12 OZ | $2.00 | $0.00 | $2.00 |
- coupon K0: $0.45 off SKU G2 (synthetic)

- n_carts=81, feasible=81, optimal=2, binding=[]
- real cart {'BAKING MIXES': 'G4', 'BAKED BREAD/BUNS/ROLLS': 'R5', 'SHORTENING/OIL': 'C9', 'SOFT DRINKS': 'Q8'} → $14.46 (feasible=True)

---

### dev-L1-9 — trap=False C*=$6.21 greedy=$6.21 (gap 0c)

**WAREHOUSE SNACKS** (CANISTER POTATO/TORT CHIPS)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| Z7 | National | 764 | 5.75 OZ | $1.29 | $0.00 | $1.29 |
| A1 | National | 764 | 5.75 OZ | $1.29 | $0.00 | $1.29 |
| L2 | National | 764 | 6.5 OZ | $1.99 | $0.00 | $1.99 ←bought |

**FD WRAPS/BAGS/TRSH BG** (SANDWICH BAGS)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| V3 | National | 458 | 100 CT | $3.39 | $0.00 | $3.39 |
| S6 | Private | 69 | 150 CT | $1.59 | $0.00 | $1.59 ←bought |
| K1 | Private | 69 | 100 CT | $2.79 | $0.80 | $1.99 |

**SOFT DRINKS** (SFT DRNK SNGL SRV BTL CARB (EX)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| D2 | National | 1208 | 20 OZ NR | $1.29 | $0.00 | $1.29 |
| J4 | National | 1918 | 20 OZ | $0.33 | $0.00 | $0.33 ←bought |
| N1 | National | 103 | 20 OZ | $1.29 | $0.29 | $1.00 |

**FRZN MEAT/MEAT DINNERS** (FRZN MULTI SERVE ENTREES ALL)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| B5 | Private | 69 | 30 OZ | $5.99 | $0.00 | $5.99 |
| A6 | National | 1508 | 28 OZ | $3.99 | $0.99 | $3.00 ←bought |
| R4 | National | 5758 | 32OZ TRAY | $7.99 | $0.00 | $7.99 |
- coupon K0: $1.00 off SKU R4 (synthetic)
- coupon K1: $0.01 off SKU K1 (synthetic)

- n_carts=81, feasible=81, optimal=2, binding=[]
- real cart {'WAREHOUSE SNACKS': 'L2', 'FD WRAPS/BAGS/TRSH BG': 'S6', 'SOFT DRINKS': 'J4', 'FRZN MEAT/MEAT DINNERS': 'A6'} → $6.91 (feasible=True)

---

### dev-L1-10 — trap=False C*=$6.45 greedy=$6.45 (gap 0c)

**CIGARETTES** (CIGARETTES)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| W5 | National | 111 | 523670 CTN | $35.84 | $0.00 | $35.84 |
| S3 | National | 111 | CTN | $2.72 | $0.00 | $2.72 |
| D6 | National | 539 | 974246  PK | $3.84 | $0.00 | $3.84 ←bought |

**PWDR/CRYSTL DRNK MX** (SOFT DRINK CANISTERS)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| H6 | National | 1782 | 1.35 OZ | $2.99 | $0.00 | $2.99 |
| W6 | Private | 69 | 19 OZ | $1.79 | $0.00 | $1.79 |
| G3 | National | 1046 | 2.3 OZ | $4.99 | $0.60 | $4.39 ←bought |

**DINNER MXS:DRY** (MACARONI & CHEESE DNRS)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| U0 | National | 317 | 7.25 OZ | $0.69 | $0.00 | $0.69 |
| S9 | Private | 69 | 12 OZ | $1.42 | $0.13 | $1.29 |
| C3 | National | 317 | 7.25 OZ | $0.69 | $0.00 | $0.69 ←bought |

**CONVENIENT BRKFST/WHLSM SNACKS** (FRUIT SNACKS)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| T9 | National | 194 | 18 OZ | $4.99 | $0.00 | $4.99 |
| U4 | Private | 69 | 5.4 OZ | $1.65 | $0.40 | $1.25 |
| S6 | National | 194 | 5 OZ | $2.79 | $0.00 | $2.79 ←bought |
- coupon K0: $1.00 off SKU D6 (synthetic)

- n_carts=81, feasible=81, optimal=2, binding=[]
- real cart {'CIGARETTES': 'D6', 'PWDR/CRYSTL DRNK MX': 'G3', 'DINNER MXS:DRY': 'C3', 'CONVENIENT BRKFST/WHLSM SNACKS': 'S6'} → $10.71 (feasible=True)

---

### dev-L1-11 — trap=False C*=$10.51 greedy=$10.51 (gap 0c)

**CONDIMENTS/SAUCES** (CHILI SAUCE COCKTAIL SAUCE)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| R1 | National | 131 | 12 OZ | $1.79 | $0.29 | $1.50 ←bought |
| G7 | Private | 69 | 12 OZ | $1.39 | $0.40 | $0.99 |
| D0 | Private | 69 | 9.5 OZ | $1.79 | $0.40 | $1.39 |

**DINNER SAUSAGE** (COCKTAILS)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| N5 | National | 1089 | 1 LB | $3.99 | $1.49 | $2.50 |
| L6 | National | 1089 | 14 OZ | $3.99 | $1.49 | $2.50 ←bought |
| F9 | National | 1089 | 1 LB | $3.99 | $1.49 | $2.50 |

**COOKIES/CONES** (GRAHAM CRACKERS)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| U7 | National | 1075 | 14.4 OZ | $3.49 | $0.00 | $3.49 |
| W0 | Private | 69 | 16 OZ | $1.03 | $0.00 | $1.03 |
| K4 | National | 586 | 14 OZ | $3.39 | $0.89 | $2.50 ←bought |

**DOMESTIC WINE** (POPULAR 750ML WINES)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| B6 | National | 2468 | 750 ML | $6.99 | $0.00 | $6.99 |
| W5 | National | 2627 | 750 ML | $5.99 | $0.00 | $5.99 ←bought |
| E4 | National | 2547 | 750 ML | $8.99 | $0.00 | $8.99 |
- coupon K0: $0.50 off SKU K4 (synthetic)

- n_carts=81, feasible=81, optimal=3, binding=[]
- real cart {'CONDIMENTS/SAUCES': 'R1', 'DINNER SAUSAGE': 'L6', 'COOKIES/CONES': 'K4', 'DOMESTIC WINE': 'W5'} → $11.99 (feasible=True)

---

### dev-L1-12 — trap=False C*=$4.05 greedy=$4.05 (gap 0c)

**YOGURT** (YOGURT NOT MULTI-PACKS)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| X5 | Private | 69 | 6 OZ | $0.39 | $0.00 | $0.39 |
| F9 | Private | 69 | 6 OZ | $0.39 | $0.00 | $0.39 |
| H5 | National | 1487 | 11 OZ | $1.69 | $0.19 | $1.50 ←bought |

**COLD CEREAL** (ADULT CEREAL)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| T2 | Private | 69 | 18 OZ | $2.29 | $0.29 | $2.00 |
| A0 | National | 194 | 18 OZ | $4.09 | $0.00 | $4.09 ←bought |
| W2 | Private | 69 | 16 OZ | $2.29 | $0.29 | $2.00 |

**FLUID MILK PRODUCTS** (FLUID MILK WHITE ONLY)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| W1 | Private | 69 | 1 GA | $2.49 | $0.00 | $2.49 ←bought |
| A7 | Private | 69 | 1 PT | $0.89 | $0.22 | $0.67 |
| N9 | National | 1543 | 1 GAL | $3.99 | $0.00 | $3.99 |

**BUTTER** (BUTTER)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| C1 | Private | 69 | 1 LB | $3.59 | $1.59 | $2.00 ←bought |
| K9 | National | 709 | 8 OZ | $1.99 | $0.00 | $1.99 |
| T1 | Private | 69 | 1 LB | $3.59 | $1.59 | $2.00 |
- coupon K0: $1.00 off SKU A7 (synthetic)

- n_carts=81, feasible=81, optimal=12, binding=['K0']
- real cart {'YOGURT': 'H5', 'COLD CEREAL': 'A0', 'FLUID MILK PRODUCTS': 'W1', 'BUTTER': 'C1'} → $10.08 (feasible=True)

---

### dev-L1-20 — trap=True C*=$9.95 greedy=$10.52 (gap 57c)

**CANDY - CHECKLANE** (CANDY BARS (SINGLES)(INCLUDING)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| H4 | Private | 69 | 3.53 OZ | $1.04 | $0.00 | $1.04 |
| F9 | National | 531 | 1.52 OZ | $0.60 | $0.34 | $0.26 ←bought |
| K2 | National | 693 | 1.5 OZ | $0.46 | $0.17 | $0.29 |

**REFRGRATD DOUGH PRODUCTS** (REFRIGERATED BISCUITS REGULAR)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| Z8 | National | 236 | 12 OZ | $1.39 | $0.00 | $1.39 |
| P9 | National | 236 | 7.5 OZ | $1.89 | $0.00 | $1.89 ←bought |
| K6 | Private | 69 | 30 OZ | $1.27 | $0.00 | $1.27 |

**FD WRAPS/BAGS/TRSH BG** (GARBAGE KITCHEN COMPACTOR BA)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| W9 | Private | 69 | 20 CT | $2.19 | $1.19 | $1.00 |
| G0 | National | 150 | 40 CT | $6.49 | $1.00 | $5.49 |
| Z3 | National | 121 | 45 CT | $7.59 | $0.00 | $7.59 ←bought |

**BEERS/ALES** (BEERALEMALT LIQUORS)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| N2 | National | 239 | 12 OZ | $11.99 | $0.00 | $11.99 ←bought |
| P0 | Private | 5483 | 12 OZ | $7.99 | $0.00 | $7.99 |
| C7 | National | 1465 | 12 OZ | $7.99 | $0.00 | $7.99 |
- coupon K0: $1.00 off SKU Z3 (real)
- coupon K1: $0.60 off SKU K2 (synthetic)

- n_carts=81, feasible=81, optimal=2, binding=['K1']
- real cart {'CANDY - CHECKLANE': 'F9', 'REFRGRATD DOUGH PRODUCTS': 'P9', 'FD WRAPS/BAGS/TRSH BG': 'Z3', 'BEERS/ALES': 'N2'} → $20.73 (feasible=True)

---

### dev-L1-24 — trap=True C*=$2.60 greedy=$2.78 (gap 18c)

**SOFT DRINKS** (SFT DRNK 2 LITER BTL CARB INCL)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| E3 | Private | 69 | 2 LTR | $0.59 | $0.03 | $0.56 |
| L0 | Private | 69 | 2 LTR | $0.59 | $0.00 | $0.59 |
| W3 | National | 1208 | 2 LTR | $1.59 | $0.71 | $0.88 ←bought |

**VEGETABLES - ALL OTHERS** (CELERY)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| B7 | National | 2 |   | $0.99 | $0.40 | $0.59 ←bought |
| A4 | National | 2 |   | $1.29 | $0.30 | $0.99 |
| R3 | Private | 69 | 1 LB | $1.29 | $0.30 | $0.99 |

**BAKING MIXES** (LAYER CAKE MIX)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| D2 | National | 5258 | 18.25 OZ | $1.69 | $0.40 | $1.29 |
| C0 | National | 194 | 18.25 OZ | $2.19 | $1.31 | $0.88 |
| H8 | National | 5258 | 18.25 OZ | $1.69 | $0.40 | $1.29 ←bought |

**BAKED BREAD/BUNS/ROLLS** (MAINSTREAM WHITE BREAD)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| F0 | National | 1838 | 20 OZ | $1.99 | $0.50 | $1.49 ←bought |
| U3 | Private | 69 | 24 OZ | $1.59 | $0.40 | $1.19 |
| H7 | Private | 69 | 16 OZ | $0.75 | $0.00 | $0.75 |
- coupon K0: $0.50 off SKU W3 (real)

- n_carts=81, feasible=81, optimal=1, binding=['K0']
- real cart {'SOFT DRINKS': 'W3', 'VEGETABLES - ALL OTHERS': 'B7', 'BAKING MIXES': 'H8', 'BAKED BREAD/BUNS/ROLLS': 'F0'} → $3.75 (feasible=True)

---

### dev-L1-41 — trap=True C*=$5.93 greedy=$6.23 (gap 30c)

**DELI MEATS** (MEAT: TURKEY BULK)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| R4 | National | 4084 |   | $4.47 | $0.49 | $3.98 ←bought |
| P6 | National | 4496 |   | $3.50 | $0.00 | $3.50 |
| C8 | National | 4218 |   | $5.77 | $0.00 | $5.77 |

**ISOTONIC DRINKS** (ISOTONIC DRINKS SINGLE SERVE)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| U3 | National | 1208 | 32 OZ | $1.33 | $0.00 | $1.33 |
| S1 | National | 1276 | 20 OZ | $6.99 | $1.99 | $5.00 |
| E4 | National | 1208 | 32 OZ | $1.34 | $0.00 | $1.34 ←bought |

**YOGURT** (YOGURT NOT MULTI-PACKS)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| A5 | National | 759 | 6 OZ | $0.79 | $0.39 | $0.40 ←bought |
| Y8 | National | 1487 | 6 OZ | $0.79 | $0.19 | $0.60 |
| S5 | Private | 69 | 10 OZ | $1.39 | $0.39 | $1.00 |

**BAKED BREAD/BUNS/ROLLS** (DIET/LIGHT BREAD)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| R7 | National | 1639 | 20 OZ | $2.59 | $1.00 | $1.59 |
| T7 | Private | 69 | 16 OZ | $1.59 | $0.59 | $1.00 ←bought |
| E9 | National | 1102 | 16 OZ | $2.19 | $0.30 | $1.89 |
- coupon K0: $0.50 off SKU Y8 (real)
- coupon K1: $0.75 off SKU S5 (synthetic)

- n_carts=81, feasible=81, optimal=2, binding=['K0']
- real cart {'DELI MEATS': 'R4', 'ISOTONIC DRINKS': 'E4', 'YOGURT': 'A5', 'BAKED BREAD/BUNS/ROLLS': 'T7'} → $6.72 (feasible=True)

---

### dev-L1-50 — trap=True C*=$4.35 greedy=$4.77 (gap 42c)

**BAKED BREAD/BUNS/ROLLS** (MAINSTREAM WHEAT/MULTIGRAIN BR)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| M4 | Private | 69 | 24 OZ | $1.59 | $0.40 | $1.19 |
| G4 | National | 910 | 20 OZ | $1.99 | $0.00 | $1.99 ←bought |
| T3 | National | 194 | 24 OZ | $1.49 | $0.00 | $1.49 |

**FRZN BREAKFAST FOODS** (FRZN BREAKFAST PASTRY)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| G3 | National | 236 | 11.5 OZ | $2.07 | $0.08 | $1.99 |
| C7 | National | 236 | 11.5 OZ | $2.07 | $0.08 | $1.99 ←bought |
| Z4 | Private | 69 | 12 CT | $2.49 | $0.49 | $2.00 |

**PASTA SAUCE** (MAINSTREAM)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| W9 | National | 754 | 26 OZ | $1.85 | $0.18 | $1.67 ←bought |
| Z9 | Private | 69 | 26 OZ | $1.09 | $0.00 | $1.09 |
| F0 | National | 1747 | 28 OZ | $2.69 | $0.00 | $2.69 |

**DRY NOODLES/PASTA** (SPAGHETTI DRY)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| Y8 | Private | 69 | 16 OZ | $0.55 | $0.05 | $0.50 |
| W4 | National | 2143 | 16 OZ | $1.19 | $0.19 | $1.00 ←bought |
| J6 | National | 566 | 32 OZ | $1.79 | $0.10 | $1.69 |
- coupon K0: $1.00 off SKU W9 (real)
- coupon K1: $0.56 off SKU G4 (synthetic)

- n_carts=81, feasible=81, optimal=3, binding=['K0']
- real cart {'BAKED BREAD/BUNS/ROLLS': 'G4', 'FRZN BREAKFAST FOODS': 'C7', 'PASTA SAUCE': 'W9', 'DRY NOODLES/PASTA': 'W4'} → $5.09 (feasible=True)

---

### dev-L1-53 — trap=True C*=$6.94 greedy=$9.25 (gap 231c)

**DELI MEATS** (MEAT: TURKEY BULK)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| T6 | National | 3730 |   | $3.66 | $0.26 | $3.40 ←bought |
| X3 | National | 3886 |   | $1.96 | $0.00 | $1.96 |
| E4 | National | 4218 |   | $7.49 | $0.00 | $7.49 |

**HISPANIC** (MEXICAN SAUCESSALSAPICANTEE)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| E1 | National | 691 | 16 OZ | $3.99 | $0.00 | $3.99 |
| A1 | Private | 69 | 24 OZ | $2.59 | $0.09 | $2.50 ←bought |
| F9 | Private | 69 | 24 OZ | $2.59 | $0.09 | $2.50 |

**FLUID MILK PRODUCTS** (FLUID MILK WHITE ONLY)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| Q1 | Private | 69 |   | $1.85 | $0.85 | $1.00 |
| G8 | Private | 69 | 1 GA | $2.69 | $0.00 | $2.69 ←bought |
| Q3 | National | 1543 | 1 GAL | $3.99 | $0.00 | $3.99 |

**COFFEE** (INSTANT COFFEE REGULAR)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| K0 | National | 456 | 8 OZ | $5.32 | $0.00 | $5.32 ←bought |
| P7 | Private | 69 | 8 OZ | $3.99 | $0.20 | $3.79 |
| W9 | National | 531 | 7 OZ | $4.69 | $0.10 | $4.59 |
- coupon K0: $4.00 off SKU G8 (real)
- coupon K1: $0.75 off SKU Q3 (real)

- n_carts=81, feasible=81, optimal=2, binding=['K0']
- real cart {'DELI MEATS': 'T6', 'HISPANIC': 'A1', 'FLUID MILK PRODUCTS': 'G8', 'COFFEE': 'K0'} → $9.91 (feasible=True)

---

### dev-L1-57 — trap=True C*=$6.76 greedy=$6.87 (gap 11c)

**DINNER SAUSAGE** (FRESH)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| R0 | National | 2082 | 16 OZ | $3.79 | $1.29 | $2.50 |
| D1 | Private | 69 | 18 OZ | $3.29 | $0.00 | $3.29 |
| U7 | National | 2209 | 19.76 OZ | $5.29 | $1.79 | $3.50 ←bought |

**DINNER MXS:DRY** (STUFFING MIXES)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| F7 | National | 1046 | 6OZ | $1.99 | $0.99 | $1.00 ←bought |
| S4 | National | 1046 |   | $1.99 | $0.49 | $1.50 |
| S9 | Private | 69 | 6 OZ | $1.59 | $0.71 | $0.88 |

**FLUID MILK PRODUCTS** (FLUID MILK WHITE ONLY)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| S5 | Private | 69 |   | $1.99 | $0.00 | $1.99 |
| J7 | Private | 69 | 1 GA | $2.49 | $0.00 | $2.49 ←bought |
| H4 | National | 1009 | 64 OZ | $3.89 | $0.40 | $3.49 |

**REFRGRATD DOUGH PRODUCTS** (MISC REFRIG DOUGH PRODUCTS)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| Z6 | National | 236 | 15 OZ | $2.39 | $0.00 | $2.39 |
| W2 | National | 236 | 11 OZ | $2.49 | $0.00 | $2.49 |
| V1 | Private | 69 | 15 OZ | $2.29 | $0.79 | $1.50 ←bought |
- coupon K0: $1.00 off SKU Z6 (real)

- n_carts=81, feasible=81, optimal=1, binding=['K0']
- real cart {'DINNER SAUSAGE': 'U7', 'DINNER MXS:DRY': 'F7', 'FLUID MILK PRODUCTS': 'J7', 'REFRGRATD DOUGH PRODUCTS': 'V1'} → $8.49 (feasible=True)

---

### dev-L1-62 — trap=True C*=$3.05 greedy=$4.07 (gap 102c)

**HISPANIC** (ORIENTAL SOY SAUCE)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| F8 | National | 928 | 15 OZ | $1.35 | $0.00 | $1.35 |
| U7 | Private | 69 | 10 OZ | $1.29 | $0.40 | $0.89 ←bought |
| P4 | National | 87 | 5 OZ | $1.00 | $0.00 | $1.00 |

**CHICKEN** (CHICKEN BREAST BONELESS)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| C4 | National | 4172 |   | $2.63 | $0.00 | $2.63 |
| D4 | National | 4303 |   | $5.72 | $3.57 | $2.15 |
| E2 | National | 4314 |   | $8.77 | $5.33 | $3.44 ←bought |

**CANDY - PACKAGED** (CANDY BAGS-NON CHOCOLATE W/FLO)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| P0 | National | 693 | 12 OZ | $1.00 | $0.00 | $1.00 ←bought |
| T5 | National | 1573 |   | $1.49 | $0.49 | $1.00 |
| D5 | National | 1019 | 5 OZ | $0.99 | $0.00 | $0.99 |

**ONIONS** (ONIONS SWEET (BULK&BAG))
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| E6 | National | 2 | 40 LB | $0.88 | $0.34 | $0.54 ←bought |
| H5 | National | 2 |   | $2.00 | $0.00 | $2.00 |
| W7 | National | 2 | 40 LB | $1.14 | $0.00 | $1.14 |
- coupon K0: $0.50 off SKU D4 (real)
- coupon K1: $2.00 off SKU C4 (real)

- n_carts=81, feasible=81, optimal=3, binding=['K1']
- real cart {'HISPANIC': 'U7', 'CHICKEN': 'E2', 'CANDY - PACKAGED': 'P0', 'ONIONS': 'E6'} → $5.87 (feasible=True)

---

### dev-L1-64 — trap=True C*=$3.97 greedy=$5.37 (gap 140c)

**BAKED SWEET GOODS** (SW GDS:DONUTS)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| S8 | Private | 69 | 12 OZ | $1.99 | $0.49 | $1.50 |
| R1 | National | 1790 | 12 OZ | $1.99 | $0.00 | $1.99 ←bought |
| S0 | National | 1790 | 8.6 OZ | $2.99 | $0.00 | $2.99 |

**MOLASSES/SYRUP/PANCAKE MIXS** (MOLASSES & SYRUPS)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| Y6 | Private | 69 | 12 OZ | $5.29 | $1.00 | $4.29 |
| H3 | Private | 69 | 24 OZ | $1.37 | $0.00 | $1.37 |
| R7 | National | 236 | 27.6 OZ | $3.69 | $0.30 | $3.39 ←bought |

**FLUID MILK PRODUCTS** (FLUID MILK WHITE ONLY)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| Y2 | Private | 69 |   | $1.99 | $0.99 | $1.00 |
| U7 | National | 1543 | 1 GAL | $3.99 | $0.00 | $3.99 |
| T0 | Private | 69 | 1 GA | $2.49 | $0.00 | $2.49 ←bought |

**COLD CEREAL** (ADULT CEREAL)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| T3 | National | 1046 | 14.5 OZ | $2.69 | $0.69 | $2.00 |
| E3 | Private | 69 | 17.3 OZ | $1.79 | $0.29 | $1.50 |
| A1 | National | 794 | 20 OZ | $3.29 | $0.30 | $2.99 ←bought |
- coupon K0: $1.90 off SKU T3 (real)

- n_carts=81, feasible=81, optimal=1, binding=['K0']
- real cart {'BAKED SWEET GOODS': 'R1', 'MOLASSES/SYRUP/PANCAKE MIXS': 'R7', 'FLUID MILK PRODUCTS': 'T0', 'COLD CEREAL': 'A1'} → $10.86 (feasible=True)

---

### dev-L1-72 — trap=True C*=$5.17 greedy=$5.98 (gap 81c)

**CHEESE** (IWS SINGLE CHEESE)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| N1 | Private | 69 | 8OZ | $1.89 | $0.89 | $1.00 |
| C8 | National | 1126 | 12 OZ | $1.99 | $0.49 | $1.50 |
| N9 | Private | 69 | 12 OZ | $1.82 | $0.32 | $1.50 ←bought |

**BACON** (ECONOMY)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| L5 | National | 1425 | 1 LB | $3.99 | $1.49 | $2.50 ←bought |
| W9 | Private | 69 | 12 OZ | $1.99 | $0.00 | $1.99 |
| W8 | National | 1425 | 1 LB | $3.99 | $1.49 | $2.50 |

**REFRGRATD DOUGH PRODUCTS** (REFRIGERATED SPECILATY ROLLS)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| D3 | National | 236 | 12OZ | $2.29 | $0.00 | $2.29 |
| P2 | National | 236 | 7 OZ | $1.69 | $0.00 | $1.69 |
| C0 | Private | 69 | 12.4 OZ | $1.99 | $0.49 | $1.50 ←bought |

**HOT CEREAL** (GRITS)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| B1 | National | 584 | 9.6 OZ | $2.19 | $0.00 | $2.19 |
| H6 | Private | 69 | 12 OZ | $1.99 | $0.15 | $1.84 |
| D1 | National | 584 | 24 OZ | $1.49 | $0.00 | $1.49 ←bought |
- coupon K0: $1.00 off SKU P2 (real)

- n_carts=81, feasible=81, optimal=1, binding=['K0']
- real cart {'CHEESE': 'N9', 'BACON': 'L5', 'REFRGRATD DOUGH PRODUCTS': 'C0', 'HOT CEREAL': 'D1'} → $6.99 (feasible=True)