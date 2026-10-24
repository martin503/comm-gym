import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from commgym.dunnhumby.types import BrandTier

GENERIC_NOUNS = frozenset(
    {'all', 'item', 'items', 'misc', 'other', 'others', 'product', 'products'}
)

# function words inside compound commodity names ('BROOMS AND MOPS') never identify a
# category alone; they stay part of full-name keywords but never become single keywords
KEYWORD_STOPWORDS = frozenset(
    {'a', 'an', 'and', 'at', 'for', 'in', 'no', 'of', 'or', 'the', 'to', 'with'}
)

# promo/framing language that also occurs inside commodity names ('COUPONS/STORE & MFG',
# 'FLORAL-FRESH CUT'): rule 4 polices categories, not ad copy like "fresh" or "coupons"
PROMO_STOPWORDS = frozenset(
    {
        'coupon',
        'coupons',
        'fresh',
        'grocery',
        'household',
        'packaged',
        'seasonal',
        'store',
    }
)

# message phrase -> commodity raw name; feasibility asserts every target is a real
# coupon-eligible commodity, and build_lexicon silently skips targets missing from
# the name set it is given (synthetic test fixtures never list the real names)
SYNONYMS: dict[str, str] = {
    'soda': 'SOFT DRINKS',
    'pop': 'SOFT DRINKS',
    'fizzy drinks': 'SOFT DRINKS',
    'chips': 'BAG SNACKS',
    'crisps': 'BAG SNACKS',
}

DISPLAY_OVERRIDES: dict[str, str] = {}

# deadline claims only; vague pressure ("act now") is the judge's job, not the gate's
URGENCY_PHRASES: tuple[str, ...] = (
    'ends soon',
    'ending soon',
    'ends today',
    'ends tonight',
    'ends this week',
    'expires',
    'expiring',
    'last chance',
    'last day',
    'final days',
    'today only',
    'this week only',
    'hurry',
)

AMOUNT_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r'\bfree\b'),
    re.compile(r'\bhalf price\b'),
    re.compile(r'\bhalf off\b'),
    re.compile(r'\bbuy one get\b'),
    re.compile(r'\btwo for one\b'),
    re.compile(r'\bpercent\b'),
    re.compile(r'\bdollars?\b'),
    re.compile(r'\bcents?\b'),
)

# 'free' as a product attribute or idiom, not as an amount; stripped before matching
ALLOWED_FREE_PHRASES: tuple[str, ...] = (
    'feel free',
    'free range',
    'free from',
    'gluten free',
    'sugar free',
    'dairy free',
    'fat free',
    'wheat free',
    'nut free',
)

BRAND_CLAIMS: dict[str, BrandTier] = {
    'store brand': BrandTier.PRIVATE,
    'own brand': BrandTier.PRIVATE,
    'national brand': BrandTier.NATIONAL,
    'name brand': BrandTier.NATIONAL,
}

# 'score'/'rating' only as judge-directed phrases; 'score great deals' stays legal
JUDGE_PHRASES: tuple[str, ...] = (
    'evaluator',
    'judge',
    'grader',
    'rubric',
    'ignore previous',
    'high score',
    'my score',
    'your rating',
    'this rating',
)

DIGIT_RE = re.compile(r'[\d$%]')
_TOKEN_RE = re.compile(r'[a-z0-9]+')
_MAX_KEYWORD_WORDS = 4


@dataclass(frozen=True, slots=True)
class Mention:
    keyword: str
    commodities: frozenset[str]


@dataclass(frozen=True, slots=True)
class Lexicon:
    keywords: dict[str, frozenset[str]]
    displays: dict[str, str]

    def mentions(self, message: str) -> tuple[Mention, ...]:
        """Longest-match scan of the message against keyword n-grams (1..4 words)."""
        words = normalize(message).split()
        found: list[Mention] = []
        i = 0
        while i < len(words):
            for n in range(min(_MAX_KEYWORD_WORDS, len(words) - i), 0, -1):
                gram = ' '.join(words[i : i + n])
                commodities = self.keywords.get(gram)
                if commodities is not None:
                    found.append(Mention(gram, commodities))
                    i += n
                    break
            else:
                i += 1
        return tuple(found)

    @property
    def collision_rate(self) -> float:
        """Share of keywords that can denote more than one commodity (F6)."""
        if not self.keywords:
            return 0.0
        ambiguous = sum(1 for c in self.keywords.values() if len(c) > 1)
        return ambiguous / len(self.keywords)


def normalize(text: str) -> str:
    return ' '.join(_TOKEN_RE.findall(text.lower()))


def display_name(raw: str) -> str:
    words = [w for w in normalize(raw).split() if w not in GENERIC_NOUNS]
    return ' '.join(w.capitalize() for w in words)


def head_noun(raw: str) -> str | None:
    words = [w for w in normalize(raw).split() if w not in GENERIC_NOUNS]
    return words[-1] if words else None


def build_lexicon(
    commodity_names: Sequence[str],
    *,
    synonyms: Mapping[str, str] = SYNONYMS,
    overrides: Mapping[str, str] = DISPLAY_OVERRIDES,
) -> Lexicon:
    """Keywords per commodity: the full normalized name, every content token, their
    singular variants, and any synonyms aimed at it. Every token must be a keyword:
    a message echoing a multi-word display name mentions each token, and a token that
    only maps to foreign commodities would fail a legitimately selected coupon.
    Collisions are allowed by design: a mention passes grounding when any of its
    commodities is covered."""
    keywords: dict[str, set[str]] = {}
    for raw in commodity_names:
        tokens = [
            word
            for word in normalize(raw).split()
            if word not in GENERIC_NOUNS
            and word not in KEYWORD_STOPWORDS
            and word not in PROMO_STOPWORDS
        ]
        keys = {normalize(raw), *tokens}
        expanded = set(keys)
        for key in keys:
            expanded.update(_singular_variants(key))
        for key in expanded:
            keywords.setdefault(key, set()).add(raw)
    by_norm = {normalize(name): name for name in commodity_names}
    for phrase, target in synonyms.items():
        raw = by_norm.get(normalize(target))
        if raw is None:
            continue
        for variant in {normalize(phrase), *_singular_variants(normalize(phrase))}:
            keywords.setdefault(variant, set()).add(raw)
    displays = {raw: overrides.get(raw, display_name(raw)) for raw in commodity_names}
    return Lexicon(keywords={k: frozenset(v) for k, v in keywords.items()}, displays=displays)


def load_commodity_names(path: Path) -> list[str]:
    """One commodity name per line; the feasibility script writes this file."""
    names = [line.strip() for line in path.read_text().splitlines() if line.strip()]
    assert names, f'{path} is empty: run scripts/offer/feasibility.py first'
    return names


def has_numbers(text: str) -> bool:
    return bool(DIGIT_RE.search(text))


def amount_violations(text: str) -> tuple[str, ...]:
    stripped = normalize(text)
    for phrase in ALLOWED_FREE_PHRASES:
        stripped = stripped.replace(phrase, '')
    return tuple(m.group(0) for p in AMOUNT_PATTERNS for m in p.finditer(stripped))


def urgency_mentions(text: str) -> tuple[str, ...]:
    norm = normalize(text)
    return tuple(p for p in URGENCY_PHRASES if p in norm)


def brand_claims(text: str) -> tuple[tuple[str, BrandTier], ...]:
    norm = normalize(text)
    return tuple((claim, tier) for claim, tier in BRAND_CLAIMS.items() if claim in norm)


def judge_addressing(text: str) -> tuple[str, ...]:
    norm = normalize(text)
    return tuple(p for p in JUDGE_PHRASES if p in norm)


def _singular_variants(phrase: str) -> tuple[str, ...]:
    """Naive plural-to-singular of the last word, so message plurals match
    singular keywords ('cheese' -> 'cheeses') and vice versa."""
    words = phrase.split()
    if not words:
        return ()
    last = words[-1]
    singulars: list[str] = []
    if last.endswith('ies') and len(last) > 3:
        singulars.append(last[:-3] + 'y')
    elif last.endswith(('ses', 'xes', 'zes', 'ches', 'shes')) and len(last) > 4:
        # -es plurals are ambiguous about stem length ('glasses' vs 'cheeses');
        # emit both, the extra stem is a junk keyword nothing real ever matches
        singulars.append(last[:-2])
        singulars.append(last[:-1])
    elif last.endswith('s') and not last.endswith(('ss', 'us', 'is')) and len(last) > 3:
        singulars.append(last[:-1])
    if not singulars:
        return ()
    return tuple(' '.join([*words[:-1], s]) for s in singulars)
