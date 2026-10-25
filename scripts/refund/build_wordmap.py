import argparse
import json
import re
from collections.abc import Sequence
from pathlib import Path

import anyio
from anyio import Semaphore, create_task_group
from loguru import logger
from tqdm import tqdm

from commgym.core.logging import setup_logging
from commgym.core.openrouter import OpenRouterClient, load_api_key
from commgym.dunnhumby.load import Product, load_products
from commgym.refund.lexicon import WORDS_BY_CATEGORY
from commgym.refund.wordmap import WORD_CATEGORIES

HARVEST_CONCURRENCY = 4
WORD_RE = re.compile(r'"([^"\n]{2,30})"')
OUT_DIR = Path('experiments/261024_wordmap_curation')


async def amain(args: argparse.Namespace) -> None:
    setup_logging()
    categories = sorted(WORDS_BY_CATEGORY)
    examples = _category_examples(args.data_dir, categories)
    if args.harvest:
        client = OpenRouterClient(load_api_key({}, args.env_file))
        words_by_category = await _harvest(client, args.model, categories, examples)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(words_by_category, indent=2, sort_keys=True) + '\n')
        logger.success(
            'harvested {} categories from {} -> {}', len(words_by_category), args.model, args.out
        )
    else:
        _merge(args.a, args.b)


async def _harvest(
    client: OpenRouterClient,
    model: str,
    categories: Sequence[str],
    examples: dict[str, str],
) -> dict[str, list[str]]:
    """One small completion per category: the everyday words customers use for it."""
    harvested: dict[str, list[str]] = {}
    lock = anyio.Lock()
    semaphore = Semaphore(HARVEST_CONCURRENCY)
    bar = tqdm(total=len(categories), desc=model.split('/')[-1], unit='cat')

    async def one(category: str) -> None:
        prompt = (
            f'Grocery category: "{category}" (examples of items in it: {examples[category]}).\n'
            'List up to 6 short everyday words or two-word phrases a customer would use for '
            'items in this category when complaining to store support. Plain lowercase words.\n'
            'Return JSON only: {"words": ["chips", "pretzels"]}'
        )
        async with semaphore:
            try:
                result = await client.chat(
                    model,
                    [
                        {
                            'role': 'system',
                            'content': 'You build grocery vocabularies. JSON only.',
                        },
                        {'role': 'user', 'content': prompt},
                    ],
                    temperature=0.0,
                    # reasoning tokens count against max_tokens, so the budget must cover
                    # the thinking plus the one-line JSON answer
                    max_tokens=2048,
                )
            except Exception as exc:
                logger.error('{}: {}', category, exc)
                bar.update(1)
                return
        words = _parse_words(result.text)
        async with lock:
            harvested[category] = words
        bar.update(1)

    async with create_task_group() as tasks:
        for category in categories:
            tasks.start_soon(one, category)
    bar.close()
    return harvested


def _parse_words(text: str) -> list[str]:
    """Words from a JSON reply, falling back to any quoted strings in the text."""
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match is not None:
        try:
            payload = json.loads(match.group(0))
        except json.JSONDecodeError:
            payload = None
        if isinstance(payload, dict) and isinstance(payload.get('words'), list):
            return _normalize(payload['words'])
    return _normalize(WORD_RE.findall(text))


def _normalize(raw: Sequence[object]) -> list[str]:
    words: list[str] = []
    for item in raw:
        if not isinstance(item, str):
            continue
        word = item.strip().strip('.').lower()
        if word and word not in words:
            words.append(word)
    return words


def _category_examples(data_dir: Path, categories: Sequence[str]) -> dict[str, str]:
    """Up to six real sub-category strings per category, straight from the products table."""
    products: list[Product] = load_products(data_dir)
    subs: dict[str, set[str]] = {}
    for product in products:
        if product.commodity in set(categories) and product.sub_commodity:
            subs.setdefault(product.commodity, set()).add(product.sub_commodity)
    return {category: ', '.join(sorted(subs.get(category, set()))[:6]) for category in categories}


def _merge(a_path: Path, b_path: Path) -> None:
    """Frozen map = seed links plus links both harvests agree on; rest listed for review."""
    a = _links(a_path)
    b = _links(b_path)
    seed = {(word, category) for word, cats in WORD_CATEGORIES.items() for category in cats}
    accepted = seed | (a & b)
    review = sorted((a ^ b) - seed)
    words: dict[str, set[str]] = {}
    for word, category in accepted:
        words.setdefault(word, set()).add(category)
    lines = [
        '# Frozen customer-word map: word -> receipt categories it can refer to.',
        '# Seed is the hand-curated CATEGORY_NOUNS inverse plus the cereal/oatmeal fix;',
        '# build_wordmap.py --merge extends it from two LLM harvests (agreement-only,',
        '# disagreements reviewed by hand). Disclose as LLM-assisted curation on the slides.',
        'WORD_CATEGORIES: dict[str, frozenset[str]] = {',
    ]
    for word in sorted(words):
        cats = ', '.join(repr(c) for c in sorted(words[word]))
        lines.append(f'    {word!r}: frozenset({{{cats}}}),')
    lines.append('}')
    target = Path('src/commgym/refund/wordmap.py')
    target.write_text('\n'.join(lines) + '\n')
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with (OUT_DIR / 'review.md').open('w') as f:
        f.write('# One-model-only word links (excluded by the agreement rule)\n\n')
        f.write(
            '| word | category | in harvest A | in harvest B | in seed |\n|---|---|---|---|---|\n'
        )
        for word, category in review:
            f.write(
                f'| {word} | {category} | {"x" if (word, category) in a else ""} '
                f'| {"x" if (word, category) in b else ""} '
                f'| {"x" if (word, category) in seed else ""} |\n'
            )
    logger.success(
        '{} words frozen ({} links: {} seed + {} agreed); {} links excluded pending review '
        '-> {} ; wordmap written to {}',
        len(words),
        len(accepted),
        len(seed),
        len(a & b) - len(seed & (a & b)),
        len(review),
        OUT_DIR / 'review.md',
        target,
    )


def _links(path: Path) -> set[tuple[str, str]]:
    payload = json.loads(path.read_text())
    assert isinstance(payload, dict), 'harvest files map category -> word list'
    return {(word, category) for category, words in payload.items() for word in _normalize(words)}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Two-model LLM curation of the frozen customer-word map'
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        '--harvest', action='store_true', help='ask one model for per-category words'
    )
    mode.add_argument(
        '--merge', action='store_true', help='merge two harvests into the frozen word map'
    )
    parser.add_argument('--model', default='openai/gpt-6-luna')
    parser.add_argument('--out', type=Path, default=OUT_DIR / 'harvest_a.json')
    parser.add_argument('--a', type=Path, default=OUT_DIR / 'harvest_a.json')
    parser.add_argument('--b', type=Path, default=OUT_DIR / 'harvest_b.json')
    parser.add_argument('--env-file', type=Path, default=Path('.env'))
    parser.add_argument('--data-dir', type=Path, default=Path('data'))
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    args = _parse_args()
    setup_logging()
    anyio.run(amain, args)
