import re
from dataclasses import dataclass

from loguru import logger

from commgym.core.openrouter import ChatResult, OpenRouterClient
from commgym.offer.config import JudgeConfig

JUDGE_PROMPT_VERSION = 'j1'

SYSTEM_TEMPLATE = """You judge push notifications for a grocery chain. You will see a household's
purchase profile, the coupons live for that household, and two candidate responses (A and B).
Each response picks coupons and writes one message.

Pick the better response for this household. Consider, in order:
- relevance: does the selection match the household's habits?
- faithfulness: does the message only claim what the profile and coupons support?
- clarity and natural tone
- persuasive without pressure or flattery

Answer with exactly one word on the first line: A, B, or TIE. You may add one short reason."""

VERDICT_SCORES = {'A': 1.0, 'B': 0.0, 'TIE': 0.5}


@dataclass(frozen=True, slots=True)
class JudgeOutcome:
    judge_win: float  # from the candidate's perspective, mean over both orders
    order_scores: tuple[float, float]  # candidate score when listed first / second
    error: str | None
    prompt_tokens: int
    completion_tokens: int


def judge_system_prompt() -> str:
    return SYSTEM_TEMPLATE


def judge_user_prompt(
    context_prompt: str,
    selection_a: tuple[str, ...],
    message_a: str,
    selection_b: tuple[str, ...],
    message_b: str,
) -> str:
    """The judge sees the policy's user prompt verbatim, so it can only hold the
    candidate to the same table the policy saw."""
    return (
        f'{context_prompt}\n\n'
        f'## Response A\nselected coupons: {", ".join(selection_a)}\nmessage: {message_a}\n\n'
        f'## Response B\nselected coupons: {", ".join(selection_b)}\nmessage: {message_b}\n\n'
        f'Which response is better: A, B, or TIE?'
    )


def parse_verdict(text: str) -> float | None:
    """First standalone A/B/TIE wins; None when nothing parseable came back."""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            word = stripped.split()[0].strip('.,:;()').upper()
            if word in VERDICT_SCORES:
                return VERDICT_SCORES[word]
            break
    match = re.search(r'\b(A|B|TIE)\b', text.upper())
    return VERDICT_SCORES[match.group(1)] if match else None


async def judge_pair(
    client: OpenRouterClient,
    cfg: JudgeConfig,
    *,
    context_prompt: str,
    candidate_selection: tuple[str, ...],
    candidate_message: str,
    reference_selection: tuple[str, ...],
    reference_message: str,
) -> JudgeOutcome:
    """Both orders at temperature 0; the average is the candidate's judge_win."""
    scores: list[float] = []
    tokens_in = tokens_out = 0
    for selection_a, message_a, selection_b, message_b in (
        (candidate_selection, candidate_message, reference_selection, reference_message),
        (reference_selection, reference_message, candidate_selection, candidate_message),
    ):
        result = await _verdict(
            client,
            cfg,
            context_prompt,
            selection_a,
            message_a,
            selection_b,
            message_b,
        )
        if result is None:
            return JudgeOutcome(
                judge_win=0.0,
                order_scores=(0.0, 0.0),
                error='unparseable_verdict',
                prompt_tokens=tokens_in,
                completion_tokens=tokens_out,
            )
        # first order: A is the candidate; second: A is the reference, so flip
        listed_first = result[0]
        scores.append(listed_first if len(scores) == 0 else 1.0 - listed_first)
        tokens_in += result[1].prompt_tokens
        tokens_out += result[1].completion_tokens
    return JudgeOutcome(
        judge_win=sum(scores) / 2,
        order_scores=(scores[0], scores[1]),
        error=None,
        prompt_tokens=tokens_in,
        completion_tokens=tokens_out,
    )


def reliability(outcomes: list[JudgeOutcome]) -> dict[str, float]:
    """Order consistency and tie rate over a set of both-order outcomes."""
    judged = [outcome for outcome in outcomes if outcome.error is None]
    assert judged, 'no parseable judgments to measure reliability on'
    consistent = sum(1 for o in judged if _class(o.order_scores[0]) == _class(o.order_scores[1]))
    ties = sum(1 for o in judged if o.judge_win == 0.5)
    return {
        'order_consistency': consistent / len(judged),
        'tie_rate': ties / len(judged),
        'n': float(len(judged)),
    }


async def _verdict(
    client: OpenRouterClient,
    cfg: JudgeConfig,
    context_prompt: str,
    selection_a: tuple[str, ...],
    message_a: str,
    selection_b: tuple[str, ...],
    message_b: str,
) -> tuple[float, ChatResult] | None:
    messages = [
        {'role': 'system', 'content': judge_system_prompt()},
        {
            'role': 'user',
            'content': judge_user_prompt(
                context_prompt, selection_a, message_a, selection_b, message_b
            ),
        },
    ]
    result = await client.chat(
        cfg.model,
        messages,
        temperature=cfg.temperature,
        max_tokens=cfg.max_tokens,
        reasoning_effort=cfg.reasoning_effort,
    )
    score = parse_verdict(result.text)
    if score is None:
        result = await client.chat(
            cfg.model,
            messages,
            temperature=cfg.temperature,
            max_tokens=cfg.max_tokens,
            reasoning_effort=cfg.reasoning_effort,
        )
        score = parse_verdict(result.text)
    if score is None:
        # reasoning models can burn the whole budget thinking; the tail says so
        logger.warning('unparseable verdict, tail: {!r}', result.text[-160:])
    return None if score is None else (score, result)


def _class(score: float) -> str:
    """win / tie / loss from a single-order score."""
    if score > 0.5:
        return 'win'
    if score < 0.5:
        return 'loss'
    return 'tie'
