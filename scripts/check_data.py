import argparse
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from loguru import logger
from tqdm import tqdm

from commgym.core.config import load_config
from commgym.core.logging import setup_logging
from commgym.dunnhumby.clean import CleaningReport, prepare_transactions
from commgym.dunnhumby.config import CleaningConfig, DataChecksConfig, SplitsConfig
from commgym.dunnhumby.load import data_dir as default_data_dir
from commgym.dunnhumby.load import (
    iter_causal_chunks,
    load_campaign_targeting,
    load_campaigns,
    load_coupon_eligibility,
    load_coupon_redemptions,
    load_demographics,
    load_products,
    load_transactions,
)
from commgym.dunnhumby.splits import eligible_commodities, select_heldout_commodities


@dataclass(frozen=True, slots=True)
class CheckResult:
    name: str
    markdown: str
    go: bool | None  # None = report-only


@dataclass(frozen=True, slots=True)
class Dataset:
    root: Path
    tx: pd.DataFrame
    txc: pd.DataFrame  # cleaned + derived unit prices + product attributes
    cleaning_report: CleaningReport
    coverage: pd.DataFrame  # (commodity, WEEK_NO) -> n priced SKUs
    store_coverage: pd.DataFrame  # (STORE_ID, commodity, WEEK_NO) -> n priced SKUs
    products: pd.DataFrame
    campaigns: pd.DataFrame
    coupons: pd.DataFrame
    targeting: pd.DataFrame
    redemptions: pd.DataFrame
    demographics: pd.DataFrame
    cfg: DataChecksConfig


def main() -> None:
    args = _parse_args()
    setup_logging()
    cfg = load_config(DataChecksConfig, args.config)
    cleaning_cfg = load_config(CleaningConfig, args.cleaning_config)
    root = args.data_dir if args.data_dir is not None else default_data_dir()
    logger.info('loading dataset from {}', root.resolve())
    d = _load_dataset(root, cleaning_cfg, cfg)
    checks: list[Callable[[Dataset], CheckResult]] = [
        check_schema,
        check_price_derivation,
        check_exclusions,
        check_price_coverage,
        check_price_spread,
        check_menu_scope,
        check_coupon_coverage,
        check_coupon_amounts,
        check_brand_tier,
        check_basket_categories,
        check_entry_ramp,
        check_heldout_commodities,
        check_split_balance,
    ]
    results = []
    for check in tqdm(checks, desc='data checks', unit='check'):
        results.append(check(d))
    if args.with_causal:
        results.append(check_causal(root))
    _write_report(results, args.out, root)
    _log_summary(results, args.out)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Run dunnhumby data checks and write a go/no-go report'
    )
    parser.add_argument('--data-dir', type=Path, default=None)
    parser.add_argument('--config', type=Path, default=Path('configs/data_checks.yaml'))
    parser.add_argument('--cleaning-config', type=Path, default=Path('configs/data.yaml'))
    parser.add_argument('--out', type=Path, default=Path('reports/data_checks.md'))
    parser.add_argument(
        '--with-causal', action='store_true', help='also scan causal_data.csv (664 MB)'
    )
    return parser.parse_args()


def _load_dataset(root: Path, cleaning_cfg: CleaningConfig, cfg: DataChecksConfig) -> Dataset:
    logger.info('loading reference tables')
    products = pd.DataFrame([p.model_dump() for p in load_products(root)])
    campaigns = pd.DataFrame([c.model_dump() for c in load_campaigns(root)])
    targeting = pd.DataFrame([t.model_dump() for t in load_campaign_targeting(root)])
    coupons = pd.DataFrame([c.model_dump() for c in load_coupon_eligibility(root)])
    redemptions = pd.DataFrame([r.model_dump() for r in load_coupon_redemptions(root)])
    demographics = pd.DataFrame([h.model_dump() for h in load_demographics(root)])
    logger.info('loading transactions (2.6M rows)')
    tx = load_transactions(root)
    logger.info('cleaning transactions')
    txc, report = prepare_transactions(tx, load_products(root), cleaning_cfg)
    coverage = (
        txc.groupby(['commodity', 'WEEK_NO']).agg(n_skus=('PRODUCT_ID', 'nunique')).reset_index()
    )
    store_coverage = (
        txc.groupby(['STORE_ID', 'commodity', 'WEEK_NO'])
        .agg(n_skus=('PRODUCT_ID', 'nunique'))
        .reset_index()
    )
    return Dataset(
        root,
        tx,
        txc,
        report,
        coverage,
        store_coverage,
        products,
        campaigns,
        coupons,
        targeting,
        redemptions,
        demographics,
        cfg,
    )


def check_schema(d: Dataset) -> CheckResult:
    e = d.cfg.expectations
    n_households = int(d.tx['household_key'].nunique())
    day_min, day_max = int(d.tx['DAY'].min()), int(d.tx['DAY'].max())
    week_min, week_max = int(d.tx['WEEK_NO'].min()), int(d.tx['WEEK_NO'].max())
    rows = [
        {'metric': 'rows', 'value': len(d.tx), 'expected': '—'},
        {'metric': 'households', 'value': n_households, 'expected': e.n_households},
        {'metric': 'baskets', 'value': int(d.tx['BASKET_ID'].nunique()), 'expected': '—'},
        {
            'metric': 'DAY range',
            'value': f'{day_min}–{day_max}',
            'expected': f'{e.min_day}–{e.max_day}',
        },
        {
            'metric': 'WEEK_NO range',
            'value': f'{week_min}–{week_max}',
            'expected': f'{e.min_week}–{e.max_week}',
        },
        {'metric': 'stores', 'value': int(d.tx['STORE_ID'].nunique()), 'expected': '—'},
    ]
    go = (
        n_households == e.n_households
        and e.min_day <= day_min
        and day_max <= e.max_day
        and e.min_week <= week_min
        and week_max <= e.max_week
    )
    return CheckResult('Schema and ranges', _table(rows), go)


def check_price_derivation(d: Dataset) -> CheckResult:
    eps = 1e-9
    valid = (d.txc['regular_unit'] >= d.txc['loyalty_unit'] - eps) & (d.txc['loyalty_unit'] > eps)
    share = float(valid.mean())
    rows = [
        {
            'metric': 'share regular ≥ loyalty > 0',
            'value': f'{share:.4%}',
            'expected': f'≥ {d.cfg.derivation_min_valid_share:.0%}',
        },
        {
            'metric': 'median regular unit price',
            'value': f'${d.txc["regular_unit"].median():.2f}',
            'expected': '—',
        },
        {
            'metric': 'median loyalty unit price',
            'value': f'${d.txc["loyalty_unit"].median():.2f}',
            'expected': '—',
        },
        {
            'metric': 'share of lines with loyalty discount',
            'value': f'{(d.tx["RETAIL_DISC"] < 0).mean():.2%}',
            'expected': '—',
        },
    ]
    return CheckResult(
        'Discount signs and price derivation',
        _table(rows),
        share >= d.cfg.derivation_min_valid_share,
    )


def check_exclusions(d: Dataset) -> CheckResult:
    r = d.cleaning_report
    rows = [{'rule': name, 'rows dropped': count} for name, count in r.dropped.items()]
    rows.append({'rule': '**kept**', 'rows dropped': r.n_kept})
    keep_share = r.n_kept / r.n_input
    rows.append({'rule': 'kept share', 'rows dropped': f'{keep_share:.2%}'})
    return CheckResult('Exclusions', _table(rows), None)


def check_price_coverage(d: Dataset) -> CheckResult:
    min_skus = d.cfg.price_coverage_min_skus
    observed = d.coverage[d.coverage['n_skus'] > 0]
    share = float((observed['n_skus'] >= min_skus).mean())
    store_observed = d.store_coverage[d.store_coverage['n_skus'] > 0]
    store_share = float((store_observed['n_skus'] >= min_skus).mean())
    rows = [
        {'metric': 'commodity-week pairs observed', 'value': len(observed), 'expected': '—'},
        {
            'metric': f'pairs with ≥ {min_skus} priced SKUs (chain)',
            'value': f'{share:.2%}',
            'expected': f'≥ {d.cfg.price_coverage_min_pair_share:.0%}',
        },
        {
            'metric': 'median priced SKUs per pair',
            'value': _scalar(observed['n_skus'].median()),
            'expected': '—',
        },
        {
            'metric': f'store-commodity-week pairs with ≥ {min_skus} SKUs',
            'value': f'{store_share:.2%}',
            'expected': 'feeds store- vs chain-level pricing decision',
        },
        {
            'metric': 'commodities ever reaching the minimum',
            'value': int(observed.loc[observed['n_skus'] >= min_skus, 'commodity'].nunique()),
            'expected': '—',
        },
    ]
    return CheckResult(
        'Price coverage', _table(rows), share >= d.cfg.price_coverage_min_pair_share
    )


def check_price_spread(d: Dataset) -> CheckResult:
    grouped = d.txc.groupby(['commodity', 'WEEK_NO'])['regular_unit'].agg(['mean', 'std'])
    cv = (grouped['std'] / grouped['mean']).dropna()
    median_cv = float(cv.median())
    tier = d.txc.groupby(['commodity', 'brand'])['regular_unit'].median().unstack('brand').dropna()
    premium = (tier['National'] - tier['Private']) / tier['Private']
    rows = [
        {
            'metric': 'median within-pair CV of unit price',
            'value': f'{median_cv:.4f}',
            'expected': f'≥ {d.cfg.price_spread_min_median_cv}',
        },
        {
            'metric': 'p90 within-pair CV',
            'value': f'{float(cv.quantile(0.9)):.4f}',
            'expected': '—',
        },
        {'metric': 'commodities with both tiers priced', 'value': len(tier), 'expected': '—'},
        {
            'metric': 'median National vs Private premium',
            'value': f'{float(premium.median()):.2%}',
            'expected': '—',
        },
        {
            'metric': 'share of commodities where National is pricier',
            'value': f'{float((premium > 0).mean()):.2%}',
            'expected': '—',
        },
    ]
    return CheckResult(
        'Within-category price spread', _table(rows), median_cv >= d.cfg.price_spread_min_median_cv
    )


def check_menu_scope(d: Dataset) -> CheckResult:
    """Commodity- vs sub-commodity-scoped menus: feasibility, spread, and tier mix."""
    min_skus = d.cfg.price_coverage_min_skus
    comp_pairs = (
        d.txc.groupby(['commodity', 'WEEK_NO']).agg(n=('PRODUCT_ID', 'nunique')).reset_index()
    )
    sub_pairs = (
        d.txc.groupby(['sub_commodity', 'WEEK_NO']).agg(n=('PRODUCT_ID', 'nunique')).reset_index()
    )
    comp_lines = d.txc.merge(comp_pairs, on=['commodity', 'WEEK_NO'])
    sub_lines = d.txc.merge(sub_pairs, on=['sub_commodity', 'WEEK_NO'])
    n_baskets = d.txc['BASKET_ID'].nunique()
    comp_cv = _cv_by(d.txc, ['commodity', 'WEEK_NO'])
    sub_cv = _cv_by(d.txc, ['sub_commodity', 'WEEK_NO'])
    comp_prem = _premium_by(d.txc, 'commodity')
    sub_prem = _premium_by(d.txc, 'sub_commodity')
    rows = [
        _scope_row('pairs observed', len(comp_pairs), len(sub_pairs)),
        _scope_row(
            f'share of pairs with ≥ {min_skus} priced SKUs',
            f'{_scalar((comp_pairs["n"] >= min_skus).mean()):.2%}',
            f'{_scalar((sub_pairs["n"] >= min_skus).mean()):.2%}',
        ),
        _scope_row(
            'median priced SKUs per pair',
            _scalar(comp_pairs['n'].median()),
            _scalar(sub_pairs['n'].median()),
        ),
        _scope_row(
            'share of lines in a feasible group',
            f'{_scalar((comp_lines["n"] >= min_skus).mean()):.2%}',
            f'{_scalar((sub_lines["n"] >= min_skus).mean()):.2%}',
        ),
        _scope_row(
            'share of baskets with ≥ 4 feasible categories',
            f'{_basket_share(comp_lines, n_baskets, min_skus, 4):.2%}',
            f'{_basket_share(sub_lines, n_baskets, min_skus, 4):.2%}',
        ),
        _scope_row(
            'share of baskets with ≥ 8 feasible categories',
            f'{_basket_share(comp_lines, n_baskets, min_skus, 8):.2%}',
            f'{_basket_share(sub_lines, n_baskets, min_skus, 8):.2%}',
        ),
        _scope_row(
            'median within-pair price CV',
            f'{_scalar(comp_cv.median()):.4f}',
            f'{_scalar(sub_cv.median()):.4f}',
        ),
        _scope_row(
            'p90 within-pair price CV',
            f'{_scalar(comp_cv.quantile(0.9)):.4f}',
            f'{_scalar(sub_cv.quantile(0.9)):.4f}',
        ),
        _scope_row('groups with both tiers priced', len(comp_prem), len(sub_prem)),
        _scope_row(
            'median National vs Private premium',
            f'{_scalar(comp_prem.median()):.2%}',
            f'{_scalar(sub_prem.median()):.2%}',
        ),
    ]
    return CheckResult('Menu scope: commodity vs sub-commodity', _table(rows), None)


def _scope_row(metric: str, commodity: object, sub_commodity: object) -> dict[str, object]:
    return {'metric': metric, 'commodity scope': commodity, 'sub-commodity scope': sub_commodity}


def _cv_by(txc: pd.DataFrame, keys: list[str]) -> pd.Series:
    grouped = txc.groupby(keys)['regular_unit'].agg(['mean', 'std'])
    return (grouped['std'] / grouped['mean']).dropna()


def _premium_by(txc: pd.DataFrame, key: str) -> pd.Series:
    tier = txc.groupby([key, 'brand'])['regular_unit'].median().unstack('brand').dropna()
    return (tier['National'] - tier['Private']) / tier['Private']


def _basket_share(lines: pd.DataFrame, n_baskets: int, min_skus: int, c: int) -> float:
    ok_cats = lines[lines['n'] >= min_skus].groupby('BASKET_ID')['commodity'].nunique()
    return float((ok_cats >= c).sum() / n_baskets)


def check_coupon_coverage(d: Dataset) -> CheckResult:
    weekly = _weekly_coupon_coverage(d)
    window = weekly[weekly['week'] >= _week_of(d.cfg.campaign_window_start_day)]
    n_eligible = int(
        d.coupons.merge(d.products[['product_id', 'commodity']], on='product_id')[
            'commodity'
        ].nunique()
    )
    coverage_share = float((window['n_eligible_commodities'] / n_eligible).mean())
    cutoff = suggest_cutoff_week(d.campaigns, d.cfg)
    early = window[window['week'] <= cutoff]
    late = window[window['week'] > cutoff]
    rows = [
        {
            'metric': 'first campaign week',
            'value': _week_of(int(d.campaigns['start_day'].min())),
            'expected': '—',
        },
        {
            'metric': 'last campaign week',
            'value': _week_of(int(d.campaigns['end_day'].max())),
            'expected': '—',
        },
        {
            'metric': 'commodities with any live coupon eligibility',
            'value': n_eligible,
            'expected': '—',
        },
        {
            'metric': 'window weeks with ≥ 1 live campaign',
            'value': int((window['n_live'] > 0).sum()),
            'expected': '—',
        },
        {
            'metric': 'mean share of eligible commodities covered per window week',
            'value': f'{coverage_share:.2%}',
            'expected': '—',
        },
        {
            'metric': f'median eligible commodities per week, early (≤ w{cutoff})',
            'value': int(early['n_eligible_commodities'].median()),
            'expected': '—',
        },
        {
            'metric': f'median eligible commodities per week, late (> w{cutoff})',
            'value': int(late['n_eligible_commodities'].median()),
            'expected': '—',
        },
    ]
    return CheckResult('Coupon coverage over time', _table(rows), None)


def check_coupon_amounts(d: Dataset) -> CheckResult:
    amounts = d.tx.loc[d.tx['COUPON_DISC'] < 0, 'COUPON_DISC'].abs()
    match = d.tx.loc[d.tx['COUPON_MATCH_DISC'] < 0, 'COUPON_MATCH_DISC'].abs()
    rows = [
        {
            'metric': 'lines with COUPON_DISC',
            'value': len(amounts),
            'expected': f'≥ {d.cfg.coupon_amounts_min_lines}',
        },
        {'metric': 'lines with COUPON_MATCH_DISC', 'value': len(match), 'expected': '—'},
    ]
    for q in (0.05, 0.25, 0.50, 0.75, 0.95):
        rows.append(
            {
                'metric': f'COUPON_DISC q{q:.2f}',
                'value': f'${float(amounts.quantile(q)):.2f}',
                'expected': '—',
            }
        )
    return CheckResult(
        'Empirical coupon amounts', _table(rows), len(amounts) >= d.cfg.coupon_amounts_min_lines
    )


def check_brand_tier(d: Dataset) -> CheckResult:
    def _share(part: pd.DataFrame) -> pd.Series:
        lines = part.groupby('household_key').size()
        private = part[part['brand'] == 'Private'].groupby('household_key').size()
        return (private / lines).fillna(0.0)

    overall, year1 = _share(d.txc), _share(d.txc[d.txc['WEEK_NO'] <= 52])
    rows = []
    for label, s in [('all weeks', overall), ('weeks ≤ 52 (early period)', year1)]:
        rows += [
            {
                'metric': f'private share mean ({label})',
                'value': f'{float(s.mean()):.3f}',
                'expected': '—',
            },
            {
                'metric': f'private share std across households ({label})',
                'value': f'{float(s.std()):.3f}',
                'expected': '—',
            },
            {
                'metric': f'private share p10 / p90 ({label})',
                'value': f'{float(s.quantile(0.1)):.3f} / {float(s.quantile(0.9)):.3f}',
                'expected': '—',
            },
            {
                'metric': f'households with zero private lines ({label})',
                'value': f'{float((s == 0).mean()):.2%}',
                'expected': '—',
            },
        ]
    return CheckResult('Household brand-tier share', _table(rows), None)


def check_basket_categories(d: Dataset) -> CheckResult:
    per_basket = d.txc.groupby('BASKET_ID')['commodity'].nunique()
    rows = [
        {'metric': 'baskets', 'value': len(per_basket), 'expected': '—'},
        {
            'metric': 'median commodities per basket',
            'value': _scalar(per_basket.median()),
            'expected': '—',
        },
        {
            'metric': 'p90 commodities per basket',
            'value': _scalar(per_basket.quantile(0.9)),
            'expected': '—',
        },
    ]
    for c in (4, 5, 6, d.cfg.max_categories):
        rows.append(
            {
                'metric': f'share of baskets with ≥ {c} commodities',
                'value': f'{_scalar((per_basket >= c).mean()):.2%}',
                'expected': f'≥ {d.cfg.basket_min_share_at_max_categories:.0%}'
                f' at C={d.cfg.max_categories}',
            }
        )
    go = (
        _scalar((per_basket >= d.cfg.max_categories).mean())
        >= d.cfg.basket_min_share_at_max_categories
    )
    return CheckResult('Basket category counts', _table(rows), go)


def check_entry_ramp(d: Dataset) -> CheckResult:
    active = d.tx.groupby('WEEK_NO')['household_key'].nunique()
    steady = active.max() * d.cfg.ramp_steady_state_share
    first_steady = int(_scalar(active[active >= steady].index.min()))
    camp_start = _week_of(d.cfg.campaign_window_start_day)
    cutoff = suggest_cutoff_week(d.campaigns, d.cfg)
    last_week = int(d.tx['WEEK_NO'].max())
    rows = [
        {
            'metric': 'max active households in a week',
            'value': int(_scalar(active.max())),
            'expected': '—',
        },
        {'metric': 'first week at steady state', 'value': first_steady, 'expected': '—'},
        {'metric': 'campaign window start week', 'value': camp_start, 'expected': '—'},
        {'metric': 'suggested cutoff week (window midpoint)', 'value': cutoff, 'expected': '—'},
        {
            'metric': f'window weeks early/late at cutoff {cutoff}',
            'value': f'{cutoff - camp_start + 1} / {last_week - cutoff}',
            'expected': '—',
        },
    ]
    go = first_steady < camp_start
    return CheckResult('Entry ramp and campaign-window cutoff', _table(rows), go)


def check_heldout_commodities(d: Dataset) -> CheckResult:
    splits_cfg = SplitsConfig(
        heldout_min_skus=d.cfg.price_coverage_min_skus,
        heldout_min_weeks=d.cfg.heldout_min_weeks,
        heldout_commodity_share=d.cfg.heldout_commodity_share,
        heldout_seed=d.cfg.heldout_seed,
    )
    eligible = eligible_commodities(
        d.coverage, splits_cfg.heldout_min_skus, splits_cfg.heldout_min_weeks
    )
    held = select_heldout_commodities(d.coverage, splits_cfg)
    per_basket = (
        d.txc[d.txc['commodity'].isin(eligible)].groupby('BASKET_ID')['commodity'].agg(set)
    )
    n_held_per_basket = per_basket.map(lambda s: len(s & set(held)))
    rows = [
        {
            'metric': 'eligible commodities (≥ min SKUs in ≥ 10 weeks)',
            'value': len(eligible),
            'expected': '—',
        },
        {'metric': 'held-out commodities', 'value': len(held), 'expected': '—'},
        {
            'metric': 'share of baskets with ≥ 1 held-out commodity',
            'value': f'{_scalar((n_held_per_basket >= 1).mean()):.2%}',
            'expected': '—',
        },
        {
            'metric': 'share of baskets with ≥ C=8 held-out (all-held-out rule)',
            'value': f'{_scalar((n_held_per_basket >= 8).mean()):.2%}',
            'expected': '—',
        },
        {
            'metric': 'median held-out commodities per basket',
            'value': _scalar(n_held_per_basket.median()),
            'expected': '—',
        },
    ]
    return CheckResult('Held-out commodity feasibility', _table(rows), None)


def check_split_balance(d: Dataset) -> CheckResult:
    """Window-only balance: instance anchors come from campaign-live weeks only (≥ week 32)."""
    cutoff = suggest_cutoff_week(d.campaigns, d.cfg)
    window_start = _week_of(d.cfg.campaign_window_start_day)
    last_week = d.cfg.expectations.max_week
    window = d.txc[d.txc['WEEK_NO'] >= window_start]

    def _stats(part: pd.DataFrame) -> dict[str, object]:
        baskets = part.groupby('BASKET_ID')['commodity'].nunique()
        spend = part.groupby('BASKET_ID')['SALES_VALUE'].sum()
        return {
            'baskets': part['BASKET_ID'].nunique(),
            'households': part['household_key'].nunique(),
            'lines': len(part),
            'median commodities/basket': _scalar(baskets.median()),
            'median basket spend': round(_scalar(spend.median()), 2),
            'private line share': round(_scalar((part['brand'] == 'Private').mean()), 3),
            'coupon line share': round(_scalar((part['COUPON_DISC'] < 0).mean()), 4),
            'distinct commodities': part['commodity'].nunique(),
        }

    early, late = (
        _stats(window[window['WEEK_NO'] <= cutoff]),
        _stats(window[window['WEEK_NO'] > cutoff]),
    )
    early_col = f'early (w{window_start}–{cutoff})'
    late_col = f'late (w{cutoff + 1}–{last_week})'
    weeks_row = {
        'metric': 'weeks in split',
        early_col: cutoff - window_start + 1,
        late_col: last_week - cutoff,
    }
    stats_rows = [{early_col: early[key], 'metric': key, late_col: late[key]} for key in early]
    rows = [weeks_row, *stats_rows]
    return CheckResult('Split balance (campaign window only)', _table(rows), None)


def check_causal(root: Path) -> CheckResult:
    total = 0
    products: set[int] = set()
    weeks: set[int] = set()
    display: dict[int, int] = {}
    mailer: dict[str, int] = {}
    for chunk in tqdm(iter_causal_chunks(root), desc='causal chunks', unit='chunk'):
        total += len(chunk)
        products.update(chunk['PRODUCT_ID'].unique().tolist())
        weeks.update(chunk['WEEK_NO'].unique().tolist())
        for key, value in chunk['display'].value_counts().items():
            display[int(key)] = display.get(int(key), 0) + int(value)
        for key, value in chunk['mailer'].value_counts().items():
            mailer[str(key)] = mailer.get(str(key), 0) + int(value)
    rows = [
        {'metric': 'rows', 'value': total, 'expected': '—'},
        {'metric': 'distinct products', 'value': len(products), 'expected': '—'},
        {'metric': 'weeks covered', 'value': len(weeks), 'expected': '—'},
        {
            'metric': 'display value counts',
            'value': dict(sorted(display.items())),
            'expected': '—',
        },
        {'metric': 'mailer value counts', 'value': dict(sorted(mailer.items())), 'expected': '—'},
    ]
    return CheckResult('Causal data (opt-in)', _table(rows), None)


def _weekly_coupon_coverage(d: Dataset) -> pd.DataFrame:
    elig = d.coupons.merge(d.products[['product_id', 'commodity']], on='product_id')
    campaign_commodities = elig.groupby('campaign')['commodity'].agg(set)
    rows = []
    for week in range(1, d.cfg.expectations.max_week + 1):
        start_day, end_day = (week - 1) * 7 + 1, week * 7
        live = d.campaigns[
            (d.campaigns['start_day'] <= end_day) & (d.campaigns['end_day'] >= start_day)
        ]
        covered: set[str] = set()
        for campaign in live['campaign']:
            covered |= campaign_commodities.get(campaign, set())
        rows.append({'week': week, 'n_live': len(live), 'n_eligible_commodities': len(covered)})
    return pd.DataFrame(rows)


def suggest_cutoff_week(campaigns: pd.DataFrame, cfg: DataChecksConfig) -> int:
    """Midpoint of the campaign-active window, snapped to a week."""
    first = int(max(cfg.campaign_window_start_day, campaigns['start_day'].min()))
    last = int(campaigns['end_day'].max())
    return _week_of((first + last) // 2)


def _week_of(day: int) -> int:
    return (day - 1) // 7 + 1


def _scalar(value: float | np.floating | int | np.integer | pd.Series) -> float:
    """Pull a Python float out of a pandas/numpy scalar aggregate."""
    if isinstance(value, pd.Series):
        value = value.iloc[0]
    return float(value)


def _table(rows: Sequence[Mapping[str, object]]) -> str:
    if not rows:
        return '_no rows_'
    headers = list(rows[0])
    lines = [
        '| ' + ' | '.join(headers) + ' |',
        '|' + '|'.join(['---'] * len(headers)) + '|',
    ]
    for row in rows:
        lines.append('| ' + ' | '.join(str(row[h]) for h in headers) + ' |')
    return '\n'.join(lines)


def _write_report(results: Sequence[CheckResult], out: Path, root: Path) -> None:
    lines = [
        '# Data Checks — Dunnhumby Complete Journey',
        '',
        f'- generated: {datetime.now().isoformat(timespec="seconds")}',
        f'- data dir: `{root.resolve()}`',
        '',
    ]
    for r in results:
        verdict = '✅ GO' if r.go else ('❌ NO-GO' if r.go is False else '— report-only')
        lines += [f'## {r.name}', '', r.markdown, '', f'**Verdict: {verdict}**', '']
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text('\n'.join(lines))
    logger.info('report written to {}', out)


def _log_summary(results: Sequence[CheckResult], out: Path) -> None:
    for r in results:
        status = 'GO' if r.go else ('NO-GO' if r.go is False else 'report-only')
        logger.info('{:>12}  {}', status, r.name)
    blocked = [r.name for r in results if r.go is False]
    if blocked:
        logger.error('data checks FAILED: {}', ', '.join(blocked))
    else:
        logger.success('all gated data checks passed; report at {}', out)


if __name__ == '__main__':
    main()
