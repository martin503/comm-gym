import re
from collections.abc import Sequence
from dataclasses import dataclass

from commgym.dunnhumby.types import BrandTier
from commgym.refund.instance import ReceiptLine
from commgym.refund.lexicon import parse_size

# coverage grammar: '[national-brand|store-brand] <category> [<n> <unit> and larger|smaller]'
# with one global 'except <sub-category>, ...' clause; category/sub text is verbatim from the
# receipt columns (lowercased) so the model can check coverage by string comparison
TIER_WORDS_COVERAGE = {'national-brand': BrandTier.NATIONAL, 'store-brand': BrandTier.PRIVATE}
BOUND_RE = re.compile(
    r'(\d+(?:\.\d+)?)\s*(oz|lb|lt|ml|gal|qt|pt|ct|pack)\s+and\s+(larger|smaller)\s*$'
)


@dataclass(frozen=True, slots=True)
class PhraseSpec:
    """One parsed coverage phrase: optional tier and size bound over a verbatim category."""

    category: str
    tier: BrandTier | None
    bound_value: float | None
    bound_unit: str | None
    direction: str | None


def coverage_of(text: str, lines: Sequence[ReceiptLine]) -> tuple[str, ...]:
    """Receipt codes a coverage description selects; the text-level inverse of the writer."""
    body, exclusions = _split_exclusions(text)
    selected: set[str] = set()
    for phrase in _split_phrases(body):
        spec = _parse_phrase(phrase)
        if spec is not None:
            selected |= _select_codes(spec, lines)
    blocked = {line.code for line in lines if line.sub_commodity.lower() in exclusions}
    return tuple(sorted(selected - blocked))


def describe_coverage(covered_codes: Sequence[str], lines: Sequence[ReceiptLine]) -> str | None:
    """Shortest exact attribute description of the covered lines, or None if none exists."""
    covered = {line.code: line for line in lines if line.code in set(covered_codes)}
    assert covered, 'coverage describes at least one displayed line'
    if any(',' in line.sub_commodity for line in lines):
        # the exclusion clause splits on commas, so a comma inside a sub-category is unusable
        return None
    keep_subs = {line.sub_commodity.lower() for line in covered.values()}
    phrases: list[str] = []
    selected: set[str] = set()
    exclusions: set[str] = set()
    groups = sorted({(item.commodity, item.brand_tier) for item in covered.values()})
    for commodity, tier in groups:
        group = [line for line in lines if line.commodity == commodity and line.brand_tier == tier]
        targets = {code for code in covered if code in {line.code for line in group}}
        found = _describe_group(group, targets, keep_subs)
        if found is None:
            return None
        phrase, chosen, subs = found
        phrases.append(phrase)
        selected |= chosen
        exclusions |= subs
    blocked = {line.code for line in lines if line.sub_commodity.lower() in exclusions}
    if selected - blocked != set(covered):
        return None
    text = ', '.join(phrases)
    if exclusions:
        text += ', except ' + ', '.join(sorted(exclusions))
    return text


def _describe_group(
    group: list[ReceiptLine], targets: set[str], keep_subs: set[str]
) -> tuple[str, set[str], set[str]] | None:
    """One (category, tier) group: a phrase, its selected codes, and the exclusions it needs."""
    for phrase, chosen in _group_candidates(group, targets):
        overshoot = [line for line in group if line.code in chosen and line.code not in targets]
        subs = {line.sub_commodity.lower() for line in overshoot}
        if subs & keep_subs or not targets <= chosen:
            continue
        return phrase, set(chosen), subs
    return None


def _group_candidates(
    group: list[ReceiptLine], targets: set[str]
) -> list[tuple[str, frozenset[str]]]:
    """Phrases for one group in preference order: plain category first, then size bounds."""
    tier_word = 'national-brand' if group[0].brand_tier is BrandTier.NATIONAL else 'store-brand'
    base = f'{tier_word} {group[0].commodity.lower()}'
    codes = frozenset(line.code for line in group)
    candidates = [(base, codes)]
    specs = {line.code: parse_size(line.size) for line in group}
    sizes = [spec for spec in specs.values() if spec is not None]
    if len(sizes) == len(specs) and len({spec.unit for spec in sizes}) == 1:
        unit = sizes[0].unit
        edges = sorted({spec.value for code in targets if (spec := specs[code]) is not None})
        for direction, edge in (
            ('larger', edges[0]),
            ('larger', edges[-1]),
            ('smaller', edges[-1]),
            ('smaller', edges[0]),
        ):
            keep = frozenset(
                code
                for code, spec in specs.items()
                if spec is not None
                and (spec.value >= edge if direction == 'larger' else spec.value <= edge)
            )
            candidates.append((f'{base} {edge:g} {unit.lower()} and {direction}', keep))
    return candidates


def _split_exclusions(text: str) -> tuple[str, frozenset[str]]:
    if ', except ' not in text:
        return text, frozenset()
    body, tail = text.split(', except ', 1)
    return body, frozenset(part.strip().lower() for part in tail.split(','))


def _split_phrases(body: str) -> list[str]:
    phrases = []
    for part in body.split(','):
        phrase = part.strip()
        if phrase[:4].lower() == 'and ':
            phrase = phrase[4:]
        if phrase:
            phrases.append(phrase)
    return phrases


def _parse_phrase(phrase: str) -> PhraseSpec | None:
    text = phrase.strip().lower()
    tier = None
    for word, value in TIER_WORDS_COVERAGE.items():
        if text.startswith(f'{word} '):
            tier = value
            text = text[len(word) + 1 :]
            break
    bound_value = bound_unit = direction = None
    match = BOUND_RE.search(text)
    if match is not None:
        bound_value = float(match.group(1))
        bound_unit = match.group(2).upper()
        direction = match.group(3)
        text = text[: match.start()].strip()
    if not text:
        return None
    return PhraseSpec(
        category=text,
        tier=tier,
        bound_value=bound_value,
        bound_unit=bound_unit,
        direction=direction,
    )


def _select_codes(spec: PhraseSpec, lines: Sequence[ReceiptLine]) -> set[str]:
    selected: set[str] = set()
    for line in lines:
        if line.commodity.lower() != spec.category:
            continue
        if spec.tier is not None and line.brand_tier != spec.tier:
            continue
        if spec.bound_value is not None:
            size = parse_size(line.size)
            if size is None or size.unit != spec.bound_unit:
                continue
            if spec.direction == 'larger' and size.value < spec.bound_value:
                continue
            if spec.direction == 'smaller' and size.value > spec.bound_value:
                continue
        selected.add(line.code)
    return selected
