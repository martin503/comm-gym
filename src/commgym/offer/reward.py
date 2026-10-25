import json
import re
from dataclasses import dataclass

from commgym.offer.config import GateConfig, RewardConfig
from commgym.offer.instance import OfferCoupon, OfferInstance
from commgym.offer.lexicon import (
    Lexicon,
    amount_violations,
    brand_claims,
    has_numbers,
    judge_addressing,
    urgency_mentions,
)

ANSWER_RE = re.compile(r'<answer>(.*?)</answer>', re.DOTALL)


@dataclass(frozen=True, slots=True)
class ParsedOffer:
    parse_ok: bool
    reason: str | None
    selected: tuple[str, ...] | None
    message: str | None


@dataclass(frozen=True, slots=True)
class GateResult:
    passed: bool
    failures: tuple[str, ...]
    word_count: int
    affinity: float
    n_selected: int


@dataclass(frozen=True, slots=True)
class OfferGrade:
    reward: float  # judge-free prefix: 0 on any gate failure
    parse_ok: bool
    gate_passed: bool
    failures: tuple[str, ...]
    affinity: float
    selected: tuple[str, ...]
    message: str | None
    word_count: int


def parse_completion(text: str) -> ParsedOffer:
    """Exactly one <answer> block holding JSON with a `selected` list and a `message`."""
    blocks = ANSWER_RE.findall(text)
    if not blocks:
        return ParsedOffer(False, 'no_answer_block', None, None)
    if len(blocks) > 1:
        return ParsedOffer(False, 'multiple_answer_blocks', None, None)
    try:
        payload = json.loads(blocks[0])
    except json.JSONDecodeError:
        return ParsedOffer(False, 'invalid_json', None, None)
    if not isinstance(payload, dict):
        return ParsedOffer(False, 'payload_not_a_dict', None, None)
    selected = payload.get('selected')
    if not isinstance(selected, list) or not all(isinstance(code, str) for code in selected):
        return ParsedOffer(False, 'selected_not_strings', None, None)
    if not selected:
        return ParsedOffer(False, 'selected_empty', None, None)
    if len(set(selected)) != len(selected):
        return ParsedOffer(False, 'duplicate_codes', None, None)
    message = payload.get('message')
    if not isinstance(message, str):
        return ParsedOffer(False, 'message_not_a_string', None, None)
    return ParsedOffer(True, None, tuple(selected), message)


def gate(
    parsed: ParsedOffer,
    instance: OfferInstance,
    level: str,
    lexicon: Lexicon,
    cfg: GateConfig,
) -> GateResult:
    """Programmatic grounding gate: any failure means the message is ungrounded."""
    assert parsed.parse_ok and parsed.selected is not None and parsed.message is not None, (
        'gate assumes a parsed completion'
    )
    selected, message = parsed.selected, parsed.message
    shown = {coupon.code: coupon for coupon in instance.slice_for(level)}
    failures: list[str] = []
    failures += [f'bad_code:{code}' for code in selected if code not in shown]
    if not cfg.min_selected <= len(selected) <= cfg.max_selected:
        failures.append(f'selection_count:{len(selected)}')
    words = len(message.split())
    if words > cfg.max_words:
        failures.append(f'length:{words}')
    failures += gate_text_failures(message, selected, shown, lexicon)
    affinity_value = affinity(selected, instance, level)
    return GateResult(
        passed=not failures,
        failures=tuple(failures),
        word_count=words,
        affinity=affinity_value,
        n_selected=len(selected),
    )


def gate_text_failures(
    message: str,
    selected: tuple[str, ...],
    shown: dict[str, OfferCoupon],
    lexicon: Lexicon,
) -> list[str]:
    """Text-level grounding rules; needs the shown slice for tier and urgency flags."""
    failures: list[str] = []
    if has_numbers(message):
        failures.append('numbers:digit_or_symbol')
    failures += [f'numbers:{phrase}' for phrase in amount_violations(message)]
    mentions = lexicon.mentions(message)
    covered = {
        commodity for code in selected if code in shown for commodity in shown[code].commodities
    }
    failures += [
        f'ungrounded_category:{mention.keyword}'
        for mention in mentions
        if not mention.commodities & covered
    ]
    if not any(mention.commodities & covered for mention in mentions):
        failures.append('not_specific')
    ends_soon = any(shown[code].ends_soon for code in selected if code in shown)
    if not ends_soon:
        failures += [f'urgency:{phrase}' for phrase in urgency_mentions(message)]
    mentioned = {commodity for mention in mentions for commodity in mention.commodities}
    for claim, tier in brand_claims(message):
        matches_tier = any(
            code in shown
            and shown[code].tier in (tier.value, 'Mixed')
            and mentioned & set(shown[code].commodities)
            for code in selected
        )
        if not matches_tier:
            failures.append(f'brand_tier:{claim}')
    failures += [f'judge_addressing:{phrase}' for phrase in judge_addressing(message)]
    return failures


def affinity(selected: tuple[str, ...], instance: OfferInstance, level: str) -> float:
    """Share of the shown pool's purchase mass captured by the selection, in [0, 1].
    A pool with zero mass anywhere carries no signal: any selection is vacuously
    optimal, so the affinity is 1.0 rather than a punishing 0.0."""
    shown = instance.slice_for(level)
    by_code = {coupon.code: coupon for coupon in shown}
    total = sum(instance.profile.mass(coupon.commodities) for coupon in shown)
    if total == 0:
        return 1.0
    picked = sum(
        instance.profile.mass(by_code[code].commodities) for code in selected if code in by_code
    )
    return picked / total


def grade(
    text: str,
    instance: OfferInstance,
    level: str,
    lexicon: Lexicon,
    gate_cfg: GateConfig,
    reward_cfg: RewardConfig,
) -> OfferGrade:
    """Grade a raw completion to the judge-free prefix of the reward; the judge
    script adds its win-rate term afterwards."""
    parsed = parse_completion(text)
    if not parsed.parse_ok:
        return OfferGrade(
            reward=0.0,
            parse_ok=False,
            gate_passed=False,
            failures=(f'parse:{parsed.reason}',),
            affinity=0.0,
            selected=(),
            message=None,
            word_count=0,
        )
    assert parsed.selected is not None and parsed.message is not None, 'parser contract broken'
    result = gate(parsed, instance, level, lexicon, gate_cfg)
    reward = reward_cfg.w_base + reward_cfg.w_affinity * result.affinity if result.passed else 0.0
    return OfferGrade(
        reward=reward,
        parse_ok=True,
        gate_passed=result.passed,
        failures=result.failures,
        affinity=result.affinity,
        selected=parsed.selected,
        message=parsed.message,
        word_count=result.word_count,
    )


def final_reward(prefix_reward: float, judge_win: float, cfg: RewardConfig) -> float:
    """Compose the stored prefix with the judged win rate; clamped to [0, 1]."""
    return max(0.0, min(1.0, prefix_reward + cfg.w_judge * judge_win))


def components_of(graded: OfferGrade, instance: OfferInstance, level: str) -> dict[str, object]:
    """Rollout-record components shared by the eval grader and the baselines writer."""
    shown = {coupon.code: coupon for coupon in instance.slice_for(level)}
    return {
        'gate_pass': graded.gate_passed,
        'parse_ok': graded.parse_ok,
        'gate_failures': list(graded.failures),
        'affinity': graded.affinity,
        'word_count': graded.word_count,
        'n_selected': len(graded.selected),
        'selected': list(graded.selected),
        'message': graded.message,
        'coupon_keys': {
            code: [coupon.campaign, coupon.coupon_upc]
            for code, coupon in shown.items()
            if code in graded.selected
        },
    }
