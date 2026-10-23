# Instance preview

### dev-L3-1 — trap=True C*=$6.61 greedy=$7.34 (gap 73c)

**FLUID MILK PRODUCTS** (FLUID MILK WHITE ONLY)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| H5 | Private | 69 | 1 GA | $2.49 | $0.00 | $2.49 ←bought |
| J4 | National | 927 | 64 OZ | $3.89 | $0.40 | $3.49 |
| F6 | National | 5423 |   | $1.00 | $0.00 | $1.00 |
| U4 | Private | 69 | 1 GA | $2.89 | $0.00 | $2.89 |

**CANNED JUICES** (CRANBERRY JUICE (50% AND UNDER)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| Y8 | National | 612 | 64 OZ | $3.89 | $0.00 | $3.89 |
| Z2 | Private | 69 | 64 OZ | $2.00 | $0.00 | $2.00 ←bought |
| U0 | National | 612 | 46 OZ | $2.99 | $0.00 | $2.99 |
| N3 | Private | 69 | 64 OZ | $2.00 | $0.00 | $2.00 |

**SOFT DRINKS** (ENERGY DRINK)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| M4 | National | 5363 | 16 OZ | $1.29 | $0.00 | $1.29 |
| W7 | National | 5149 | 4PK/8.3 OZ | $6.99 | $1.00 | $5.99 |
| W4 | National | 1208 | 16 OZ | $1.79 | $0.29 | $1.50 |
| E9 | National | 5149 | 8.3 OZ | $1.89 | $0.00 | $1.89 ←bought |

**TOMATOES** (TOMATOES HOTHOUSE ON THE VINE)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| F5 | National | 2 | 13 LB | $2.45 | $0.00 | $2.45 ←bought |
| Z1 | National | 2 | 8 LB | $3.32 | $0.00 | $3.32 |
| K9 | National | 2 | 13 LB | $1.82 | $0.00 | $1.82 |
| Y6 | National | 2 | 7.5 LB | $0.39 | $0.00 | $0.39 |

**SUSHI** (SUSHI - IN STORE PREPARED)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| R7 | National | 5355 | 7 OZ | $5.95 | $0.00 | $5.95 ←bought |
| Q9 | National | 5355 |   | $4.95 | $0.00 | $4.95 |
| D6 | National | 5355 | 8 OZ | $5.95 | $0.00 | $5.95 |
| U7 | National | 5355 | 1.3 OZ | $0.95 | $0.00 | $0.95 |

**COFFEE** (INSTANT COFFEE FLAVORED NO SWE)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| H7 | National | 103 | 9.5 OZ | $4.99 | $0.00 | $4.99 ←bought |
| A6 | National | 103 | 13.7 OZ | $1.99 | $0.00 | $1.99 |
| Z4 | National | 103 | 6.5 OZ | $1.99 | $0.00 | $1.99 |
| Y3 | National | 1046 | 3.9 OZ | $1.71 | $0.00 | $1.71 |
- coupon K0: $1.00 off SKU A6 (synthetic)
- coupon K1: $0.55 off SKU U4 (synthetic)
- coupon K2: $0.50 off SKU U0 (synthetic)
- coupon K3: $2.00 off SKU D6 (synthetic)
- bundle K4: $0.50 off when spend on FLUID MILK PRODUCTS, CANNED JUICES ≥ $3.12 (synthetic)
- bundle K5: $0.55 off when spend on SUSHI, SOFT DRINKS ≥ $5.83 (synthetic)
- constraint: ≥ 5 National items

- n_carts=4096, feasible=3072, optimal=3, binding=['K0', 'quota:National']
- real cart {'FLUID MILK PRODUCTS': 'H5', 'CANNED JUICES': 'Z2', 'SOFT DRINKS': 'E9', 'TOMATOES': 'F5', 'SUSHI': 'R7', 'COFFEE': 'H7'} → $18.72 (feasible=False)

---

### dev-L3-5 — trap=True C*=$23.44 greedy=$15.19 (gap -825c)

**HISPANIC** (MEXICAN SAUCESSALSAPICANTEE)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| B0 | National | 959 | 24 OZ | $3.49 | $0.00 | $3.49 |
| B8 | Private | 69 | 10 OZ | $0.99 | $0.20 | $0.79 |
| T4 | Private | 69 | 10OZ | $1.69 | $0.00 | $1.69 |
| F4 | National | 781 | 16 OZ | $2.89 | $0.89 | $2.00 ←bought |

**SEAFOOD - FROZEN** (SEAFOOD-FRZ-IQF COOKED SHRIMP)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| T7 | Private | 69 | 11 OZ | $6.99 | $2.31 | $4.68 |
| E1 | Private | 69 | 40 OZ | $32.99 | $16.00 | $16.99 |
| Z2 | Private | 69 | 17 OZ | $12.99 | $4.29 | $8.70 |
| W4 | Private | 69 | 14 OZ | $9.99 | $3.30 | $6.69 ←bought |

**DIAPERS & DISPOSABLES** (BABY DIAPERS)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| F9 | Private | 69 | 40 CT | $5.88 | $0.59 | $5.29 |
| H2 | National | 751 | 29 CT | $10.59 | $0.00 | $10.59 ←bought |
| X3 | National | 764 | 34 CT | $15.99 | $2.00 | $13.99 |
| Q5 | National | 751 | 40 CT | $15.99 | $0.00 | $15.99 |

**FLUID MILK PRODUCTS** (FLUID MILK WHITE ONLY)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| S5 | Private | 69 |   | $1.99 | $0.00 | $1.99 ←bought |
| M2 | Private | 69 |   | $1.99 | $0.00 | $1.99 |
| E0 | National | 926 | 1/2 GAL | $3.79 | $0.00 | $3.79 |
| F3 | National | 927 | 64 OZ | $3.89 | $0.00 | $3.89 |

**BEANS - CANNED GLASS & MW** (VARIETY BEANS - KIDNEY PINTO)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| E3 | National | 843 | 16 OZ | $0.92 | $0.00 | $0.92 |
| Q1 | National | 1557 | 15.5 OZ | $0.89 | $0.20 | $0.69 ←bought |
| K8 | Private | 69 | 15 OZ | $0.52 | $0.00 | $0.52 |
| T2 | Private | 69 | 15 OZ | $0.45 | $0.00 | $0.45 |

**COOKIES** (COOKIES: HOLIDAY/SPECIAL OCCAS)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| P1 | National | 784 | 10 OZ | $3.19 | $0.00 | $3.19 |
| V2 | National | 5510 | 15 OZ | $2.99 | $0.00 | $2.99 |
| L2 | National | 5510 | 10 CT | $3.00 | $0.00 | $3.00 ←bought |
| W9 | National | 5510 | 10 CT | $3.00 | $0.00 | $3.00 |
- coupon K0: $0.30 off SKU E0 (real)
- coupon K1: $1.00 off SKU S5 (synthetic)
- bundle K2: $0.50 off when spend on COOKIES, DIAPERS & DISPOSABLES ≥ $12.50 (synthetic)
- bundle K3: $0.50 off when spend on COOKIES, BEANS - CANNED GLASS & MW ≥ $3.46 (synthetic)
- constraint: ≥ 5 National items

- n_carts=4096, feasible=384, optimal=3, binding=['K0', 'K2', 'K3', 'quota:National']
- real cart {'HISPANIC': 'F4', 'SEAFOOD - FROZEN': 'W4', 'DIAPERS & DISPOSABLES': 'H2', 'FLUID MILK PRODUCTS': 'S5', 'BEANS - CANNED GLASS & MW': 'Q1', 'COOKIES': 'L2'} → $22.96 (feasible=False)

---

### dev-L3-6 — trap=True C*=$3.31 greedy=$4.03 (gap 72c)

**LUNCHMEAT** (POULTRY)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| M4 | National | 1275 | 12 OZ | $2.99 | $0.49 | $2.50 |
| L0 | Private | 69 | 10OZ | $3.29 | $0.79 | $2.50 ←bought |
| E2 | Private | 69 | 6 OZ | $1.50 | $0.00 | $1.50 |
| A1 | National | 1107 | 10 OZ | $3.59 | $1.09 | $2.50 |

**MARGARINES** (MARGARINE: TUBS AND BOWLS)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| U2 | National | 6037 | 15 OZ | $2.29 | $0.00 | $2.29 |
| U0 | Private | 69 | 45 OZ | $1.89 | $0.60 | $1.29 |
| Y8 | National | 516 | 15 OZ | $1.49 | $0.00 | $1.49 |
| G8 | National | 516 | 45 OZ | $2.13 | $0.00 | $2.13 ←bought |

**FROZEN PIZZA** (BURRITOS)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| E7 | National | 2310 | 40 OZ | $3.49 | $0.99 | $2.50 |
| L6 | National | 1862 | 5OZ | $0.34 | $0.00 | $0.34 ←bought |
| W2 | National | 1862 | 5OZ | $0.33 | $0.00 | $0.33 |
| M8 | National | 1862 | 5 OZ | $0.99 | $0.10 | $0.89 |

**CHEESE** (SHREDDED CHEESE)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| Q3 | National | 317 | 8 OZ | $2.69 | $0.69 | $2.00 ←bought |
| E1 | Private | 69 | 24 OZ | $5.99 | $2.00 | $3.99 |
| X9 | Private | 69 | 8 OZ | $1.89 | $0.22 | $1.67 |
| X3 | Private | 69 | 2 LB | $3.69 | $0.00 | $3.69 |

**BAG SNACKS** (SGL SV/VEND MACH SNACKS CHIP/P)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| V3 | National | 544 | 3.50 OZ | $0.99 | $0.00 | $0.99 |
| T5 | National | 544 | .875 OZ | $0.30 | $0.00 | $0.30 |
| D3 | National | 544 | 1 OZ | $0.30 | $0.00 | $0.30 ←bought |
| F2 | National | 544 | .625 OZ | $0.25 | $0.00 | $0.25 |

**BAKED BREAD/BUNS/ROLLS** (MAINSTREAM WHITE BREAD)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| T3 | Private | 69 | 20 OZ | $1.29 | $0.30 | $0.99 |
| J0 | National | 910 | 20 OZ | $1.69 | $0.30 | $1.39 ←bought |
| A6 | Private | 69 | 20 OZ | $1.29 | $0.30 | $0.99 |
| Q2 | National | 1237 | 20 OZ | $2.19 | $0.69 | $1.50 |
- coupon K0: $0.75 off SKU Q3 (real)
- coupon K1: $1.00 off SKU F2 (synthetic)
- coupon K2: $1.00 off SKU T3 (synthetic)
- bundle K3: $0.50 off when spend on CHEESE, BAG SNACKS ≥ $2.98 (synthetic)
- bundle K4: $1.50 off when spend on MARGARINES, LUNCHMEAT ≥ $2.98 (synthetic)
- constraint: ≥ 5 National items

- n_carts=4096, feasible=1216, optimal=4, binding=['K0', 'K1', 'K2', 'K4', 'quota:National']
- real cart {'LUNCHMEAT': 'L0', 'MARGARINES': 'G8', 'FROZEN PIZZA': 'L6', 'CHEESE': 'Q3', 'BAG SNACKS': 'D3', 'BAKED BREAD/BUNS/ROLLS': 'J0'} → $6.41 (feasible=True)

---

### dev-L3-8 — trap=True C*=$4.46 greedy=$4.92 (gap 46c)

**FRZN VEGETABLE/VEG DSH** (FRZN BAGGED VEGETABLES - PLAIN)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| G9 | National | 165 | 28 OZ | $2.49 | $0.82 | $1.67 |
| A2 | Private | 69 | 16 OZ | $1.49 | $0.00 | $1.49 ←bought |
| U6 | Private | 69 | 32 OZ | $2.49 | $0.60 | $1.89 |
| A5 | Private | 69 | 16 OZ | $1.49 | $0.49 | $1.00 |

**ANALGESICS** (PEDIATRIC ANALGESICS)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| U8 | National | 5001 |   | $5.49 | $1.90 | $3.59 |
| P4 | National | 5001 |   | $5.99 | $0.00 | $5.99 |
| A4 | Private | 69 |   | $1.85 | $0.92 | $0.93 ←bought |
| G6 | National | 4951 |   | $4.99 | $0.00 | $4.99 |

**REFRGRATD DOUGH PRODUCTS** (MISC REFRIG DOUGH PRODUCTS)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| E5 | Private | 69 | 15 OZ | $2.29 | $0.79 | $1.50 ←bought |
| B6 | National | 236 | 11 OZ | $2.49 | $0.00 | $2.49 |
| X3 | National | 978 | 11.4 OZ | $3.29 | $0.00 | $3.29 |
| C2 | Private | 69 | 14.2 OZ | $2.29 | $0.29 | $2.00 |

**DOG FOODS** (CAN DOGFD GOURMET/SUPER PREM ()
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| P2 | National | 1225 | 5.5 OZ | $0.69 | $0.14 | $0.55 |
| H7 | National | 262 | 11 OZ | $2.99 | $0.10 | $2.89 |
| D5 | National | 262 | 11 OZ | $2.99 | $0.10 | $2.89 |
| S8 | Private | 69 | 5.3OZ/PCH | $0.40 | $0.00 | $0.40 ←bought |

**SOFT DRINKS** (SFT DRNK 2 LITER BTL CARB INCL)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| A6 | Private | 69 | 2 LTR | $0.59 | $0.00 | $0.59 |
| R0 | Private | 69 | 2 LTR | $0.59 | $0.00 | $0.59 |
| D6 | National | 2224 | 2 LTR* | $1.59 | $0.25 | $1.34 |
| Q3 | Private | 69 | 2 LTR | $0.59 | $0.00 | $0.59 ←bought |

**FRZN POTATOES** (FRZN FRENCH FRIES)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| V3 | Private | 69 | 32OZ | $1.79 | $0.29 | $1.50 ←bought |
| A1 | National | 135 | 28 OZ | $2.69 | $0.40 | $2.29 |
| W0 | Private | 69 | 32OZ | $1.79 | $0.29 | $1.50 |
| Z2 | National | 135 | 22 OZ | $2.69 | $0.40 | $2.29 |
- coupon K0: $2.37 off SKU P4 (synthetic)
- coupon K1: $1.65 off SKU P2 (synthetic)
- coupon K2: $1.00 off SKU A5 (synthetic)
- coupon K3: $0.50 off SKU Z2 (synthetic)
- bundle K4: $0.40 off when spend on REFRGRATD DOUGH PRODUCTS, DOG FOODS ≥ $4.95 (synthetic)
- constraint: ≥ 3 National items

- n_carts=4096, feasible=2760, optimal=1, binding=['K1', 'K2', 'K3', 'quota:National']
- real cart {'FRZN VEGETABLE/VEG DSH': 'A2', 'ANALGESICS': 'A4', 'REFRGRATD DOUGH PRODUCTS': 'E5', 'DOG FOODS': 'S8', 'SOFT DRINKS': 'Q3', 'FRZN POTATOES': 'V3'} → $6.41 (feasible=False)

---

### dev-L3-9 — trap=True C*=$10.04 greedy=$10.80 (gap 76c)

**CHICKEN** (CHICKEN DRUMS)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| Y0 | National | 4179 |   | $2.32 | $0.00 | $2.32 ←bought |
| W5 | National | 3979 |   | $2.67 | $0.00 | $2.67 |
| H3 | National | 4320 |   | $5.68 | $0.00 | $5.68 |
| S9 | National | 4316 |   | $4.05 | $0.00 | $4.05 |

**WATER - CARBONATED/FLVRD DRINK** (NON-CRBNTD DRNKING/MNERAL WATE)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| Q4 | Private | 69 | 16.9 OZ | $2.15 | $0.90 | $1.25 |
| G1 | National | 103 | 144 OZ | $3.99 | $0.00 | $3.99 |
| Z0 | National | 2058 | GAL | $0.99 | $0.10 | $0.89 |
| M6 | National | 2224 | 20 OZ | $0.69 | $0.00 | $0.69 ←bought |

**DINNER SAUSAGE** (FRESH)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| K4 | National | 2082 | 16 OZ | $3.99 | $0.00 | $3.99 |
| Q2 | Private | 69 | 18 OZ | $3.99 | $0.99 | $3.00 ←bought |
| X6 | National | 1912 | 16 OZ | $3.29 | $0.00 | $3.29 |
| D9 | National | 665 | 14 OZ | $2.99 | $0.49 | $2.50 |

**BACON** (ECONOMY)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| M9 | National | 397 | 16 OZ | $4.39 | $1.89 | $2.50 ←bought |
| R9 | National | 1425 | 1 LB | $3.99 | $1.49 | $2.50 |
| Q0 | National | 397 | 16 OZ | $4.39 | $1.89 | $2.50 |
| B6 | Private | 69 | 12 OZ | $1.99 | $0.49 | $1.50 |

**BAKED BREAD/BUNS/ROLLS** (HOT DOG BUNS)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| S0 | Private | 69 | 11 OZ | $0.79 | $0.00 | $0.79 |
| M1 | Private | 69 | 13 OZ/8CT | $1.39 | $0.40 | $0.99 |
| E3 | National | 1102 | 12 OZ | $2.19 | $0.80 | $1.39 |
| U3 | Private | 69 | 10 OZ | $1.39 | $0.40 | $0.99 ←bought |

**CHARCOAL AND LIGHTER FLUID** (CHARCOAL)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| H9 | National | 2 | 18 LB | $7.99 | $2.00 | $5.99 |
| N7 | National | 1091 |   | $7.99 | $2.00 | $5.99 |
| Z9 | Private | 903 | 9 LBS | $4.19 | $1.19 | $3.00 |
| F2 | National | 1091 | 13.5 LB | $9.79 | $1.80 | $7.99 ←bought |
- coupon K0: $1.50 off SKU H3 (real)
- coupon K1: $1.00 off SKU W5 (real)
- bundle K2: $1.00 off when spend on BACON, DINNER SAUSAGE ≥ $4.08 (synthetic)
- bundle K3: $0.50 off when spend on DINNER SAUSAGE, BAKED BREAD/BUNS/ROLLS ≥ $4.52 (synthetic)
- constraint: ≥ 4 National items

- n_carts=4096, feasible=3240, optimal=1, binding=['K1', 'K2', 'K3', 'quota:National']
- real cart {'CHICKEN': 'Y0', 'WATER - CARBONATED/FLVRD DRINK': 'M6', 'DINNER SAUSAGE': 'Q2', 'BACON': 'M9', 'BAKED BREAD/BUNS/ROLLS': 'U3', 'CHARCOAL AND LIGHTER FLUID': 'F2'} → $16.49 (feasible=True)

---

### dev-L3-10 — trap=True C*=$5.94 greedy=$4.65 (gap -129c)

**PASTA SAUCE** (MAINSTREAM)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| C6 | National | 754 | 26 OZ | $1.66 | $0.00 | $1.66 |
| Q1 | Private | 69 | 26 OZ | $1.19 | $0.00 | $1.19 |
| D1 | National | 1251 | 14 OZ | $1.59 | $0.00 | $1.59 ←bought |
| S5 | National | 1775 | 32 OZ | $4.49 | $0.50 | $3.99 |

**PIES** (PIES: FRUIT/NUT)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| W1 | Private | 895 |   | $2.99 | $0.00 | $2.99 |
| S6 | Private | 69 |   | $6.99 | $2.00 | $4.99 |
| M8 | National | 523 |   | $3.00 | $0.00 | $3.00 |
| B3 | Private | 69 |   | $1.49 | $0.50 | $0.99 ←bought |

**SOUP** (CONDENSED SOUP)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| W6 | Private | 69 | 10.5 OZ | $0.99 | $0.10 | $0.89 |
| M4 | National | 1251 | 11.5 OZ | $1.49 | $0.49 | $1.00 ←bought |
| E0 | Private | 69 | 10.75 OZ | $0.99 | $0.00 | $0.99 |
| R0 | National | 1251 | 10.75 OZ | $1.39 | $0.00 | $1.39 |

**BEANS - CANNED GLASS & MW** (PREPARED BEANS - BAKED W/PORK)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| P1 | National | 843 | 28 OZ | $1.49 | $0.00 | $1.49 |
| G1 | National | 1276 | 15 OZ | $0.89 | $0.00 | $0.89 ←bought |
| F2 | Private | 69 | 16 OZ | $0.39 | $0.00 | $0.39 |
| C5 | National | 1276 | 28 OZ | $1.39 | $0.00 | $1.39 |

**BREAKFAST SWEETS** (SW GDS:DONUTS)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| S7 | Private | 69 | 12 OZ | $1.99 | $0.00 | $1.99 |
| U1 | National | 1790 | 12 OZ | $1.99 | $0.00 | $1.99 |
| A9 | National | 2 |   | $0.50 | $0.00 | $0.50 ←bought |
| X3 | National | 1790 | 8.6 OZ | $2.99 | $0.00 | $2.99 |

**EGGS** (EGGS - LARGE)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| Z1 | National | 2306 | 12 CT | $2.99 | $0.00 | $2.99 |
| X0 | National | 5539 | 1 DZ | $2.99 | $0.00 | $2.99 |
| W8 | Private | 69 | 1 DZ | $1.04 | $0.00 | $1.04 |
| N6 | Private | 69 | 6 CT | $0.69 | $0.00 | $0.69 ←bought |
- coupon K0: $0.50 off SKU C6 (real)
- coupon K1: $0.55 off SKU M4 (real)
- bundle K2: $0.75 off when spend on PIES, SOUP ≥ $3.04 (synthetic)
- bundle K3: $1.00 off when spend on SOUP, BREAKFAST SWEETS ≥ $2.01 (synthetic)
- constraint: ≥ 5 National items

- n_carts=4096, feasible=756, optimal=1, binding=['K0', 'K1', 'K2', 'quota:National']
- real cart {'PASTA SAUCE': 'D1', 'PIES': 'B3', 'SOUP': 'M4', 'BEANS - CANNED GLASS & MW': 'G1', 'BREAKFAST SWEETS': 'A9', 'EGGS': 'N6'} → $5.11 (feasible=False)

---

### dev-L3-11 — trap=True C*=$14.67 greedy=$15.97 (gap 130c)

**CHEESES** (CHEESE:SPECIALTY PREPACK)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| G9 | National | 6127 | 5 OZ | $3.99 | $0.00 | $3.99 ←bought |
| Y5 | National | 3764 |   | $2.97 | $0.27 | $2.70 |
| T5 | Private | 69 | 8 OZ | $5.49 | $0.00 | $5.49 |
| Z2 | National | 2220 | 6 OZ | $3.99 | $0.00 | $3.99 |

**CHEESE** (SHREDDED CHEESE)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| M2 | Private | 69 | 8 OZ | $1.78 | $0.11 | $1.67 ←bought |
| Q1 | Private | 69 | 8 OZ | $1.89 | $0.22 | $1.67 |
| A2 | National | 317 | 8 OZ | $2.79 | $1.13 | $1.66 |
| M0 | Private | 69 | 8 OZ | $1.84 | $0.17 | $1.67 |

**DIAPERS & DISPOSABLES** (BABY DIAPERS)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| G3 | National | 764 | 26 CT | $11.34 | $0.00 | $11.34 ←bought |
| C3 | Private | 69 | 52 CT | $12.99 | $0.00 | $12.99 |
| J1 | National | 751 | 68 CT | $18.99 | $1.00 | $17.99 |
| R7 | National | 751 | 21 CT | $10.59 | $1.10 | $9.49 |

**SNACKS** (SPECIALTY CRACKERS)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| Z8 | National | 1429 | 5.25 OZ | $2.19 | $0.00 | $2.19 |
| K1 | National | 159 | 10.25 OZ | $2.99 | $0.00 | $2.99 |
| C6 | National | 2483 | 3.2 OZ | $2.69 | $0.00 | $2.69 ←bought |
| E5 | Private | 69 | 8 OZ | $2.39 | $0.00 | $2.39 |

**SOFT DRINKS** (SFT DRNK 2 LITER BTL CARB INCL)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| M5 | Private | 69 | 2 LTR | $0.59 | $0.00 | $0.59 |
| M1 | National | 2224 | 2 LTR | $1.39 | $0.06 | $1.33 ←bought |
| A3 | Private | 69 | 2 LTR | $0.59 | $0.00 | $0.59 |
| H9 | Private | 69 |   | $0.59 | $0.00 | $0.59 |

**BABYFOOD** (BABY FOOD)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| F6 | National | 404 | 4 OZ | $0.79 | $0.00 | $0.79 |
| Z5 | Private | 69 | 4 OZ | $0.59 | $0.00 | $0.59 |
| H7 | Private | 69 | 4 OZ | $0.59 | $0.00 | $0.59 |
| S7 | Private | 69 | 4 OZ | $0.59 | $0.00 | $0.59 ←bought |
- coupon K0: $0.50 off SKU A2 (real)
- coupon K1: $2.00 off SKU J1 (real)
- coupon K2: $0.50 off SKU F6 (synthetic)
- coupon K3: $0.75 off SKU Y5 (synthetic)
- bundle K4: $1.00 off when spend on CHEESE, BABYFOOD ≥ $2.29 (synthetic)
- bundle K5: $2.00 off when spend on BABYFOOD, DIAPERS & DISPOSABLES ≥ $17.47 (synthetic)
- constraint: ≥ 5 National items

- n_carts=4096, feasible=297, optimal=3, binding=['K0', 'K2', 'K3', 'K4', 'quota:National']
- real cart {'CHEESES': 'G9', 'CHEESE': 'M2', 'DIAPERS & DISPOSABLES': 'G3', 'SNACKS': 'C6', 'SOFT DRINKS': 'M1', 'BABYFOOD': 'S7'} → $21.61 (feasible=False)

---

### dev-L3-12 — trap=True C*=$10.33 greedy=$10.34 (gap 1c)

**POPCORN** (POPCORN - MICROWAVE)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| U1 | Private | 69 | 1 LB | $0.59 | $0.00 | $0.59 |
| V9 | National | 194 | 10CT/3.5OZ | $5.99 | $0.00 | $5.99 |
| Y5 | National | 2034 | 3-3.5 OZ | $1.99 | $0.99 | $1.00 ←bought |
| G4 | National | 194 | 35 OZ | $5.99 | $0.00 | $5.99 |

**CHEESE** (SHREDDED CHEESE)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| J8 | Private | 69 | 8 OZ | $1.89 | $0.22 | $1.67 |
| H2 | Private | 69 | 24 OZ | $5.99 | $2.00 | $3.99 |
| W5 | National | 317 | 8 OZ | $2.99 | $0.99 | $2.00 ←bought |
| S9 | Private | 69 | 8 OZ | $1.89 | $0.22 | $1.67 |

**SALD DRSNG/SNDWCH SPRD** (SEMI-SOLID SALAD DRESSING MAY)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| Y9 | Private | 69 | 32 OZ | $2.59 | $0.59 | $2.00 |
| Y7 | National | 317 | 60 OZ | $5.69 | $0.30 | $5.39 |
| V5 | National | 1179 | 15 OZ | $2.39 | $0.00 | $2.39 |
| H7 | National | 317 | 10 OZ | $1.59 | $0.00 | $1.59 ←bought |

**FD WRAPS/BAGS/TRSH BG** (GARBAGE KITCHEN COMPACTOR BA)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| Q5 | National | 121 | 80 CT | $6.49 | $0.70 | $5.79 |
| L1 | Private | 69 | 13 GAL | $2.99 | $0.49 | $2.50 |
| R6 | Private | 69 | 13 GAL | $2.99 | $0.00 | $2.99 |
| G7 | National | 121 | 40 CT | $6.49 | $0.70 | $5.79 ←bought |

**BLEACH** (SOIL & STAIN REMOVER)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| E2 | National | 764 | 1 CT | $2.99 | $0.00 | $2.99 |
| D9 | National | 1136 | 22 OZ | $3.26 | $0.99 | $2.27 ←bought |
| Z1 | Private | 69 | 32 OZ | $1.99 | $0.00 | $1.99 |
| R8 | National | 5846 | 21.5 OZ | $3.99 | $1.00 | $2.99 |

**BAG SNACKS** (TORTILLA/NACHO CHIPS)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| W1 | National | 544 | 10 OZ | $3.49 | $0.50 | $2.99 |
| Z2 | National | 544 | 12.5 OZ | $3.49 | $0.00 | $3.49 ←bought |
| N4 | National | 2223 | 16 OZ | $2.49 | $0.49 | $2.00 |
| X8 | Private | 69 | 20 OZ | $2.99 | $0.49 | $2.50 |
- coupon K0: $0.75 off SKU W5 (real)
- coupon K1: $1.00 off SKU E2 (synthetic)
- bundle K2: $1.00 off when spend on CHEESE, SALD DRSNG/SNDWCH SPRD ≥ $6.68 (synthetic)
- bundle K3: $1.50 off when spend on SALD DRSNG/SNDWCH SPRD, CHEESE ≥ $4.60 (synthetic)
- constraint: ≥ 5 National items

- n_carts=4096, feasible=1026, optimal=1, binding=['K0', 'K1', 'quota:National']
- real cart {'POPCORN': 'Y5', 'CHEESE': 'W5', 'SALD DRSNG/SNDWCH SPRD': 'H7', 'FD WRAPS/BAGS/TRSH BG': 'G7', 'BLEACH': 'D9', 'BAG SNACKS': 'Z2'} → $15.39 (feasible=True)

---

### dev-L3-15 — trap=True C*=$10.56 greedy=$10.56 (gap 0c)

**FRZN MEAT/MEAT DINNERS** (FRZN SS PREMIUM ENTREES/DNRS/N)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| K3 | National | 1230 | 12 OZ | $3.99 | $1.99 | $2.00 ←bought |
| Y3 | National | 151 | 6.125 OZ | $3.19 | $0.19 | $3.00 |
| W1 | National | 1230 | 8.5 OZ | $2.99 | $1.32 | $1.67 |
| G5 | National | 151 | 9 OZ | $3.19 | $0.52 | $2.67 |

**COOKIES** (COOKIES: REGULAR)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| V4 | Private | 69 |   | $3.99 | $0.00 | $3.99 |
| B2 | National | 5237 | 5 OZ | $3.99 | $0.00 | $3.99 ←bought |
| E5 | Private | 69 |   | $3.99 | $0.00 | $3.99 |
| M8 | Private | 69 |   | $4.39 | $0.00 | $4.39 |

**BREAKFAST SAUSAGE/SANDWICHES** (LINKS - RAW)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| L0 | National | 2082 | 12 OZ | $3.79 | $0.80 | $2.99 |
| Y6 | National | 2219 | 9.6 OZ | $3.99 | $1.49 | $2.50 ←bought |
| U4 | Private | 69 | 12 OZ | $2.99 | $0.49 | $2.50 |
| D2 | National | 2209 | 12OZ | $3.49 | $0.50 | $2.99 |

**FLUID MILK PRODUCTS** (FLUID MILK WHITE ONLY)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| F2 | National | 1543 | 1/2 GAL | $2.39 | $0.00 | $2.39 |
| N8 | National | 1543 | 1/2 PT | $1.59 | $0.00 | $1.59 |
| C4 | Private | 69 | 1 GA | $2.69 | $0.92 | $1.77 ←bought |
| D8 | Private | 69 | 1 GA | $2.67 | $0.00 | $2.67 |

**BAKED BREAD/BUNS/ROLLS** (HAMBURGER BUNS)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| U2 | Private | 69 | 12 OZ | $0.99 | $0.00 | $0.99 |
| S9 | Private | 69 | 21 OZ | $1.59 | $0.09 | $1.50 |
| X8 | National | 1638 | 8 CT | $2.79 | $1.00 | $1.79 |
| K1 | Private | 69 | 13 OZ | $1.39 | $0.40 | $0.99 ←bought |

**CHEESE** (IWS SINGLE CHEESE)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| S7 | Private | 69 | 16 OZ | $4.99 | $2.49 | $2.50 |
| M0 | National | 317 | 16 OZ | $2.99 | $0.00 | $2.99 |
| D3 | National | 317 | 48OZ | $9.79 | $0.00 | $9.79 |
| J0 | Private | 69 | 12 OZ | $1.82 | $0.00 | $1.82 ←bought |
- coupon K0: $0.35 off SKU S7 (synthetic)
- coupon K1: $2.00 off SKU U2 (synthetic)
- bundle K2: $1.00 off when spend on FRZN MEAT/MEAT DINNERS, COOKIES ≥ $6.68 (synthetic)
- bundle K3: $1.00 off when spend on BAKED BREAD/BUNS/ROLLS, FLUID MILK PRODUCTS ≥ $4.01 (synthetic)
- constraint: ≥ 4 National items

- n_carts=4096, feasible=1632, optimal=1, binding=['K1', 'quota:National']
- real cart {'FRZN MEAT/MEAT DINNERS': 'K3', 'COOKIES': 'B2', 'BREAKFAST SAUSAGE/SANDWICHES': 'Y6', 'FLUID MILK PRODUCTS': 'C4', 'BAKED BREAD/BUNS/ROLLS': 'K1', 'CHEESE': 'J0'} → $13.07 (feasible=False)

---

### dev-L3-16 — trap=True C*=$7.26 greedy=$6.07 (gap -119c)

**CHEESE** (CREAM CHEESE)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| U2 | Private | 69 | 8 OZ | $1.69 | $0.19 | $1.50 |
| C6 | Private | 69 | 8 OZ | $1.69 | $0.19 | $1.50 |
| P5 | National | 317 | 8 OZ | $2.09 | $0.20 | $1.89 ←bought |
| U5 | National | 317 | 8 OZ | $2.29 | $0.40 | $1.89 |

**BAKED BREAD/BUNS/ROLLS** (BAGELS)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| B0 | Private | 69 | 22 OZ | $1.89 | $0.39 | $1.50 |
| Y0 | Private | 69 | 22 OZ | $1.89 | $0.39 | $1.50 ←bought |
| H7 | Private | 69 | 22 OZ | $1.89 | $0.39 | $1.50 |
| W9 | National | 159 | 17 OZ | $3.19 | $0.00 | $3.19 |

**FROZEN PIZZA** (PIZZA/TRADITIONAL)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| E9 | Private | 69 | 20.5 OZ | $3.79 | $1.29 | $2.50 |
| A7 | Private | 69 | 21.5 OZ | $3.79 | $1.29 | $2.50 |
| B3 | National | 1722 | 16 OZ | $3.65 | $0.31 | $3.34 ←bought |
| V6 | National | 1755 | 25.36 OZ | $5.99 | $0.00 | $5.99 |

**DINNER MXS:DRY** (SKILLET DINNERS)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| S7 | National | 194 | 6.2 OZ | $2.59 | $1.59 | $1.00 |
| W5 | National | 194 | 5.8 OZ | $2.59 | $1.59 | $1.00 ←bought |
| J5 | Private | 69 | 8.25 OZ | $0.99 | $0.10 | $0.89 |
| V1 | National | 194 | 6.5 OZ | $2.59 | $1.59 | $1.00 |

**FLUID MILK PRODUCTS** (FLUID MILK WHITE ONLY)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| X4 | Private | 69 | 1 GA | $2.69 | $0.00 | $2.69 |
| H2 | National | 1078 | 64 OZ | $4.39 | $0.00 | $4.39 |
| C1 | Private | 69 |   | $1.85 | $0.85 | $1.00 ←bought |
| W3 | National | 5423 |   | $0.49 | $0.00 | $0.49 |

**CANDY - CHECKLANE** (CHEWING GUM)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| H6 | National | 1445 | 1.02 OZ | $1.99 | $0.99 | $1.00 |
| F8 | National | 348 | 14 CT | $0.99 | $0.00 | $0.99 ←bought |
| Q9 | National | 117 | 9 CT | $0.99 | $0.00 | $0.99 |
| Y3 | National | 348 | 15 PC | $0.99 | $0.00 | $0.99 |
- coupon K0: $0.50 off SKU E9 (real)
- coupon K1: $0.50 off SKU A7 (real)
- coupon K2: $0.30 off SKU W3 (synthetic)
- coupon K3: $1.00 off SKU F8 (synthetic)
- bundle K4: $0.20 off when spend on CANDY - CHECKLANE, FROZEN PIZZA ≥ $4.09 (synthetic)
- bundle K5: $1.00 off when spend on CANDY - CHECKLANE, BAKED BREAD/BUNS/ROLLS ≥ $3.92 (synthetic)
- constraint: ≥ 5 National items

- n_carts=4096, feasible=704, optimal=12, binding=['K0', 'K2', 'K3', 'K5', 'quota:National']
- real cart {'CHEESE': 'P5', 'BAKED BREAD/BUNS/ROLLS': 'Y0', 'FROZEN PIZZA': 'B3', 'DINNER MXS:DRY': 'W5', 'FLUID MILK PRODUCTS': 'C1', 'CANDY - CHECKLANE': 'F8'} → $8.52 (feasible=False)

---

### dev-L3-17 — trap=True C*=$12.06 greedy=$11.83 (gap -23c)

**LUNCHMEAT** (BOLOGNA)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| N8 | National | 1094 | 8 OZ | $2.39 | $0.00 | $2.39 |
| V5 | National | 1094 | 8 OZ | $1.89 | $0.64 | $1.25 |
| D1 | National | 1094 | 16 OZ | $3.99 | $1.49 | $2.50 ←bought |
| P4 | Private | 69 | 16 OZ | $2.29 | $0.62 | $1.67 |

**CHEESE** (IWS SINGLE CHEESE)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| U4 | National | 317 | 12 OZ | $3.69 | $0.00 | $3.69 |
| J3 | National | 317 | 12 OZ | $2.19 | $0.00 | $2.19 ←bought |
| F4 | Private | 69 | 12 OZ | $1.86 | $0.61 | $1.25 |
| J5 | Private | 69 | 8OZ | $1.89 | $0.89 | $1.00 |

**COFFEE FILTERS** (COFFEE FILTERS)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| P0 | National | 1333 |   | $1.09 | $0.00 | $1.09 |
| Q4 | National | 1634 | 100 CT | $1.69 | $0.00 | $1.69 |
| F9 | Private | 69 |   | $0.99 | $0.49 | $0.50 |
| K1 | Private | 69 |   | $1.39 | $0.00 | $1.39 ←bought |

**ORAL HYGIENE PRODUCTS** (MOUTHWASH RINSES AND SPRAYS)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| A9 | Private | 69 |   | $2.99 | $0.99 | $2.00 |
| P9 | National | 118 |   | $2.99 | $0.00 | $2.99 ←bought |
| E9 | Private | 69 |   | $3.19 | $1.19 | $2.00 |
| X0 | National | 118 |   | $1.59 | $0.00 | $1.59 |

**YOGURT** (YOGURT MULTI-PACKS)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| Y4 | National | 1487 | 24 OZ | $2.79 | $0.29 | $2.50 ←bought |
| Z8 | National | 759 | 8PK/24.8OZ | $3.69 | $0.40 | $3.29 |
| P8 | National | 1487 | 20 OZ | $3.29 | $0.00 | $3.29 |
| N6 | Private | 69 | 8 CT | $2.99 | $0.30 | $2.69 |

**LAUNDRY DETERGENTS** (POWDER LAUNDRY DETERGENT)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| G8 | National | 764 | 63 LOADS | $14.49 | $4.50 | $9.99 |
| V2 | National | 764 | 31 LOADS | $6.99 | $1.00 | $5.99 |
| A3 | National | 764 | 31 LOADS | $8.04 | $0.00 | $8.04 ←bought |
| R6 | National | 764 | 31 LOADS | $7.79 | $0.00 | $7.79 |
- coupon K0: $0.50 off SKU N8 (real)
- coupon K1: $1.00 off SKU P4 (real)
- coupon K2: $1.00 off SKU Y4 (real)
- coupon K3: $0.55 off SKU N6 (real)
- bundle K4: $0.35 off when spend on YOGURT, COFFEE FILTERS ≥ $3.62 (synthetic)
- bundle K5: $1.00 off when spend on LUNCHMEAT, YOGURT ≥ $4.59 (synthetic)
- constraint: ≥ 5 National items

- n_carts=4096, feasible=1344, optimal=1, binding=['K0', 'K2', 'K5', 'quota:National']
- real cart {'LUNCHMEAT': 'D1', 'CHEESE': 'J3', 'COFFEE FILTERS': 'K1', 'ORAL HYGIENE PRODUCTS': 'P9', 'YOGURT': 'Y4', 'LAUNDRY DETERGENTS': 'A3'} → $17.26 (feasible=True)

---

### dev-L3-18 — trap=True C*=$6.00 greedy=$6.30 (gap 30c)

**REFRGRATD DOUGH PRODUCTS** (REFRIGERATED BISCUITS REGULAR)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| A2 | Private | 69 | 16 OZ | $1.29 | $0.08 | $1.21 ←bought |
| N1 | National | 236 | 16.3 OZ | $1.79 | $0.10 | $1.69 |
| Q2 | National | 236 | 16.3 OZ | $1.79 | $0.10 | $1.69 |
| Y1 | National | 236 | 16.3 OZ | $1.79 | $0.10 | $1.69 |

**BAKING MIXES** (FROSTING)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| U6 | National | 194 | 12 OZ | $2.19 | $0.69 | $1.50 |
| G7 | National | 5258 | 16 OZ | $2.19 | $0.69 | $1.50 |
| F4 | National | 194 | 12 OZ | $2.19 | $0.69 | $1.50 ←bought |
| B7 | National | 1266 | 16 OZ | $1.34 | $0.00 | $1.34 |

**EGGS** (EGGS - LARGE)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| X9 | National | 5539 | DZ | $2.29 | $0.00 | $2.29 |
| D0 | Private | 69 | 12 CT | $2.49 | $0.00 | $2.49 |
| U2 | Private | 69 | 12 CT | $1.79 | $0.00 | $1.79 |
| E9 | Private | 69 | 1 DZ | $1.09 | $0.00 | $1.09 ←bought |

**CANNED JUICES** (ASEPTIC PACK JUICE AND DRINKS)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| Z5 | National | 1046 | 10/6.75 OZ | $1.89 | $0.00 | $1.89 |
| W3 | National | 1046 | 6.75 OZ | $1.03 | $0.00 | $1.03 ←bought |
| Q9 | Private | 69 | 67.5 OZ | $1.75 | $0.18 | $1.57 |
| Q4 | National | 2557 | 67.5 OZ | $1.89 | $0.00 | $1.89 |

**BAG SNACKS** (TORTILLA/NACHO CHIPS)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| N4 | National | 544 | 13 OZ | $2.75 | $0.87 | $1.88 |
| A0 | National | 544 | 12.5 OZ | $2.75 | $0.87 | $1.88 ←bought |
| X5 | Private | 69 | 13.5OZ | $2.29 | $0.29 | $2.00 |
| S5 | Private | 69 | 20 OZ | $2.99 | $0.37 | $2.62 |

**FLUID MILK PRODUCTS** (FLUID MILK WHITE ONLY)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| Z6 | Private | 69 | 1 GA | $2.49 | $0.00 | $2.49 ←bought |
| F0 | National | 1543 | 1/2 GAL | $2.19 | $0.00 | $2.19 |
| J5 | National | 1543 | GAL | $3.99 | $0.00 | $3.99 |
| H7 | National | 5423 | 1 GA | $1.25 | $0.00 | $1.25 |
- coupon K0: $1.00 off SKU X9 (real)
- coupon K1: $1.00 off SKU W3 (synthetic)
- coupon K2: $0.50 off SKU E9 (synthetic)
- bundle K3: $1.00 off when spend on EGGS, CANNED JUICES ≥ $3.06 (synthetic)
- bundle K4: $0.75 off when spend on FLUID MILK PRODUCTS, REFRGRATD DOUGH PRODUCTS ≥ $3.68 (synthetic)
- constraint: ≥ 4 National items

- n_carts=4096, feasible=2880, optimal=2, binding=['K0', 'K1', 'K3']
- real cart {'REFRGRATD DOUGH PRODUCTS': 'A2', 'BAKING MIXES': 'F4', 'EGGS': 'E9', 'CANNED JUICES': 'W3', 'BAG SNACKS': 'A0', 'FLUID MILK PRODUCTS': 'Z6'} → $6.95 (feasible=False)

---

### dev-L3-19 — trap=True C*=$5.35 greedy=$7.85 (gap 250c)

**VEGETABLES - SHELF STABLE** (CORN)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| U7 | National | 407 | 11 OZ | $1.19 | $0.20 | $0.99 |
| J9 | National | 282 | 14.75 OZ | $1.09 | $0.30 | $0.79 |
| A7 | Private | 69 | 8.75 OZ | $0.49 | $0.00 | $0.49 |
| G6 | Private | 69 | 15.25 OZ | $0.79 | $0.29 | $0.50 ←bought |

**FROZEN PIZZA** (SNACKS/APPETIZERS)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| S6 | National | 1039 | 44.5 OZ | $8.19 | $3.20 | $4.99 ←bought |
| X5 | National | 1039 |   | $3.79 | $0.79 | $3.00 |
| P8 | National | 5697 | 3.5 LB | $13.99 | $0.00 | $13.99 |
| J0 | Private | 69 | 8 OZ | $2.69 | $0.90 | $1.79 |

**BAG SNACKS** (TORTILLA/NACHO CHIPS)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| C6 | National | 544 | 13.0 OZ | $2.75 | $0.87 | $1.88 |
| R3 | National | 544 | 20 OZ | $4.19 | $0.00 | $4.19 |
| W2 | National | 2150 | 12 OZ | $1.99 | $0.49 | $1.50 |
| U1 | Private | 69 | 13.5OZ | $2.59 | $0.59 | $2.00 ←bought |

**SOFT DRINKS** (MIXERS(TONIC WTR/GNGR ALE)FLAV)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| Z3 | National | 2224 | LTR | $1.39 | $0.00 | $1.39 |
| F7 | National | 1647 | 20 OZ | $1.29 | $0.00 | $1.29 ←bought |
| W5 | National | 2224 | 1 LTR | $1.39 | $0.00 | $1.39 |
| A2 | National | 2224 | 10 OZ | $4.69 | $0.00 | $4.69 |

**CHEESE** (SHREDDED CHEESE)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| A1 | National | 317 | 8 OZ | $2.69 | $0.00 | $2.69 ←bought |
| U3 | Private | 69 | 8 OZ | $1.78 | $0.00 | $1.78 |
| Q5 | Private | 69 | 6 OZ | $2.69 | $0.00 | $2.69 |
| C8 | National | 317 | 8 OZ | $2.69 | $0.00 | $2.69 |

**HISPANIC** (MEXICAN SAUCESSALSAPICANTEE)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| Y9 | Private | 69 | 16 OZ | $1.68 | $0.68 | $1.00 |
| B9 | National | 830 | 8 OZ | $1.49 | $0.24 | $1.25 |
| Z2 | National | 781 | 15.5 OZ | $3.49 | $0.00 | $3.49 ←bought |
| C9 | National | 781 | 15.5 OZ | $2.89 | $0.00 | $2.89 |
- coupon K0: $2.50 off SKU C8 (real)
- coupon K1: $0.25 off SKU S6 (synthetic)
- coupon K2: $1.00 off SKU Z3 (synthetic)
- bundle K3: $2.50 off when spend on HISPANIC, CHEESE ≥ $6.09 (synthetic)
- bundle K4: $0.40 off when spend on HISPANIC, FROZEN PIZZA ≥ $9.23 (synthetic)
- constraint: ≥ 4 National items

- n_carts=4096, feasible=3168, optimal=2, binding=['K0', 'K2', 'K3', 'quota:National']
- real cart {'VEGETABLES - SHELF STABLE': 'G6', 'FROZEN PIZZA': 'S6', 'BAG SNACKS': 'U1', 'SOFT DRINKS': 'F7', 'CHEESE': 'A1', 'HISPANIC': 'Z2'} → $12.21 (feasible=True)

---

### dev-L3-20 — trap=True C*=$3.75 greedy=$7.64 (gap 389c)

**VEGETABLES - SHELF STABLE** (MISCELLANEOUS VEGETABLES)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| G9 | National | 942 | 6 OZ | $3.29 | $0.30 | $2.99 |
| K2 | National | 942 | 6 OZ | $3.29 | $0.30 | $2.99 ←bought |
| W3 | Private | 69 | 6 OZ | $2.69 | $0.69 | $2.00 |
| K3 | Private | 69 | 6 OZ | $1.59 | $0.00 | $1.59 |

**ONIONS** (ONIONS SWEET (BULK&BAG))
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| J6 | National | 2 | 40 LB | $1.14 | $0.00 | $1.14 |
| B8 | National | 2 | 40 LB | $1.92 | $0.00 | $1.92 |
| U6 | National | 2 | 40 LB | $1.13 | $0.00 | $1.13 |
| B3 | National | 2 | 40 LB | $0.57 | $0.00 | $0.57 ←bought |

**SOFT DRINKS** (SOFT DRINKS 12/18&15PK CAN CAR)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| J2 | National | 2224 | 12 OZ | $4.59 | $1.59 | $3.00 |
| U2 | National | 103 | 12 OZ | $3.79 | $1.82 | $1.97 ←bought |
| W1 | Private | 69 | 12 OZ | $2.09 | $0.00 | $2.09 |
| R5 | Private | 69 | 12 OZ | $2.09 | $0.00 | $2.09 |

**CHEESE** (CREAM CHEESE)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| H0 | Private | 69 | 8-OZ 966 | $1.61 | $0.61 | $1.00 ←bought |
| E9 | National | 317 | 9 OZ | $3.62 | $0.70 | $2.92 |
| T1 | National | 317 | 16 OZ | $3.69 | $0.30 | $3.39 |
| V0 | Private | 69 | 8 OZ | $1.19 | $0.31 | $0.88 |

**BAKED BREAD/BUNS/ROLLS** (MAINSTREAM WHITE BREAD)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| Q5 | National | 1102 | 20 OZ | $2.39 | $0.89 | $1.50 |
| M8 | National | 910 | 20 OZ | $1.69 | $0.00 | $1.69 |
| W7 | Private | 69 | 20 OZ | $1.09 | $0.10 | $0.99 ←bought |
| Q7 | National | 1102 | 20 OZ | $1.69 | $0.40 | $1.29 |

**APPLES** (APPLES OTHER (BULK&BAG))
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| C4 | National | 6318 | 4 PK | $2.50 | $0.00 | $2.50 |
| A8 | National | 673 | 3 LB | $2.49 | $0.49 | $2.00 ←bought |
| H3 | National | 2 | 72CT | $2.04 | $0.00 | $2.04 |
| P6 | National | 2 |   | $1.64 | $0.00 | $1.64 |
- coupon K0: $0.55 off SKU W3 (real)
- coupon K1: $1.00 off SKU Q7 (synthetic)
- coupon K2: $1.00 off SKU Q5 (synthetic)
- bundle K3: $0.40 off when spend on ONIONS, CHEESE ≥ $2.20 (synthetic)
- bundle K4: $4.69 off when spend on CHEESE, BAKED BREAD/BUNS/ROLLS ≥ $3.34 (synthetic)
- constraint: ≥ 4 National items

- n_carts=4096, feasible=3200, optimal=1, binding=['K0', 'K1', 'K3', 'K4']
- real cart {'VEGETABLES - SHELF STABLE': 'K2', 'ONIONS': 'B3', 'SOFT DRINKS': 'U2', 'CHEESE': 'H0', 'BAKED BREAD/BUNS/ROLLS': 'W7', 'APPLES': 'A8'} → $9.52 (feasible=True)

---

### dev-L3-23 — trap=True C*=$10.04 greedy=$12.09 (gap 205c)

**DIETARY AID PRODUCTS** (LIQUID NUTRITION FOR ADULTS)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| T2 | National | 1420 | 6PK/8OZ | $8.49 | $1.00 | $7.49 |
| U5 | National | 1420 | 6PK/8OZ | $8.49 | $1.00 | $7.49 ←bought |
| A6 | Private | 69 | 8 OZ | $6.49 | $0.00 | $6.49 |
| M0 | Private | 69 | 8 OZ | $6.49 | $0.00 | $6.49 |

**SOUP** (BROTH)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| Q7 | Private | 69 | 14 OZ | $0.69 | $0.19 | $0.50 |
| M1 | National | 5150 | 8 OZ | $0.89 | $0.20 | $0.69 |
| L8 | Private | 69 | 14 OZ | $0.69 | $0.19 | $0.50 |
| A1 | National | 921 | 14 1/2 OZ | $0.99 | $0.10 | $0.89 ←bought |

**BAKED SWEET GOODS** (SW GDS:DONUTS)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| W5 | National | 304 |   | $3.69 | $0.00 | $3.69 |
| S3 | National | 1790 | 12 OZ | $1.99 | $0.00 | $1.99 ←bought |
| D2 | National | 5723 |   | $3.69 | $0.00 | $3.69 |
| X8 | Private | 69 | 12 OZ | $1.99 | $0.00 | $1.99 |

**FLUID MILK PRODUCTS** (CHOCOLATE MILK)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| U2 | Private | 69 |   | $1.99 | $0.99 | $1.00 ←bought |
| F6 | Private | 69 | 1 GA | $2.69 | $0.00 | $2.69 |
| V9 | National | 531 | 13.5 OZ | $1.49 | $0.49 | $1.00 |
| P9 | Private | 69 | 1 QT | $1.29 | $0.00 | $1.29 |

**PAPER TOWELS** (PAPER TOWELS & HOLDERS)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| T4 | National | 1011 |   | $9.99 | $2.30 | $7.69 |
| X2 | Private | 69 |   | $0.57 | $0.07 | $0.50 ←bought |
| B2 | Private | 69 | 35.8 SQ FT | $0.50 | $0.00 | $0.50 |
| Y2 | Private | 69 |   | $7.99 | $2.00 | $5.99 |

**CHEESE** (NATURAL CHEESE EXACT WT CHUNKS)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| D5 | Private | 69 | 24 OZ | $5.99 | $1.00 | $4.99 ←bought |
| B5 | National | 317 | 8 OZ | $2.79 | $1.12 | $1.67 |
| Y7 | Private | 69 | 8 OZ | $1.78 | $0.17 | $1.61 |
| L3 | National | 317 | 8 OZ | $2.79 | $1.12 | $1.67 |
- coupon K0: $1.00 off SKU L3 (real)
- coupon K1: $0.40 off SKU T4 (real)
- coupon K2: $2.50 off SKU W5 (synthetic)
- coupon K3: $0.50 off SKU V9 (synthetic)
- bundle K4: $0.45 off when spend on DIETARY AID PRODUCTS, SOUP ≥ $7.66 (synthetic)
- bundle K5: $0.35 off when spend on PAPER TOWELS, DIETARY AID PRODUCTS ≥ $7.42 (synthetic)
- constraint: ≥ 4 National items

- n_carts=4096, feasible=1040, optimal=12, binding=['K0', 'K2', 'K3', 'K4', 'K5', 'quota:National']
- real cart {'DIETARY AID PRODUCTS': 'U5', 'SOUP': 'A1', 'BAKED SWEET GOODS': 'S3', 'FLUID MILK PRODUCTS': 'U2', 'PAPER TOWELS': 'X2', 'CHEESE': 'D5'} → $16.06 (feasible=False)

---

### dev-L3-24 — trap=True C*=$4.08 greedy=$6.82 (gap 274c)

**FRZN POTATOES** (FRZN FRENCH FRIES)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| U2 | National | 135 | 28 OZ | $2.69 | $0.70 | $1.99 ←bought |
| J7 | National | 135 | 28 OZ | $2.69 | $0.70 | $1.99 |
| P3 | Private | 69 | 5LB | $3.05 | $0.26 | $2.79 |
| P2 | National | 135 | 26 OZ | $2.69 | $0.70 | $1.99 |

**FLUID MILK PRODUCTS** (FLUID MILK WHITE ONLY)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| Q6 | Private | 69 |   | $1.85 | $0.85 | $1.00 ←bought |
| R3 | Private | 69 |   | $1.85 | $0.85 | $1.00 |
| S3 | Private | 69 | 1 PT | $0.89 | $0.00 | $0.89 |
| X5 | National | 1078 | 64 OZ | $4.39 | $0.00 | $4.39 |

**BREAKFAST SAUSAGE/SANDWICHES** (LINKS - RAW)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| Y2 | Private | 69 | 12 OZ | $2.99 | $0.99 | $2.00 ←bought |
| K8 | National | 2209 | 12OZ | $3.49 | $0.00 | $3.49 |
| J9 | National | 2219 | 9.6 OZ | $3.99 | $1.49 | $2.50 |
| G3 | National | 2209 | 12OZ | $3.49 | $0.00 | $3.49 |

**PASTA SAUCE** (MAINSTREAM)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| H5 | National | 754 | 26 OZ | $1.67 | $0.00 | $1.67 ←bought |
| N3 | National | 1251 | 26 OZ | $2.39 | $0.39 | $2.00 |
| L6 | National | 1251 | 25.6 OZ | $2.39 | $0.39 | $2.00 |
| A3 | Private | 69 | 26 OZ | $1.19 | $0.00 | $1.19 |

**BAKED BREAD/BUNS/ROLLS** (MAINSTREAM WHITE BREAD)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| X0 | National | 5423 | 20 OZ | $0.75 | $0.00 | $0.75 |
| H0 | Private | 69 | 24 OZ | $1.59 | $0.59 | $1.00 ←bought |
| T4 | Private | 69 | 20 OZ | $1.29 | $0.30 | $0.99 |
| Z4 | Private | 69 | 16 OZ | $0.75 | $0.00 | $0.75 |

**BAG SNACKS** (PRETZELS)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| N9 | National | 2223 | 11 OZ | $2.59 | $0.00 | $2.59 |
| A0 | Private | 69 | 15OZ | $1.00 | $0.00 | $1.00 ←bought |
| S4 | Private | 69 | 15OZ | $1.10 | $0.10 | $1.00 |
| L0 | National | 2223 | 8 OZ | $3.49 | $0.00 | $3.49 |
- coupon K0: $1.57 off SKU J7 (real)
- coupon K1: $2.50 off SKU R3 (real)
- coupon K2: $1.00 off SKU Q6 (real)
- coupon K3: $1.00 off SKU U2 (real)
- bundle K4: $1.00 off when spend on FLUID MILK PRODUCTS, BREAKFAST SAUSAGE/SANDWICHES ≥ $3.75 (synthetic)
- bundle K5: $0.75 off when spend on BAG SNACKS, PASTA SAUCE ≥ $2.34 (synthetic)
- constraint: ≥ 4 National items

- n_carts=4096, feasible=1692, optimal=6, binding=['K0', 'K1', 'K4', 'K5', 'quota:National']
- real cart {'FRZN POTATOES': 'U2', 'FLUID MILK PRODUCTS': 'Q6', 'BREAKFAST SAUSAGE/SANDWICHES': 'Y2', 'PASTA SAUCE': 'H5', 'BAKED BREAD/BUNS/ROLLS': 'H0', 'BAG SNACKS': 'A0'} → $5.91 (feasible=False)

---

### dev-L3-26 — trap=True C*=$12.90 greedy=$11.93 (gap -97c)

**SALD DRSNG/SNDWCH SPRD** (SEMI-SOLID SALAD DRESSING MAY)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| J7 | Private | 69 | 11.25 OZ | $1.59 | $0.30 | $1.29 |
| R4 | Private | 69 | 16 OZ | $1.29 | $0.00 | $1.29 |
| D4 | National | 1179 | 10 OZ | $1.89 | $0.00 | $1.89 ←bought |
| K6 | National | 317 | 18 OZ | $2.89 | $0.00 | $2.89 |

**CRACKERS/MISC BKD FD** (SNACK CRACKERS)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| A1 | National | 1075 | 8.1 OZ | $2.99 | $0.00 | $2.99 |
| P3 | National | 1075 | 9.5 OZ | $3.09 | $0.00 | $3.09 |
| Y3 | National | 2121 | 12 OZ | $2.69 | $0.19 | $2.50 |
| Z8 | Private | 69 | 8 OZ | $1.05 | $0.00 | $1.05 ←bought |

**MEAT - MISC** (BREAST - BONELESS(IQF))
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| P1 | National | 397 | 40 OZ | $9.99 | $3.00 | $6.99 |
| C2 | Private | 69 | 40 OZ | $8.24 | $1.30 | $6.94 |
| L7 | Private | 69 | 3 LB | $8.99 | $3.00 | $5.99 ←bought |
| V6 | Private | 69 | 3 LB | $7.99 | $2.00 | $5.99 |

**COOKIES/CONES** (SANDWICH COOKIES)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| L0 | National | 1075 | 7.75 OZ | $2.79 | $0.00 | $2.79 |
| W3 | Private | 69 | 18 OZ | $2.79 | $0.81 | $1.98 |
| X2 | National | 1075 | 18 OZ | $2.68 | $0.68 | $2.00 ←bought |
| Q2 | Private | 69 | 17 OZ | $2.79 | $0.81 | $1.98 |

**CHEESE** (IWS SINGLE CHEESE)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| B0 | National | 317 | 12 OZ | $2.19 | $0.00 | $2.19 ←bought |
| N6 | National | 317 | 12 OZ | $3.69 | $0.00 | $3.69 |
| D7 | Private | 69 | 10.66 OZ | $0.98 | $0.00 | $0.98 |
| M2 | Private | 69 | 10.66 OZ | $1.29 | $0.00 | $1.29 |

**LUNCHMEAT** (PEPPERONI/SALAMI)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| X3 | National | 1161 | 7 OZ | $3.49 | $0.49 | $3.00 |
| A7 | National | 1425 | 6 OZ | $0.99 | $0.00 | $0.99 ←bought |
| Z2 | Private | 69 | 8OZ | $2.99 | $0.00 | $2.99 |
| P5 | National | 1161 | 7 OZ | $3.29 | $0.00 | $3.29 |
- coupon K0: $0.35 off SKU L7 (real)
- coupon K1: $1.00 off SKU P1 (real)
- bundle K2: $1.00 off when spend on CHEESE, LUNCHMEAT ≥ $5.58 (synthetic)
- bundle K3: $0.50 off when spend on CRACKERS/MISC BKD FD, COOKIES/CONES ≥ $5.25 (synthetic)
- constraint: ≥ 4 National items

- n_carts=4096, feasible=1712, optimal=1, binding=['K1', 'quota:National']
- real cart {'SALD DRSNG/SNDWCH SPRD': 'D4', 'CRACKERS/MISC BKD FD': 'Z8', 'MEAT - MISC': 'L7', 'COOKIES/CONES': 'X2', 'CHEESE': 'B0', 'LUNCHMEAT': 'A7'} → $13.76 (feasible=True)

---

### dev-L3-32 — trap=True C*=$8.24 greedy=$7.88 (gap -36c)

**COOKIES/CONES** (GRAHAM CRACKERS)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| S1 | National | 1075 | 14.4 OZ | $2.75 | $0.00 | $2.75 |
| N8 | Private | 69 | 15 OZ | $2.59 | $0.92 | $1.67 |
| Y3 | National | 1075 | 4.68 OZ | $2.89 | $0.00 | $2.89 |
| Y7 | National | 1075 | 13 OZ | $3.59 | $0.00 | $3.59 ←bought |

**FLUID MILK PRODUCTS** (FLUID MILK WHITE ONLY)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| M8 | Private | 69 |   | $1.87 | $0.37 | $1.50 |
| V6 | Private | 69 |   | $1.85 | $0.35 | $1.50 |
| K6 | Private | 69 | 1 GA | $2.69 | $0.00 | $2.69 ←bought |
| D9 | National | 926 | 32 OZ | $1.79 | $0.00 | $1.79 |

**SOFT DRINKS** (SOFT DRINKS 12/18&15PK CAN CAR)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| R1 | National | 2224 | 12PK/12OZ | $3.99 | $1.99 | $2.00 |
| H7 | National | 2224 | 12 OZ | $4.59 | $1.59 | $3.00 |
| A1 | National | 2224 | 12 OZ | $3.99 | $1.99 | $2.00 ←bought |
| P9 | Private | 69 | 12 OZ | $2.00 | $0.33 | $1.67 |

**BAG SNACKS** (MISC BAG SNACKS)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| F6 | National | 1890 | 3.5 OZ | $1.79 | $0.00 | $1.79 |
| Y5 | Private | 69 | 5 OZ | $1.05 | $0.00 | $1.05 |
| M2 | National | 544 | 10.5 OZ | $3.49 | $0.00 | $3.49 ←bought |
| G8 | National | 972 | 4 OZ | $1.99 | $0.20 | $1.79 |

**BEERS/ALES** (BEERALEMALT LIQUORS)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| K1 | National | 239 | 12 OZ | $11.99 | $0.00 | $11.99 |
| H2 | National | 239 | 12PK/12OZ | $8.49 | $0.00 | $8.49 ←bought |
| T0 | National | 2384 | 6PK/12OZ | $6.99 | $0.00 | $6.99 |
| D6 | National | 2232 | 24 OZ | $0.99 | $0.00 | $0.99 |

**CRACKERS/MISC BKD FD** (CHEESE CRACKERS (CHEEZ-ITS/GOL)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| P8 | National | 159 | 6.6 OZ | $1.99 | $0.99 | $1.00 ←bought |
| Y0 | National | 159 | 6.6 OZ | $1.99 | $0.99 | $1.00 |
| X8 | National | 1075 | 8 OZ | $3.69 | $0.00 | $3.69 |
| E2 | Private | 69 | 16 OZ | $1.69 | $0.02 | $1.67 |
- coupon K0: $0.50 off SKU M2 (real)
- coupon K1: $0.55 off SKU V6 (synthetic)
- bundle K2: $1.00 off when spend on SOFT DRINKS, BAG SNACKS ≥ $2.76 (synthetic)
- bundle K3: $0.30 off when spend on CRACKERS/MISC BKD FD, BEERS/ALES ≥ $11.37 (synthetic)
- constraint: ≥ 5 National items

- n_carts=4096, feasible=1728, optimal=8, binding=['K2', 'quota:National']
- real cart {'COOKIES/CONES': 'Y7', 'FLUID MILK PRODUCTS': 'K6', 'SOFT DRINKS': 'A1', 'BAG SNACKS': 'M2', 'BEERS/ALES': 'H2', 'CRACKERS/MISC BKD FD': 'P8'} → $19.76 (feasible=True)

---

### dev-L3-34 — trap=True C*=$2.94 greedy=$7.63 (gap 469c)

**SOUP** (DRY SOUP)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| L0 | National | 1002 | 3 OZ | $0.17 | $0.00 | $0.17 ←bought |
| T6 | National | 869 | 4.2 OZ/2CT | $1.49 | $0.00 | $1.49 |
| W3 | National | 869 | 2 CT | $1.29 | $0.00 | $1.29 |
| L2 | Private | 69 | 12.1 OZ | $2.99 | $0.30 | $2.69 |

**DRY NOODLES/PASTA** (SPAGHETTI DRY)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| M1 | Private | 69 | 16 OZ | $0.52 | $0.00 | $0.52 |
| J0 | Private | 69 | 1LB | $0.52 | $0.00 | $0.52 ←bought |
| C8 | National | 179 | 16OZ | $1.19 | $0.19 | $1.00 |
| M6 | Private | 69 | 16 OZ | $1.49 | $0.49 | $1.00 |

**COLD CEREAL** (KIDS CEREAL)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| A3 | National | 584 | 15 OZ | $3.99 | $1.00 | $2.99 |
| P3 | Private | 69 | 13 OZ | $1.89 | $0.00 | $1.89 |
| Q5 | Private | 69 | 14 OZ | $2.39 | $0.39 | $2.00 ←bought |
| R3 | National | 794 | 17 OZ | $3.29 | $0.79 | $2.50 |

**FLUID MILK PRODUCTS** (FLUID MILK WHITE ONLY)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| L6 | Private | 69 |   | $1.99 | $0.99 | $1.00 |
| B1 | Private | 69 | 1 GA | $2.69 | $0.00 | $2.69 |
| F0 | Private | 69 | 1 GA | $2.69 | $0.00 | $2.69 ←bought |
| R8 | National | 1543 | .5 GAL | $2.19 | $0.00 | $2.19 |

**FRZN MEAT/MEAT DINNERS** (FRZN SS PREMIUM ENTREES/DNRS/T)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| P0 | National | 320 | 14 OZ | $4.19 | $2.20 | $1.99 |
| X4 | National | 320 | 16.5 OZ | $3.79 | $1.80 | $1.99 |
| N5 | National | 151 | 11 1/2 OZ | $3.49 | $0.00 | $3.49 |
| V1 | National | 151 | 12 OZ | $2.49 | $0.15 | $2.34 ←bought |

**FROZEN MEAT** (FRZN MULTI SERVE ENTREES ALL)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| R9 | Private | 69 | 24 OZ | $5.99 | $1.00 | $4.99 |
| M8 | National | 6081 | 1.5 LB | $6.99 | $0.00 | $6.99 |
| E2 | National | 608 | 28 OZ | $2.06 | $0.00 | $2.06 |
| Q9 | National | 1508 | 28 OZ | $3.99 | $1.49 | $2.50 ←bought |
- coupon K0: $4.69 off SKU X4 (real)
- coupon K1: $0.75 off SKU R9 (real)
- coupon K2: $0.25 off SKU M8 (real)
- bundle K3: $1.00 off when spend on FRZN MEAT/MEAT DINNERS, SOUP ≥ $4.41 (synthetic)
- bundle K4: $0.50 off when spend on FROZEN MEAT, FLUID MILK PRODUCTS ≥ $8.11 (synthetic)
- constraint: ≥ 3 National items

- n_carts=4096, feasible=3472, optimal=2, binding=['K0', 'quota:National']
- real cart {'SOUP': 'L0', 'DRY NOODLES/PASTA': 'J0', 'COLD CEREAL': 'Q5', 'FLUID MILK PRODUCTS': 'F0', 'FRZN MEAT/MEAT DINNERS': 'V1', 'FROZEN MEAT': 'Q9'} → $10.22 (feasible=True)

---

### dev-L3-35 — trap=True C*=$8.46 greedy=$8.56 (gap 10c)

**CRACKERS/MISC BKD FD** (SNACK CRACKERS)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| D5 | National | 1075 | 16 OZ | $3.49 | $0.00 | $3.49 ←bought |
| R0 | National | 1075 | 8.1 OZ | $2.99 | $0.99 | $2.00 |
| H7 | Private | 69 | 9.5 OZ | $1.05 | $0.00 | $1.05 |
| U3 | National | 586 | 16 OZ | $2.59 | $1.34 | $1.25 |

**PORK** (RIBS)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| T8 | National | 2843 |   | $3.90 | $0.00 | $3.90 |
| N2 | National | 3500 |   | $17.49 | $5.85 | $11.64 |
| R9 | National | 2866 |   | $3.00 | $0.00 | $3.00 |
| V0 | National | 3456 |   | $13.40 | $3.66 | $9.74 ←bought |

**GREETING CARDS/WRAP/PARTY SPLY** (CARDS EVERYDAY)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| W3 | National | 1407 |   | $2.29 | $0.00 | $2.29 |
| S0 | National | 1407 |   | $2.99 | $0.00 | $2.99 |
| H3 | National | 1407 |   | $1.99 | $0.00 | $1.99 |
| Z7 | National | 5143 |   | $3.29 | $0.00 | $3.29 ←bought |

**CHEESE** (MISCELLANEOUS CHEESE)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| L7 | National | 995 | 6 OZ | $3.29 | $0.79 | $2.50 |
| S5 | National | 317 | 12 OZ | $2.99 | $0.00 | $2.99 ←bought |
| B7 | Private | 69 | 4 OZ | $1.99 | $0.49 | $1.50 |
| S4 | Private | 69 | 12 OZ | $3.49 | $0.99 | $2.50 |

**SOUP** (CONDENSED SOUP)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| M2 | Private | 69 | 10.5OZ | $0.69 | $0.00 | $0.69 |
| V6 | National | 1251 | 50 OZ | $3.49 | $0.00 | $3.49 |
| F4 | National | 1251 | 10.5 OZ | $1.39 | $0.00 | $1.39 |
| J4 | National | 1251 | 26 OZ | $2.19 | $0.00 | $2.19 ←bought |

**CANDY - CHECKLANE** (CANDY BARS (SINGLES)(INCLUDING)
| code | brand | mfr | size | shelf | loyalty | net |
|---|---|---|---|---|---|---|
| A5 | National | 531 | 1.5 OZ | $0.59 | $0.00 | $0.59 |
| M9 | National | 693 |   | $0.60 | $0.26 | $0.34 |
| Z4 | National | 693 | 1.4 OZ | $0.69 | $0.36 | $0.33 ←bought |
| S6 | National | 693 | 1.45 OZ | $0.60 | $0.26 | $0.34 |
- coupon K0: $0.50 off SKU R0 (synthetic)
- coupon K1: $0.50 off SKU S4 (synthetic)
- bundle K2: $1.00 off when spend on CANDY - CHECKLANE, SOUP ≥ $1.51 (synthetic)
- bundle K3: $2.50 off when spend on SOUP, PORK ≥ $12.11 (synthetic)
- constraint: ≥ 5 National items

- n_carts=4096, feasible=3072, optimal=3, binding=['K2', 'quota:National']
- real cart {'CRACKERS/MISC BKD FD': 'D5', 'PORK': 'V0', 'GREETING CARDS/WRAP/PARTY SPLY': 'Z7', 'CHEESE': 'S5', 'SOUP': 'J4', 'CANDY - CHECKLANE': 'Z4'} → $21.03 (feasible=True)