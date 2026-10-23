import json
import re
from collections.abc import Mapping
from dataclasses import dataclass

from commgym.cartopt.config import RewardConfig
from commgym.cartopt.instance import BrandQuota, Constraint, Instance, LoyalSKU, MenuSKU
from commgym.cartopt.pricing import cost

ANSWER_RE = re.compile(r'<answer>(.*?)</answer>', re.DOTALL)


@dataclass(frozen=True, slots=True)
class ParsedAnswer:
    parse_ok: bool
    reason: str | None
    cart: dict[str, object] | None
    total_dollars: float | None


@dataclass(frozen=True, slots=True)
class GradeResult:
    reward: float
    parse_ok: bool
    feasible: bool
    frac_constraints: float
    opt: float
    exact_opt: bool
    price_ok: bool
    violations: tuple[str, ...]
    total_cents: int | None
    cost_cents: int | None
    cost_gap_cents: int | None


def parse_completion(text: str) -> ParsedAnswer:
    """Exactly one <answer> block holding JSON with a `cart` dict and a numeric `total`."""
    blocks = ANSWER_RE.findall(text)
    if not blocks:
        return ParsedAnswer(False, 'no_answer_block', None, None)
    if len(blocks) > 1:
        return ParsedAnswer(False, 'multiple_answer_blocks', None, None)
    try:
        payload = json.loads(blocks[0])
    except json.JSONDecodeError:
        return ParsedAnswer(False, 'invalid_json', None, None)
    if not isinstance(payload, dict) or not isinstance(payload.get('cart'), dict):
        return ParsedAnswer(False, 'cart_not_a_dict', None, None)
    total = payload.get('total')
    if isinstance(total, bool) or not isinstance(total, int | float):
        return ParsedAnswer(False, 'total_not_numeric', None, None)
    return ParsedAnswer(True, None, payload['cart'], float(total))


def grade(
    text: str, instance: Instance, c_star_cents: int, c_ref_cents: int, cfg: RewardConfig
) -> GradeResult:
    """Grade a raw model completion end to end (parse, then the shared cart grader)."""
    parsed = parse_completion(text)
    if not parsed.parse_ok:
        assert parsed.cart is None and parsed.total_dollars is None, 'parser contract broken'
        return GradeResult(
            reward=0.0,
            parse_ok=False,
            feasible=False,
            frac_constraints=0.0,
            opt=0.0,
            exact_opt=False,
            price_ok=False,
            violations=(f'parse:{parsed.reason}',),
            total_cents=None,
            cost_cents=None,
            cost_gap_cents=None,
        )
    assert parsed.cart is not None and parsed.total_dollars is not None, 'parser contract broken'
    return grade_cart(parsed.cart, parsed.total_dollars, instance, c_star_cents, c_ref_cents, cfg)


def grade_cart(
    cart: Mapping[str, object],
    total_dollars: float,
    instance: Instance,
    c_star_cents: int,
    c_ref_cents: int,
    cfg: RewardConfig,
) -> GradeResult:
    """Grade a parsed cart; baselines and model completions share this exact path."""
    checks, chosen = _constraint_checks(cart, instance)
    violations = tuple(name for name, ok in checks if not ok)
    feasible = not violations
    priceable = len(chosen) == len(instance.commodities)
    pricing_cart = {commodity: sku.code for commodity, sku in chosen.items()}
    cost_cents = cost(pricing_cart, instance).total_cents if priceable else None
    total_cents = int(round(total_dollars * 100))
    if feasible:
        assert cost_cents is not None, 'a feasible cart always picks one valid code per commodity'
        opt = _opt_score(cost_cents, c_star_cents, c_ref_cents, cfg)
        exact_opt = cost_cents <= c_star_cents + cfg.tie_eps_cents
        price_ok = abs(total_cents - cost_cents) <= cfg.price_tol_cents
    else:
        opt, exact_opt, price_ok = 0.0, False, False
    frac = _frac_satisfied(checks)
    reward = _total(cfg, feasible, frac, opt, price_ok)
    return GradeResult(
        reward=reward,
        parse_ok=True,
        feasible=feasible,
        frac_constraints=frac,
        opt=opt,
        exact_opt=exact_opt,
        price_ok=price_ok,
        violations=violations,
        total_cents=total_cents,
        cost_cents=cost_cents,
        cost_gap_cents=(cost_cents - c_star_cents) if cost_cents is not None else None,
    )


def _total(cfg: RewardConfig, feasible: bool, frac: float, opt: float, price_ok: bool) -> float:
    """Lexicographic by construction: w_partial < w_feasible separates the tiers."""
    if not feasible:
        return cfg.w_partial * frac
    return cfg.w_feasible + cfg.w_opt * opt + cfg.w_price * price_ok


def _opt_score(cost_cents: int, c_star_cents: int, c_ref_cents: int, cfg: RewardConfig) -> float:
    if cost_cents <= c_star_cents + cfg.tie_eps_cents:
        return 1.0
    if c_ref_cents <= c_star_cents:
        # Degenerate (median feasible == optimum): nothing between the band and the median.
        return 0.0
    return max(0.0, min(1.0, (c_ref_cents - cost_cents) / (c_ref_cents - c_star_cents)))


def _constraint_checks(
    cart: Mapping[str, object], instance: Instance
) -> tuple[tuple[tuple[str, bool], ...], dict[str, MenuSKU]]:
    """One check per commodity, one per declared constraint, plus the no-extra-categories check."""
    by_code = {sku.code: sku for skus in instance.menu.values() for sku in skus}
    checks: list[tuple[str, bool]] = []
    chosen: dict[str, MenuSKU] = {}
    for commodity in instance.commodities:
        value = cart.get(commodity)
        match: MenuSKU | None = by_code.get(value) if isinstance(value, str) else None
        ok = match is not None and match.commodity == commodity
        checks.append((_violation_name(commodity, value, match), ok))
        if ok:
            assert match is not None, 'match checked above'
            chosen[commodity] = match
    extra = {key for key in cart if key not in set(instance.commodities)}
    checks.append(('extra_categories', not extra))
    for constraint in instance.constraints:
        checks.append(_constraint_check(constraint, chosen, by_code))
    return tuple(checks), chosen


def _constraint_check(
    constraint: Constraint, chosen: dict[str, MenuSKU], by_code: dict[str, MenuSKU]
) -> tuple[str, bool]:
    match constraint:
        case BrandQuota(tier=tier, min_count=min_count):
            count = sum(1 for sku in chosen.values() if sku.brand_tier == tier)
            return (f'quota:{tier.value}', count >= min_count)
        case LoyalSKU(code=code):
            sku = by_code[code]
            return (f'loyal:{code}', chosen.get(sku.commodity) == sku)


def _violation_name(commodity: str, value: object, match: MenuSKU | None) -> str:
    """Label for a failed commodity check; only surfaced when the check fails."""
    if value is None:
        return f'missing:{commodity}'
    if match is not None and match.commodity != commodity:
        return f'wrong_category:{commodity}'
    return f'bad_code:{commodity}'


def _frac_satisfied(checks: tuple[tuple[str, bool], ...]) -> float:
    return sum(1 for _, ok in checks if ok) / len(checks)
