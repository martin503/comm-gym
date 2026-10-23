import pandas as pd

from commgym.dunnhumby.clean import clean_transactions, derive_unit_prices
from commgym.dunnhumby.config import CleaningConfig
from commgym.dunnhumby.load import Product, load_products

PRODUCT_CSV = (
    'PRODUCT_ID,MANUFACTURER,DEPARTMENT,BRAND,COMMODITY_DESC,SUB_COMMODITY_DESC,CURR_SIZE_OF_PRODUCT\n'
    '101,2,GROCERY,National,SOFT DRINKS,COLA,12 OZ\n'
    '102,3,GROCERY,Private,BAG SNACKS,CHIPS,10 OZ\n'
    '103,,GROCERY,National,SALAD BAR,MISC,\n'
    '104,4,KIOSK-GAS,Private,GAS,GAS,1 GAL\n'
)


def test_load_products_drops_invalid_rows(tmp_path):
    (tmp_path / 'product.csv').write_text(PRODUCT_CSV)
    products = load_products(tmp_path)
    assert {
        'ids': sorted(p.product_id for p in products),
        'brands': sorted(p.brand.value for p in products),
        'commodity_of_102': next(p.commodity for p in products if p.product_id == 102),
    } == {
        'ids': [101, 102, 104],
        'brands': ['National', 'Private', 'Private'],
        'commodity_of_102': 'BAG SNACKS',
    }


def test_derive_unit_prices_matches_user_guide_definition():
    tx = pd.DataFrame(
        {
            'SALES_VALUE': [0.79],
            'RETAIL_DISC': [-0.60],
            'COUPON_DISC': [-0.15],
            'COUPON_MATCH_DISC': [0.0],
            'QUANTITY': [1],
        }
    )
    out = derive_unit_prices(tx)
    assert {
        'regular': round(float(out['regular_unit'].iloc[0]), 2),
        'loyalty': round(float(out['loyalty_unit'].iloc[0]), 2),
    } == {'regular': 1.54, 'loyalty': 0.94}


def _product(pid: int, dept: str, commodity: str) -> Product:
    return Product.model_validate(
        {
            'PRODUCT_ID': pid,
            'MANUFACTURER': 1,
            'DEPARTMENT': dept,
            'BRAND': 'Private',
            'COMMODITY_DESC': commodity,
            'SUB_COMMODITY_DESC': '',
            'CURR_SIZE_OF_PRODUCT': '',
        }
    )


def test_clean_transactions_counts_each_rule():
    products = [
        _product(101, 'GROCERY', 'SOFT DRINKS'),
        _product(104, 'KIOSK-GAS', 'GAS'),
        _product(105, 'GROCERY', 'NO COMMODITY DESCRIPTION'),
    ]
    tx = pd.DataFrame(
        {
            'household_key': [1] * 7,
            'BASKET_ID': [10] * 7,
            'DAY': [5] * 7,
            'PRODUCT_ID': [101, 101, 101, 104, 105, 101, 999],
            'QUANTITY': [1, 0, 1, 1, 1, 20, 1],
            'SALES_VALUE': [1.39, 1.00, 0.0, 3.00, 2.00, 5.00, 1.00],
            'STORE_ID': [364] * 7,
            'RETAIL_DISC': [0.0] * 7,
            'TRANS_TIME': [0] * 7,
            'WEEK_NO': [1] * 7,
            'COUPON_DISC': [0.0] * 7,
            'COUPON_MATCH_DISC': [0.0] * 7,
        }
    )
    cleaned, report = clean_transactions(tx, products, CleaningConfig())
    assert {
        'dropped': report.dropped,
        'kept_products': cleaned['PRODUCT_ID'].tolist(),
        'n_input': report.n_input,
    } == {
        'dropped': {
            'unknown_product': 1,
            'nonpositive_quantity': 1,
            'nonpositive_sales_value': 1,
            'excluded_department': 1,
            'excluded_commodity': 1,
            'quantity_outlier': 1,
        },
        'kept_products': [101],
        'n_input': 7,
    }
