import re
from collections.abc import Sequence
from dataclasses import dataclass

from commgym.refund.instance import ReceiptLine, Reference
from commgym.refund.wordmap import WORD_CATEGORIES

# nouns whose plural is not word + 's'; those never get the quantity reference style
IRREGULAR_PLURALS: dict[str, str] = {
    'milk': 'milk',
    'bread': 'bread',
    'beef': 'beef',
    'pork': 'pork',
    'chicken': 'chicken',
    'meat': 'meat',
    'poultry': 'poultry',
    'candy': 'candy',
    'lettuce': 'lettuce',
    'rice': 'rice',
    'baking supplies': 'baking supplies',
    'cleaning supplies': 'cleaning supplies',
    'paper products': 'paper products',
    'feminine hygiene': 'feminine hygiene',
    'ice cream': 'ice cream',
    'berries': 'berries',
    'peaches': 'peaches',
    'potatoes': 'potatoes',
    'tomatoes': 'tomatoes',
    'grapes': 'grapes',
    'chips': 'chips',
    'nuts': 'nuts',
    'dips': 'dips',
    'frozen fries': 'frozen fries',
    'canned beans': 'canned beans',
    'canned vegetables': 'canned vegetables',
    'frozen vegetables': 'frozen vegetables',
    'school supplies': 'school supplies',
    'vegetables': 'vegetables',
}

SIZE_RE = re.compile(
    r'(\d+(?:\.\d+)?)\s*(OZ|OUNCE|OUNCES|LB|LBS|POUND|POUNDS|LT|LITER|LITERS|L|ML|'
    r'GAL|QT|PT|CT|COUNT|PK|PACK)\b',
    re.IGNORECASE,
)
# displayed sizes mix weight, volume, and count units; comparisons only run within one unit
COMPARABLE_UNITS = ('OZ', 'LB', 'LT', 'ML', 'GAL', 'QT', 'PT', 'CT', 'PACK')

QUANTITY_WORDS: dict[int, str] = {
    2: 'two',
    3: 'three',
    4: 'four',
    5: 'five',
    6: 'six',
    7: 'seven',
    8: 'eight',
    9: 'nine',
    10: 'ten',
    11: 'eleven',
    12: 'twelve',
}
# claims say 'name-brand'; coupon coverage descriptions say 'national-brand'
TIER_WORDS = {'Private': 'store-brand', 'National': 'name-brand'}
# a size rung only counts when the target beats its neighbors by this factor; closer sizes
# (16.9 vs 12 OZ) are arguable and never become size references
SIZE_MARGIN = 1.5

# inverse of the parser's word map; word order feeds the reference ladder and rng choices,
# so it must be deterministic. Shortest-first: generic words ('yogurt') are preferred over
# specific-sounding ones ('greek yogurt') so claims never over-specify the category.
_order = sorted(WORD_CATEGORIES, key=lambda word: (len(word), word))
WORDS_BY_CATEGORY: dict[str, tuple[str, ...]] = {}
for _word in _order:
    for _category in WORD_CATEGORIES[_word]:
        WORDS_BY_CATEGORY[_category] = (*WORDS_BY_CATEGORY.get(_category, ()), _word)


@dataclass(frozen=True, slots=True)
class SizeSpec:
    value: float
    unit: str


def words_of(category: str) -> tuple[str, ...]:
    """Customer words that can refer to this receipt category."""
    return WORDS_BY_CATEGORY.get(category, ())


def plural_of(word: str) -> str:
    return IRREGULAR_PLURALS.get(word, f'{word}s')


def parse_size(text: str) -> SizeSpec | None:
    """First parseable measurement in the product-size free text, normalized to upper unit."""
    if not text:
        return None
    if re.search(r'\d\s*/\s*\d', text):
        # multipack shorthand like '6/12 OZ' (six 12-oz packs) is not a unit size
        return None
    match = SIZE_RE.search(text)
    if match is None:
        return None
    unit = match.group(2).upper()
    unit = {
        'OUNCES': 'OZ',
        'OUNCE': 'OZ',
        'LBS': 'LB',
        'POUND': 'LB',
        'POUNDS': 'LB',
        'LITERS': 'LT',
        'LITER': 'LT',
        'COUNT': 'CT',
        'PK': 'PACK',
    }.get(unit, unit)
    return SizeSpec(float(match.group(1)), unit)


def _tokens(text: str) -> frozenset[str]:
    return frozenset(part for part in re.split(r'[^a-z0-9]+', text.lower()) if part)


def _is_generic(word: str, categories: frozenset[str]) -> bool:
    """A word that merely echoes a category name is generic and never sub-grounded."""
    return any(_tokens(word) <= _tokens(category) for category in categories)


def resolve_reference(ref: Reference, lines: Sequence[ReceiptLine]) -> tuple[str, ...]:
    """Receipt codes a claim's word points at; modifiers narrow the word-matched lines in order."""
    categories = WORD_CATEGORIES.get(ref.word)
    if categories is None:
        return ()
    matched = [line for line in lines if line.commodity in categories]
    if not _is_generic(ref.word, categories):
        # a specific word ('ricotta', 'greek yogurt') names a sub-kind: when some matched
        # line's sub-category carries that kind, only those lines count
        grounded = [line for line in matched if _tokens(ref.word) <= _tokens(line.sub_commodity)]
        if grounded:
            matched = grounded
    if ref.brand_tier is not None:
        matched = [line for line in matched if line.brand_tier == ref.brand_tier]
    if ref.size_cmp is not None:
        sized = [(line, parse_size(line.size)) for line in matched]
        if any(spec is None for _, spec in sized):
            # an unparseable size among candidates makes the comparison undecidable
            return tuple(line.code for line in matched)
        units = {spec.unit for _, spec in sized if spec is not None}
        if len(units) != 1:
            return tuple(line.code for line in matched)
        values = [spec.value for _, spec in sized if spec is not None]
        target_value = max(values) if ref.size_cmp == 'bigger' else min(values)
        matched = [line for line, spec in sized if spec is not None and spec.value == target_value]
    if ref.quantity is not None:
        matched = [line for line in matched if line.quantity == ref.quantity]
    return tuple(line.code for line in matched)


# the ladder no longer feeds label generation (claim wording is LLM-written and independently
# verified); scripts/refund/feasibility.py, the frozen gate record, still imports it
def unique_reference(
    line: ReceiptLine, lines: Sequence[ReceiptLine]
) -> tuple[Reference, str] | None:
    """Word-first ladder: first word whose bare match or one-modifier match pins this line."""
    available = words_of(line.commodity)
    # words naming this line's sub-kind ('ricotta' on a ricotta line) come first, longest
    # first; generic words follow in the usual shortest-first order
    grounded = [
        word
        for word in available
        if not _is_generic(word, WORD_CATEGORIES[word])
        and _tokens(word) <= _tokens(line.sub_commodity)
    ]
    ordered = sorted(grounded, key=len, reverse=True) + [
        word for word in available if word not in set(grounded)
    ]
    for word in ordered:
        rungs: list[tuple[Reference, str]] = [(Reference(word=word), 'word')]
        others = [
            other
            for other in lines
            if other is not line and other.commodity in WORD_CATEGORIES[word]
        ]
        if others:
            rungs.append((Reference(word=word, brand_tier=line.brand_tier), 'brand_tier'))
            size_cmp = _size_comparison(line, others)
            if size_cmp is not None:
                rungs.append((Reference(word=word, size_cmp=size_cmp), 'size'))
            if plural_of(word) != word and line.quantity >= 2:
                rungs.append((Reference(word=word, quantity=line.quantity), 'quantity'))
        for ref, style in rungs:
            if resolve_reference(ref, lines) == (line.code,):
                return ref, style
    return None


def _size_comparison(line: ReceiptLine, others: Sequence[ReceiptLine]) -> str | None:
    """'bigger'/'smaller' when every same-word line parses to one unit and this line is extreme."""
    specs = [parse_size(other.size) for other in others]
    own = parse_size(line.size)
    if own is None or any(spec is None for spec in specs):
        return None
    units = {spec.unit for spec in specs if spec is not None} | {own.unit}
    if len(units) != 1:
        return None
    values = [spec.value for spec in specs if spec is not None]
    if own.value >= SIZE_MARGIN * max(values):
        return 'bigger'
    if own.value * SIZE_MARGIN <= min(values):
        return 'smaller'
    return None
