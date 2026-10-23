import json
from collections.abc import Mapping

from commgym.cartopt.config import RewardConfig
from commgym.cartopt.instance import BrandQuota, BrandTier, Instance, MenuSKU, SkuCoupon
from commgym.cartopt.reward import GradeResult, grade, grade_cart, parse_completion
from commgym.cartopt.solver import Solution, solve

CFG = RewardConfig()

# Hand-derived fixture (prices in cents, no loyalty):
#   CAT: A1 Private 200 | A2 National 280 ; DOG: B1 Private 150 | B2 National 210
#   coupon c1: 30c off A2 ; quota: >= 1 National
# Carts: A1+B1 = 350 infeasible (no National) <- the greedy trap, cheaper than C*
#        A2+B1 = 400 feasible  <- C* (the optimum must use the coupon)
#        A1+B2 = 410 feasible  <- median feasible = C_ref
#        A2+B2 = 460 feasible
C_STAR = 400
C_REF = 410
CHECKS = 4  # CAT, DOG, extras, quota

INSTANCE = Instance(
    commodities=('CAT', 'DOG'),
    menu={
        'CAT': (
            MenuSKU('A1', 1, 'CAT', BrandTier.PRIVATE, 1, '', 200, 0),
            MenuSKU('A2', 2, 'CAT', BrandTier.NATIONAL, 1, '', 280, 0),
        ),
        'DOG': (
            MenuSKU('B1', 3, 'DOG', BrandTier.PRIVATE, 1, '', 150, 0),
            MenuSKU('B2', 4, 'DOG', BrandTier.NATIONAL, 1, '', 210, 0),
        ),
    },
    coupons=(SkuCoupon('c1', 'A2', 30),),
    constraints=(BrandQuota(BrandTier.NATIONAL, 1),),
)


def _grade_cart(cart: Mapping[str, object], total: float) -> GradeResult:
    return grade_cart(cart, total, INSTANCE, C_STAR, C_REF, CFG)


def _grade_text(text: str) -> GradeResult:
    return grade(text, INSTANCE, C_STAR, C_REF, CFG)


def _completion(cart: Mapping[str, object], total: float) -> str:
    payload = json.dumps({'cart': cart, 'total': total})
    return f'Reasoning about the quota...\n<answer>{payload}</answer>'


def _fields(result: GradeResult) -> dict[str, object]:
    return {
        'reward': result.reward,
        'feasible': result.feasible,
        'frac': result.frac_constraints,
        'opt': result.opt,
        'exact_opt': result.exact_opt,
        'price_ok': result.price_ok,
        'violations': result.violations,
        'cost': result.cost_cents,
    }


def test_oracle_weights_and_total_penalties():
    assert {
        'oracle': _fields(_grade_cart({'CAT': 'A2', 'DOG': 'B1'}, 4.00)),
        'overstated_total': _fields(_grade_cart({'CAT': 'A2', 'DOG': 'B1'}, 4.99)),
        'understated_total': _fields(_grade_cart({'CAT': 'A2', 'DOG': 'B1'}, 3.00)),
    } == {
        'oracle': {
            'reward': 1.0,
            'feasible': True,
            'frac': 1.0,
            'opt': 1.0,
            'exact_opt': True,
            'price_ok': True,
            'violations': (),
            'cost': 400,
        },
        'overstated_total': {
            'reward': 0.9,
            'feasible': True,
            'frac': 1.0,
            'opt': 1.0,
            'exact_opt': True,
            'price_ok': False,
            'violations': (),
            'cost': 400,
        },
        'understated_total': {
            'reward': 0.9,
            'feasible': True,
            'frac': 1.0,
            'opt': 1.0,
            'exact_opt': True,
            'price_ok': False,
            'violations': (),
            'cost': 400,
        },
    }


def test_infeasible_carts_score_partial_fractions():
    # (cart, violations, constraint checks passed); frac and reward are 3/4-style partials
    cases: dict[str, tuple[Mapping[str, object], tuple[str, ...], int]] = {
        'bad_code': ({'CAT': 'Z9', 'DOG': 'B2'}, ('bad_code:CAT',), 3),
        'list_in_category': (
            {'CAT': ['A1', 'A2'], 'DOG': 'B1'},
            ('bad_code:CAT', 'quota:National'),
            2,
        ),
        'missing_category': ({'DOG': 'B2'}, ('missing:CAT',), 3),
        'extra_category': (
            {'CAT': 'A1', 'DOG': 'B2', 'FREE': 'A2'},
            ('extra_categories',),
            3,
        ),
        'wrong_category': (
            {'CAT': 'B1', 'DOG': 'A1'},
            ('wrong_category:CAT', 'wrong_category:DOG', 'quota:National'),
            1,
        ),
    }
    actual = {}
    for name, (cart, _, _) in cases.items():
        result = _grade_cart(cart, 3.50)
        actual[name] = (result.violations, result.frac_constraints, result.reward)
    assert actual == {
        name: (violations, passed / CHECKS, 0.3 * passed / CHECKS)
        for name, (_, violations, passed) in cases.items()
    }


def test_parse_failure_modes_score_zero():
    cases = {
        'no_answer_block': (
            'The cheapest cart is A1 + B2 for $3.50.',
            'parse:no_answer_block',
        ),
        'invalid_json': (
            '<answer>{"cart": {CAT: A1}, "total": 3.50}</answer>',
            'parse:invalid_json',
        ),
        'json_outside_tags': (
            '{"cart": {"CAT": "A1", "DOG": "B2"}, "total": 3.50}',
            'parse:no_answer_block',
        ),
        'non_numeric_total': (
            '<answer>{"cart": {"CAT": "A1"}, "total": "cheap"}</answer>',
            'parse:total_not_numeric',
        ),
        'multiple_answer_blocks': (
            _completion({'CAT': 'A2', 'DOG': 'B1'}, 4.00)
            + _completion({'CAT': 'A2', 'DOG': 'B2'}, 4.60),
            'parse:multiple_answer_blocks',
        ),
    }
    actual = {}
    for name, (text, _) in cases.items():
        result = _grade_text(text)
        actual[name] = (result.reward, result.violations[0])
    assert actual == {name: (0.0, reason) for name, (_, reason) in cases.items()}


def test_parse_completion_accepts_exactly_one_block():
    parsed = parse_completion(_completion({'CAT': 'A1', 'DOG': 'B2'}, 3.50))
    assert {'ok': parsed.parse_ok, 'total': parsed.total_dollars} == {'ok': True, 'total': 3.5}


def test_greedy_trap_scores_below_oracle():
    # greedy-cheapest = first-listed codes here: A1 + B1 is cheapest but has no National item
    greedy = _grade_cart({'CAT': 'A1', 'DOG': 'B1'}, 3.50)
    oracle = _grade_cart({'CAT': 'A2', 'DOG': 'B1'}, 4.00)
    assert {
        'reward': greedy.reward,
        'feasible': greedy.feasible,
        'cost': greedy.cost_cents,
        'below_oracle': greedy.reward < oracle.reward,
    } == {
        'reward': 0.3 * 3 / CHECKS,
        'feasible': False,
        'cost': 350,
        'below_oracle': True,
    }


def test_random_feasible_opts_center_at_zero():
    solution = solve(INSTANCE)
    carts = (
        {'CAT': 'A2', 'DOG': 'B1'},
        {'CAT': 'A1', 'DOG': 'B2'},
        {'CAT': 'A2', 'DOG': 'B2'},
    )
    opts = sorted(_grade_cart(cart, 0.0).opt for cart in carts)
    assert {
        'opts': opts,
        'median': opts[len(opts) // 2],
        'n_feasible': solution.n_feasible,
        'c_star_matches': solution.c_star_cents() == C_STAR,
    } == {
        'opts': [0.0, 0.0, 1.0],
        'median': 0.0,
        'n_feasible': 3,
        'c_star_matches': True,
    }


def test_degenerate_median_equals_optimum():
    # carts cost 200, 200, 600 -> median (200) == C*, so only the optimum band earns opt credit
    degenerate = Instance(
        commodities=('CAT', 'DOG'),
        menu={
            'CAT': (
                MenuSKU('A1', 1, 'CAT', BrandTier.PRIVATE, 1, '', 100, 0),
                MenuSKU('A2', 2, 'CAT', BrandTier.PRIVATE, 1, '', 100, 0),
                MenuSKU('A3', 3, 'CAT', BrandTier.NATIONAL, 1, '', 500, 0),
            ),
            'DOG': (MenuSKU('B1', 4, 'DOG', BrandTier.PRIVATE, 1, '', 100, 0),),
        },
        coupons=(),
        constraints=(),
    )
    solution = solve(degenerate)

    def reward(cart: Mapping[str, str], total: float) -> float:
        return _reward(degenerate, solution, cart, total)

    assert {
        'c_star': solution.c_star_cents(),
        'c_ref': solution.c_ref_cents(),
        'best': reward({'CAT': 'A2', 'DOG': 'B1'}, 2.00),
        'worst': reward({'CAT': 'A3', 'DOG': 'B1'}, 6.00),
    } == {'c_star': 200, 'c_ref': 200, 'best': 1.0, 'worst': 0.6}


def _reward(
    instance: Instance, solution: Solution, cart: Mapping[str, str], total: float
) -> float:
    return grade_cart(
        cart, total, instance, solution.c_star_cents(), solution.c_ref_cents(), CFG
    ).reward
