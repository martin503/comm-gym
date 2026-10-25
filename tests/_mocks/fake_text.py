import json
import re
from dataclasses import dataclass

# The writer encodes each claim's intent in the reference text itself ('ref L03',
# 'ref L04|L07', 'ref none'), so the resolver and extractor fakes can re-derive the
# expected answers from the prompts without any shared state with the code under test.
CODES_RE = re.compile(r'\bL\d{2,}\b')
ROW_RE = re.compile(r'^(\d+)\. (a price|a coupon|a missing-item) complaint.*? about "(.+?)"')
WORTH_RE = re.compile(r'worth \$(\d+\.\d\d)')
KIND_UNIQUE_RE = re.compile(r'^(\d+)\. Must refer to line (L\d+)')
KIND_CLARIFY_RE = re.compile(r'^(\d+)\. Must be readable as any of lines (.+?), and nothing else')
KIND_ABSENT_RE = re.compile(r'^(\d+)\. The customer complains about')
RESOLVE_RE = re.compile(r'^(\d+)\. "(ref [^"]+)"')
INTENT_RE = re.compile(r'^(ref )(.+)$')


@dataclass
class _Row:
    type_value: str
    reference: str
    stated_cents: int | None


class FakeTextModel:
    """TextModel double: deterministic answers derived from each prompt's own intent.

    Single-flight: it records the Claims rows of the most recent message prompt so the
    extractor can answer; concurrent render_anchor calls would race that state.
    """

    def __init__(
        self,
        *,
        fail_reference: str | None = None,
        fail_reference_rounds: int = 0,
        leak_once: bool = False,
        extra_sentence_once: bool = False,
        wrong_extraction_once: bool = False,
    ) -> None:
        self.fail_reference = fail_reference
        self.fail_reference_rounds = fail_reference_rounds
        self.leak_once = leak_once
        self.extra_sentence_once = extra_sentence_once
        self.wrong_extraction_once = wrong_extraction_once
        self.calls = 0
        self.rows: list[_Row] = []

    async def complete(
        self, model: str, prompt: str, *, temperature: float, max_tokens: int
    ) -> str:
        self.calls += 1
        if prompt.startswith('You write how a grocery customer'):
            return self._write_references(prompt)
        if prompt.startswith('Rewrite the flagged'):
            return self._rewrite(prompt)
        if prompt.startswith('Resolve customer item references'):
            return self._resolve(prompt)
        if prompt.startswith('You write a grocery customer'):
            return self._write_message(prompt)
        if prompt.startswith('Extract the claims'):
            return self._extract(prompt)
        raise AssertionError(f'unrouted prompt: {prompt[:60]!r}')

    def _write_references(self, prompt: str) -> str:
        refs = {}
        for line in prompt.splitlines():
            if match := KIND_UNIQUE_RE.match(line):
                refs[int(match.group(1))] = f'ref {match.group(2)}'
            elif match := KIND_CLARIFY_RE.match(line):
                codes = CODES_RE.findall(match.group(2))
                refs[int(match.group(1))] = 'ref ' + '|'.join(codes)
            elif match := KIND_ABSENT_RE.match(line):
                refs[int(match.group(1))] = 'ref none'
        ordered = [refs[i] for i in sorted(refs)]
        return json.dumps({'references': ordered})

    def _rewrite(self, prompt: str) -> str:
        refs = []
        for line in prompt.splitlines():
            match = re.match(r'^(\d+)\. ".+?" was read as .+?; it must mean exactly (.+?)\.', line)
            if match is None:
                continue
            want = match.group(2)
            refs.append(
                'ref none'
                if want == 'no line at all'
                else 'ref ' + '|'.join(CODES_RE.findall(want))
            )
        return json.dumps({'references': refs})

    def _resolve(self, prompt: str) -> str:
        claims = []
        for line in prompt.splitlines():
            match = RESOLVE_RE.match(line)
            if match is None:
                continue
            reference = match.group(2)
            codes = self._codes_of(reference)
            if reference == self.fail_reference and self.fail_reference_rounds > 0:
                self.fail_reference_rounds -= 1
                # 'L99' is not on any receipt, so the renderer filters it to no line at all
                codes = ['L99']
            claims.append({'lines': codes})
        return json.dumps({'claims': claims})

    def _write_message(self, prompt: str) -> str:
        self.rows = []
        sentences = []
        for line in prompt.splitlines():
            match = ROW_RE.match(line)
            if match is None:
                continue
            index, kind, reference = int(match.group(1)), match.group(2), match.group(3)
            stated = WORTH_RE.search(line)
            cents = int(round(float(stated.group(1)) * 100)) if stated else None
            type_value = {
                'a price': 'price',
                'a coupon': 'coupon',
                'a missing-item': 'missing_item',
            }[kind]
            self.rows.append(_Row(type_value, reference, cents))
            sentence = f'Claim {index}: trouble with this item.'
            if cents is not None:
                sentence = f'Claim {index}: it was worth ${cents / 100:.2f} to me.'
            if self.leak_once:
                sentence += '(see L01)'
            sentences.append(sentence)
        if self.extra_sentence_once:
            sentences.append('Please help.')
            self.extra_sentence_once = False
        self.leak_once = False
        return json.dumps({'message': ' '.join(sentences)})

    def _extract(self, prompt: str) -> str:
        claims = []
        for index, row in enumerate(self.rows, start=1):
            entry = {
                'type': row.type_value,
                'item': row.reference,
                'stated_cents': row.stated_cents,
            }
            if self.wrong_extraction_once and index == 1:
                entry['type'] = 'missing_item'
            claims.append(entry)
        self.wrong_extraction_once = False
        return json.dumps({'claims': claims})

    def _codes_of(self, reference: str) -> list[str]:
        intent = INTENT_RE.match(reference)
        if intent is None or intent.group(2) == 'none':
            return []
        return intent.group(2).split('|')
