import pandas as pd

from commgym.dunnhumby.config import SplitsConfig
from commgym.dunnhumby.splits import build_splits, select_heldout_commodities


def _txc(n_households: int) -> pd.DataFrame:
    rows = []
    for household in range(1, n_households + 1):
        for week in (38, 45):
            rows.append(
                {
                    'household_key': household,
                    'BASKET_ID': household * 100 + week,
                    'DAY': week * 7,
                    'WEEK_NO': week,
                    'SALES_VALUE': float(household),
                    'commodity': 'CAT-1',
                    'brand': 'National',
                }
            )
    return pd.DataFrame(rows)


def _coverage() -> pd.DataFrame:
    rows = [
        {'commodity': commodity, 'WEEK_NO': week, 'n_skus': 5}
        for commodity in ('CAT-1', 'CAT-2', 'CAT-3')
        for week in range(1, 13)
    ]
    rows += [{'commodity': 'CAT-4', 'WEEK_NO': week, 'n_skus': 1} for week in range(1, 13)]
    return pd.DataFrame(rows)


def test_build_splits_cohorts_disjoint_and_windows_correct():
    cfg = SplitsConfig(cutoff_week=41)
    splits = build_splits(_txc(10), {1}, _coverage(), cfg)
    cohort_a = splits.train.households
    cohort_b = splits.eval_unseen.households
    assert {
        'disjoint': not (cohort_a & cohort_b),
        'covers_all_households': len(cohort_a | cohort_b) == 10,
        'cohort_b_minority': 1 <= len(cohort_b) <= 3,
        'train_weeks': (splits.train.first_week, splits.train.last_week),
        'dev_weeks': (splits.dev.first_week, splits.dev.last_week),
        'eval_weeks': (splits.eval_unseen.first_week, splits.eval_unseen.last_week),
        'eval_known_matches_cohort_a': splits.eval_known.households == cohort_a,
    } == {
        'disjoint': True,
        'covers_all_households': True,
        'cohort_b_minority': True,
        'train_weeks': (32, 41),
        'dev_weeks': (32, 41),
        'eval_weeks': (42, 45),
        'eval_known_matches_cohort_a': True,
    }


def test_heldout_selection_is_deterministic_and_eligibility_gated():
    cfg = SplitsConfig()
    first = select_heldout_commodities(_coverage(), cfg)
    second = select_heldout_commodities(_coverage(), cfg)
    # 3 eligible commodities (CAT-4 never reaches 4 SKUs), share 0.2 -> round(0.6) = 1 held out
    assert {
        'deterministic': first == second,
        'n_held': len(first),
        'gated': 'CAT-4' not in first,
    } == {
        'deterministic': True,
        'n_held': 1,
        'gated': True,
    }


def test_price_table_medians_by_hand():
    from commgym.dunnhumby.config import PricingConfig
    from commgym.dunnhumby.prices import PricePoint, build_price_table

    txc = pd.DataFrame(
        {
            'PRODUCT_ID': [101, 101, 101, 102],
            'WEEK_NO': [40, 40, 40, 40],
            'regular_unit': [2.00, 2.40, 2.00, 3.00],
            'loyalty_unit': [2.00, 2.20, 2.00, 2.80],
        }
    )
    table = build_price_table(txc, PricingConfig())
    assert table == {(101, 40): PricePoint(200, 0, 3), (102, 40): PricePoint(300, 20, 1)}
