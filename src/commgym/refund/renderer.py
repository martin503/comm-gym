import json
import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from pydantic import BaseModel, ConfigDict, ValidationError

from commgym.refund.instance import ReceiptLine
from commgym.refund.policy import StatedType

# initial reference round plus one rewrite; a claim still unmatched after that discards the anchor
VERIFY_ROUNDS = 2
# bump when any prompt changes: the render cache is keyed per revision so stale renders are
# never mixed with new-prompt ones
PROMPT_REVISION = 5
MAX_TOKENS = 2048
WRITER_TEMPERATURE = 0.8
VERIFIER_TEMPERATURE = 0.0
LINE_CODE_RE = re.compile(r'\bL\d{2,}\b')
COUPON_CODE_RE = re.compile(r'\bC\d{2,}\b')
DOLLAR_RE = re.compile(r'\$\s?\d+(?:\.\d{1,2})?|\b\d+\.\d{2}\b')
JSON_BLOCK_RE = re.compile(r'\{.*\}', re.DOTALL)


class TextModel(Protocol):
    async def complete(
        self, model: str, prompt: str, *, temperature: float, max_tokens: int
    ) -> str: ...


@dataclass(frozen=True, slots=True)
class ClaimSpec:
    """What the writer must express for one claim; carries no truth."""

    stated_type: StatedType
    kind: str  # 'unique' | 'clarify' | 'absent'
    target_lines: tuple[str, ...]  # unique: one code; clarify: several; absent: none
    absent_item: str | None  # history category name for absent claims
    stated_cents: int | None  # exact figure the message must state


@dataclass(frozen=True, slots=True)
class RenderOutcome:
    """A rendered anchor; ok=False means the anchor is discarded (keep the discard log)."""

    ok: bool
    references: tuple[str, ...]
    sentences: tuple[str, ...]
    discards: tuple[tuple[str, str], ...]  # (stage, kind) of every discarded attempt
    detail: dict[str, object]  # verifier line sets and the message, for the build log


def split_sentences(message: str) -> list[str]:
    """Sentence split that keeps dollar amounts like $4.99 (no space) in one sentence."""
    return [part.strip() for part in re.split(r'(?<=[.!?])\s+', message) if part.strip()]


def leak_errors(message: str, allowed_figures: frozenset[str]) -> list[str]:
    """Line codes, coupon codes, or dollar figures the customer was never given."""
    errors = [f'line code {m}' for m in LINE_CODE_RE.findall(message)]
    errors += [f'coupon code {m}' for m in COUPON_CODE_RE.findall(message)]
    for match in DOLLAR_RE.findall(message):
        if f'${match.replace("$ ", "").lstrip("$")}' not in allowed_figures:
            errors.append(f'figure {match}')
    return errors


async def render_anchor(
    lines: Sequence[ReceiptLine],
    specs: Sequence[ClaimSpec],
    text: TextModel,
    writer_model: str,
    verifier_models: Sequence[str],
) -> RenderOutcome:
    """Write references, require both readers to resolve them as intended, then the message."""
    discards: list[tuple[str, str]] = []
    detail: dict[str, object] = {}
    references = await _write_references(lines, specs, text, writer_model)
    if references is None:
        return _discard(discards + [('reference_parse', 'all')], detail)
    kept = [False] * len(specs)
    resolutions: dict[int, tuple[frozenset[str], ...]] = {}
    for round_ in range(VERIFY_ROUNDS):
        pending = [i for i in range(len(specs)) if not kept[i]]
        settled = await _resolve_references(
            lines, [references[i] for i in pending], text, verifier_models
        )
        if settled is None:
            return _discard(discards + [('resolution_parse', 'all')], detail)
        for pos, i in enumerate(pending):
            resolutions[i] = settled[pos]
            if all(s == frozenset(specs[i].target_lines) for s in settled[pos]):
                kept[i] = True
            else:
                discards.append(('reference_mismatch', specs[i].kind))
        detail['resolutions'] = {i: [sorted(s) for s in sets_] for i, sets_ in resolutions.items()}
        if all(kept):
            break
        if round_ < VERIFY_ROUNDS - 1:
            rewritten = await _rewrite_references(
                lines, specs, references, resolutions, text, writer_model
            )
            if rewritten is None:
                return _discard(discards + [('reference_parse', 'all')], detail)
            for i, phrase in rewritten.items():
                references[i] = phrase
    if not all(kept):
        return _discard(discards, detail)
    rendered = await _write_message(
        lines, specs, references, text, writer_model, verifier_models, discards, detail
    )
    if rendered is None:
        return _discard(discards, detail)
    sentences = rendered
    detail['message'] = ' '.join(sentences)
    return RenderOutcome(True, tuple(references), sentences, tuple(discards), detail)


def _discard(discards: list[tuple[str, str]], detail: dict[str, object]) -> RenderOutcome:
    return RenderOutcome(False, (), (), tuple(discards), detail)


async def _write_references(
    lines: Sequence[ReceiptLine],
    specs: Sequence[ClaimSpec],
    text: TextModel,
    model: str,
) -> list[str] | None:
    prompt = _prompt(
        lines,
        'You write how a grocery customer refers to items in a support complaint.',
        _reference_instructions(specs),
        'Return JSON only: {"references": ["...", ...]} with exactly one reference per claim.',
    )
    payload = await _ask(text, model, prompt, _ReferencesPayload, WRITER_TEMPERATURE)
    if payload is None or len(payload.references) != len(specs):
        return None
    return [ref.strip() for ref in payload.references]


async def _rewrite_references(
    lines: Sequence[ReceiptLine],
    specs: Sequence[ClaimSpec],
    references: list[str],
    resolutions: dict[int, tuple[frozenset[str], ...]],
    text: TextModel,
    model: str,
) -> dict[int, str] | None:
    """Second chance for references a reader resolved differently than intended."""
    failed = [
        i
        for i, sets_ in resolutions.items()
        if not all(s == frozenset(specs[i].target_lines) for s in sets_)
    ]
    notes = []
    for i in failed:
        seen = ' and '.join(
            f'{{{", ".join(sorted(s))}}}' if s else '{no line}' for s in resolutions[i]
        )
        want = ', '.join(specs[i].target_lines) or 'no line at all'
        notes.append(
            f'{i + 1}. "{references[i]}" was read as {seen}; it must mean exactly {want}. '
            + _kind_line(specs[i])
        )
    prompt = _prompt(
        lines,
        'Rewrite the flagged item references so each one resolves exactly as required.',
        '\n'.join(notes),
        'Return JSON only: {"references": ["...", ...]} with one new reference per flagged '
        'claim, in their original order.',
    )
    payload = await _ask(text, model, prompt, _ReferencesPayload, WRITER_TEMPERATURE)
    if payload is None or len(payload.references) != len(failed):
        return None
    return {i: ref.strip() for i, ref in zip(failed, payload.references, strict=True)}


async def _resolve_references(
    lines: Sequence[ReceiptLine],
    references: Sequence[str],
    text: TextModel,
    verifier_models: Sequence[str],
) -> list[tuple[frozenset[str], ...]] | None:
    """Each verifier independently lists the lines every reference could mean."""
    valid = frozenset(line.code for line in lines)
    listing = '\n'.join(f'{i + 1}. "{ref}"' for i, ref in enumerate(references))
    prompt = _prompt(
        lines,
        'Resolve customer item references against this receipt.',
        (
            'For each reference, list every line it could plausibly refer to under a generous '
            'everyday reading: a category word covers the whole category, a brand word narrows '
            'by brand, a size word picks the clearly larger or smaller item, and a specific '
            'kind narrows to that kind. Use [] when nothing fits. Judge each reference on its '
            f'own.\n\nReferences:\n{listing}'
        ),
        'Return JSON only: {"claims": [{"lines": ["L03"]}, ...]} with one entry per reference.',
    )
    per_model: list[list[frozenset[str]]] = []
    for model in verifier_models:
        payload = await _ask(text, model, prompt, _LinesPayload, VERIFIER_TEMPERATURE)
        if payload is None or len(payload.claims) != len(references):
            return None
        per_model.append(
            [frozenset(code for code in claim.lines if code in valid) for claim in payload.claims]
        )
    return list(zip(*per_model, strict=True))


async def _write_message(
    lines: Sequence[ReceiptLine],
    specs: Sequence[ClaimSpec],
    references: Sequence[str],
    text: TextModel,
    model: str,
    verifier_models: Sequence[str],
    discards: list[tuple[str, str]],
    detail: dict[str, object],
) -> tuple[str, ...] | None:
    """One sentence per claim, joined; sentence count, leaks, and both extractions checked.

    Failed attempts record the message and verifier extractions into detail so the build
    log shows exactly what disagreed.
    """
    for _ in range(VERIFY_ROUNDS):
        payload = await _ask(
            text,
            model,
            _message_prompt(lines, specs, references),
            _MessagePayload,
            WRITER_TEMPERATURE,
        )
        if payload is None:
            discards.append(('message_parse', 'all'))
            continue
        message = payload.message.strip()
        detail['message'] = message
        sentences = split_sentences(message)
        if len(sentences) != len(specs):
            discards.append(('message_sentence_count', 'all'))
            detail['n_sentences'] = len(sentences)
            continue
        allowed = frozenset(
            f'${cents / 100:.2f}'
            for cents in (spec.stated_cents for spec in specs)
            if cents is not None
        )
        leaks = leak_errors(message, allowed)
        if leaks:
            discards.append(('message_leak', 'all'))
            detail['leaks'] = leaks
            continue
        ok, extractions = await _message_matches_plan(lines, message, specs, text, verifier_models)
        detail['extractions'] = extractions
        if not ok:
            discards.append(('message_extraction', 'all'))
            continue
        return tuple(sentences)
    return None


async def _message_matches_plan(
    lines: Sequence[ReceiptLine],
    message: str,
    specs: Sequence[ClaimSpec],
    text: TextModel,
    verifier_models: Sequence[str],
) -> tuple[bool, dict[str, list[dict[str, object] | list[list[str]]]]]:
    """Both verifiers extract the claims; keep the message only if both match the plan.

    Line sets are never judged here: each verifier's extracted item phrase goes back
    through the same bare-phrase resolution prompt that verified the references, so both
    stages read the wording under one procedure instead of two generosity regimes.
    """
    prompt = _prompt(
        lines,
        'Extract the claims from the customer message below.',
        (
            f'Customer message:\n"""\n{message}\n"""\n\n'
            'For each claim, in order, return: "type" — "price" (overcharged or wrong price), '
            '"coupon" (a coupon or discount did not apply), or "missing_item" (item not '
            'received); "item" — the item reference quoted exactly from the message, never a '
            'line code; "stated_cents" — any dollar amount the customer states, as an integer '
            'number of cents (499 for $4.99), else null.'
        ),
        'Return JSON only: {"claims": [{"type": "price", "item": "...", '
        '"stated_cents": 499}, ...]} with one entry per claim in the message.',
    )
    logged: dict[str, list[dict[str, object] | list[list[str]]]] = {}
    for model in verifier_models:
        payload = await _ask(text, model, prompt, _ExtractionPayload, VERIFIER_TEMPERATURE)
        if payload is None:
            return False, logged
        logged[model] = [claim.model_dump() for claim in payload.claims]
        if len(payload.claims) != len(specs):
            return False, logged
        for claim, spec in zip(payload.claims, specs, strict=True):
            if claim.type.strip().lower().replace(' ', '_') != spec.stated_type.value or (
                not _cents_agree(claim.stated_cents, spec.stated_cents)
            ):
                return False, logged
        settled = await _resolve_references(
            lines, [claim.item for claim in payload.claims], text, (model,)
        )
        if settled is None:
            return False, logged
        logged[f'{model}#resolve'] = [[sorted(s) for s in sets_] for sets_ in settled]
        for sets_, spec in zip(settled, specs, strict=True):
            if any(s != frozenset(spec.target_lines) for s in sets_):
                return False, logged
    return True, logged


def _cents_agree(stated: int | float | None, spec: int | None) -> bool:
    """Verifiers echo the amount as cents or as the dollar figure; both mean the same fact."""
    if spec is None:
        return stated is None or stated == 0
    if stated is None:
        return False
    return stated == spec or abs(stated - spec / 100) < 0.005


def _reference_instructions(specs: Sequence[ClaimSpec]) -> str:
    header = (
        'Write only the item reference for each claim — the few words a customer uses to name '
        'the item (for example "the navel oranges" or "the big bottle of soda"). No complaint '
        'words, no verbs, no line codes, no dollar amounts. Use a size word only when the size '
        'difference is obvious, and a brand or quantity word only when it helps.\n\nClaims:'
    )
    return (
        header + '\n' + '\n'.join(f'{i + 1}. {_kind_line(spec)}' for i, spec in enumerate(specs))
    )


def _kind_line(spec: ClaimSpec) -> str:
    if spec.kind == 'unique':
        return f'Must refer to line {spec.target_lines[0]} on this receipt and nothing else.'
    if spec.kind == 'clarify':
        return (
            f'Must be readable as any of lines {" or ".join(spec.target_lines)}, and nothing else.'
        )
    return (
        f'The customer complains about {spec.absent_item} — something they buy regularly that '
        'is not on this receipt (for example it never made it home); the wording must fit no '
        'line on this receipt.'
    )


COMPLAINT_KINDS = {
    StatedType.PRICE: 'a price complaint (feels overcharged, the shelf tag showed less)',
    StatedType.COUPON: 'a coupon complaint (a digital coupon or discount did not come off)',
    StatedType.MISSING_ITEM: (
        'a missing-item complaint (paid for it but never received it; never mention the receipt)'
    ),
}


def _message_prompt(
    lines: Sequence[ReceiptLine], specs: Sequence[ClaimSpec], references: Sequence[str]
) -> str:
    rows = []
    for i, spec in enumerate(specs):
        row = f'{i + 1}. {COMPLAINT_KINDS[spec.stated_type]} about "{references[i]}"'
        if spec.stated_cents is not None:
            row += f'; the customer says it was worth ${spec.stated_cents / 100:.2f}'
        rows.append(row)
    body = (
        f"Write the customer's support message about this receipt. It must contain exactly "
        f'{len(specs)} claims in this order, one sentence per claim, no greeting or sign-off, '
        "in the customer's own words. Use each item reference verbatim (you may add 'the' or "
        "'my', never other item words), make each claim's kind unmistakable from its wording, "
        'and when an amount is given, state it exactly as written. Do not mention line codes '
        'or receipt columns, and do not invent items, complaints, or dollar amounts.\n'
        'Vary the wording across sentences: no two sentences may open the same way or reuse '
        "the same complaint formula or stock phrase (for example don't say 'the shelf tag "
        "showed a lower price' twice). Customers write casually — 'rang up wrong', 'the price "
        "was off on', 'my coupon never applied', 'never got the' — not support-ticket "
        'language.\n\n'
        'Claims:\n' + '\n'.join(rows)
    )
    return _prompt(
        lines,
        "You write a grocery customer's message to store support.",
        body,
        'Return JSON only: {"message": "..."}',
    )


def _prompt(lines: Sequence[ReceiptLine], task: str, body: str, output: str) -> str:
    table = [
        '| line | category | sub-category | brand tier | size | qty |',
        '|---|---|---|---|---|---|',
    ]
    for line in lines:
        table.append(
            f'| {line.code} | {line.commodity} | {line.sub_commodity} |'
            f' {line.brand_tier.value} | {line.size} | {line.quantity} |'
        )
    return f'{task}\n\nReceipt:\n' + '\n'.join(table) + f'\n\n{body}\n\n{output}'


class _ReferencesPayload(BaseModel):
    model_config = ConfigDict(extra='ignore')

    references: list[str]


class _LinesEntry(BaseModel):
    model_config = ConfigDict(extra='ignore')

    lines: list[str] = []


class _LinesPayload(BaseModel):
    model_config = ConfigDict(extra='ignore')

    claims: list[_LinesEntry]


class _ExtractionEntry(BaseModel):
    model_config = ConfigDict(extra='ignore')

    type: str
    item: str
    stated_cents: int | float | None = None


class _ExtractionPayload(BaseModel):
    model_config = ConfigDict(extra='ignore')

    claims: list[_ExtractionEntry]


class _MessagePayload(BaseModel):
    model_config = ConfigDict(extra='ignore')

    message: str


async def _ask[T: BaseModel](
    text: TextModel,
    model: str,
    prompt: str,
    payload_type: type[T],
    temperature: float,
) -> T | None:
    """One completion, parsed leniently into a payload; None when the reply is unusable."""
    raw = await text.complete(model, prompt, temperature=temperature, max_tokens=MAX_TOKENS)
    match = JSON_BLOCK_RE.search(raw)
    if match is None:
        return None
    try:
        payload = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
    try:
        return payload_type.model_validate(payload)
    except ValidationError:
        return None
