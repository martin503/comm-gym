import numpy as np
from hypothesis import assume, given
from hypothesis import strategies as st

from commgym.cartopt.config import RewardConfig
from commgym.cartopt.instance import BrandQuota, BrandTier, Constraint, Coupon, Instance, MenuSKU
from commgym.cartopt.reward import grade, grade_cart, parse_completion
from commgym.cartopt.solver import cart_at, solve

CFG = RewardConfig()

# fixed instance for the arbitrary-text bound property: 2 carts, Private quota satisfied by both
FIXED = Instance(
    commodities=('CAT',),
    menu={
        'CAT': (
            MenuSKU('A1', 1, 'CAT', BrandTier.PRIVATE, 1, '', 200, 0),
            MenuSKU('A2', 2, 'CAT', BrandTier.PRIVATE, 1, '', 400, 0),
        )
    },
    coupons=(),
    constraints=(BrandQuota(BrandTier.PRIVATE, 1),),
)
FIXED_SOLUTION = solve(FIXED)


@st.composite
def quota_instances(draw: st.DrawFn) -> Instance:
    """Small no-coupon instances with one brand quota (coupons can't drive cost negative)."""
    n_commodities = draw(st.integers(min_value=2, max_value=3))
    menu: dict[str, list[MenuSKU]] = {}
    for k in range(n_commodities):
        commodity = f'CAT{k}'
        n_skus = draw(st.integers(min_value=1, max_value=3))
        skus = []
        for i in range(n_skus):
            shelf = draw(st.integers(min_value=1, max_value=600))
            loyalty = draw(st.integers(min_value=0, max_value=shelf))
            tier = BrandTier.NATIONAL if draw(st.booleans()) else BrandTier.PRIVATE
            skus.append(MenuSKU(f'S{k}_{i}', 10 * k + i, commodity, tier, 1, '', shelf, loyalty))
        menu[commodity] = skus
    tier = draw(st.sampled_from([BrandTier.NATIONAL, BrandTier.PRIVATE]))
    constraints: tuple[Constraint, ...] = (BrandQuota(tier, 1),)
    coupons: tuple[Coupon, ...] = ()
    return Instance(tuple(menu), {c: tuple(s) for c, s in menu.items()}, coupons, constraints)


def _reference(instance: Instance) -> tuple[Instance, int, int]:
    solution = solve(instance)
    return instance, solution.c_star_cents(), solution.c_ref_cents()


@given(text=st.text())
def test_reward_stays_in_unit_interval_for_arbitrary_text(text: str):
    result = grade(text, FIXED, FIXED_SOLUTION.c_star_cents(), FIXED_SOLUTION.c_ref_cents(), CFG)
    assert 0.0 <= result.reward <= 1.0


@given(instance=quota_instances(), seed=st.integers(min_value=0))
def test_infeasible_cart_scores_below_feasible(instance: Instance, seed: int):
    solution = solve(instance)
    assume(solution.n_feasible > 0)
    rng = np.random.default_rng(seed)
    feasible_idx = np.flatnonzero(solution.feasible)
    cart = cart_at(instance, int(rng.choice(feasible_idx)))
    broken = dict(cart)
    # a code from the second category under the first category's key is always invalid
    broken[instance.commodities[0]] = cart[instance.commodities[1]]
    instance, c_star, c_ref = _reference(instance)
    feasible_r = grade_cart(cart, 0.0, instance, c_star, c_ref, CFG).reward
    infeasible_r = grade_cart(broken, 0.0, instance, c_star, c_ref, CFG).reward
    assert {
        'ordering': infeasible_r < feasible_r,
        'partial_cap': infeasible_r <= CFG.w_partial,
        'feasible_floor': feasible_r >= CFG.w_feasible,
    } == {'ordering': True, 'partial_cap': True, 'feasible_floor': True}


@given(junk=st.text(), payload=st.text())
def test_two_answer_blocks_never_parse(junk: str, payload: str):
    parsed = parse_completion(f'{junk}<answer>{payload}</answer>{junk}<answer></answer>')
    assert {'ok': parsed.parse_ok, 'reason': parsed.reason} == {
        'ok': False,
        'reason': 'multiple_answer_blocks',
    }
