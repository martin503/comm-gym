import json
import math
import re
from collections.abc import Sequence
from dataclasses import dataclass

from commgym.refund.config import RewardConfig
from commgym.refund.instance import Claim, RefundInstance
from commgym.refund.policy import Decision, ReasonCode

ANSWER_RE = re.compile(r'<answer>(.*?)</answer>', re.DOTALL)
REQUIRED_FIELDS = ('line', 'decision', 'reason', 'refund')


@dataclass(frozen=True, slots=True)
class ParsedClaim:
    """One model answer, normalized; refund already converted to integer cents."""

    line: str | None
    decision: Decision
    reason: ReasonCode
    refund_cents: int


@dataclass(frozen=True, slots=True)
class ParsedAnswer:
    parse_ok: bool
    reason: str | None
    claims: tuple[ParsedClaim, ...] | None


@dataclass(frozen=True, slots=True)
class ClaimScore:
    score: float
    decision_ok: bool
    line_ok: bool
    reason_ok: bool
    refund_ok: bool
    false_approve: bool
    false_reject: bool
    dollar_error_cents: int


@dataclass(frozen=True, slots=True)
class GradeResult:
    reward: float
    parse_ok: bool
    parse_reason: str | None
    claim_scores: tuple[ClaimScore, ...]


def parse_completion(text: str, n_claims: int, valid_codes: frozenset[str]) -> ParsedAnswer:
    """Exactly one <answer> block holding one JSON claim object per message claim, in order."""
    blocks = ANSWER_RE.findall(text)
    if not blocks:
        return ParsedAnswer(False, 'no_answer_block', None)
    if len(blocks) > 1:
        return ParsedAnswer(False, 'multiple_answer_blocks', None)
    try:
        payload = json.loads(blocks[0])
    except json.JSONDecodeError:
        return ParsedAnswer(False, 'invalid_json', None)
    if not isinstance(payload, dict):
        return ParsedAnswer(False, 'payload_not_a_dict', None)
    entries = payload.get('claims')
    if not isinstance(entries, list):
        return ParsedAnswer(False, 'claims_not_a_list', None)
    if len(entries) != n_claims:
        return ParsedAnswer(False, 'wrong_claim_count', None)
    parsed: list[ParsedClaim] = []
    for entry in entries:
        if not isinstance(entry, dict):
            return ParsedAnswer(False, 'claim_not_a_dict', None)
        for field in REQUIRED_FIELDS:
            if field not in entry:
                return ParsedAnswer(False, f'missing_field:{field}', None)
        line = entry['line']
        if line is not None and (not isinstance(line, str) or line not in valid_codes):
            return ParsedAnswer(False, 'bad_line', None)
        decision_text, reason_text = entry['decision'], entry['reason']
        if not isinstance(decision_text, str) or not isinstance(reason_text, str):
            return ParsedAnswer(False, 'bad_decision_or_reason', None)
        try:
            decision = Decision(decision_text)
            reason = ReasonCode(reason_text)
        except ValueError:
            return ParsedAnswer(False, 'bad_decision_or_reason', None)
        refund = entry['refund']
        if isinstance(refund, bool) or not isinstance(refund, int | float):
            return ParsedAnswer(False, 'refund_not_numeric', None)
        if not math.isfinite(refund):
            return ParsedAnswer(False, 'refund_not_finite', None)
        if refund < 0:
            return ParsedAnswer(False, 'refund_negative', None)
        parsed.append(ParsedClaim(line, decision, reason, int(round(refund * 100))))
    return ParsedAnswer(True, None, tuple(parsed))


def grade(text: str, instance: RefundInstance, cfg: RewardConfig) -> GradeResult:
    """Grade a raw model completion end to end (parse, then per-claim scoring)."""
    codes = frozenset(line.code for line in instance.lines)
    parsed = parse_completion(text, len(instance.claims), codes)
    if not parsed.parse_ok:
        assert parsed.claims is None, 'parser contract broken'
        return GradeResult(0.0, False, parsed.reason, ())
    assert parsed.claims is not None, 'parser contract broken'
    return grade_parsed(parsed.claims, instance, cfg)


def grade_parsed(
    claims: Sequence[ParsedClaim], instance: RefundInstance, cfg: RewardConfig
) -> GradeResult:
    """Score already-parsed answers; baselines and model completions share this exact path."""
    assert len(claims) == len(instance.claims), 'one parsed answer per message claim'
    assert instance.claims, 'instances carry at least one claim'
    scores = tuple(
        _score_claim(answer, truth, cfg)
        for answer, truth in zip(claims, instance.claims, strict=True)
    )
    return GradeResult(
        reward=sum(s.score for s in scores) / len(scores),
        parse_ok=True,
        parse_reason=None,
        claim_scores=scores,
    )


def _score_claim(answer: ParsedClaim, truth: Claim, cfg: RewardConfig) -> ClaimScore:
    """Spec §6: wrong decision zeroes the claim; a truth-reject with any refund also zeroes."""
    decision_ok = answer.decision is truth.truth_decision
    line_ok = answer.line == truth.truth_line
    reason_ok = answer.reason is truth.truth_reason
    refund_ok = abs(answer.refund_cents - truth.truth_refund_cents) <= cfg.refund_tol_cents
    if not decision_ok:
        score = 0.0
    elif truth.truth_decision is Decision.APPROVE:
        score = (
            cfg.w_decision
            + cfg.w_line * line_ok
            + cfg.w_reason_approve * reason_ok
            + cfg.w_refund * refund_ok
        )
    else:
        score = cfg.w_decision + cfg.w_line * line_ok + cfg.w_reason_reject * reason_ok
        if answer.refund_cents != 0:
            score = 0.0
    return ClaimScore(
        score=score,
        decision_ok=decision_ok,
        line_ok=line_ok,
        reason_ok=reason_ok,
        refund_ok=refund_ok,
        false_approve=(not decision_ok and truth.truth_decision is Decision.REJECT),
        false_reject=(not decision_ok and truth.truth_decision is Decision.APPROVE),
        dollar_error_cents=abs(answer.refund_cents - truth.truth_refund_cents),
    )
