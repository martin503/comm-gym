import pytest
from _mocks.fake_text import FakeTextModel

from commgym.dunnhumby.types import BrandTier
from commgym.refund.instance import ReceiptLine
from commgym.refund.policy import StatedType
from commgym.refund.renderer import ClaimSpec, leak_errors, render_anchor, split_sentences


def _line(
    code: str,
    commodity: str,
    *,
    sub: str = 'MISC',
    brand: BrandTier = BrandTier.NATIONAL,
    size: str = '12 OZ',
    quantity: int = 1,
) -> ReceiptLine:
    return ReceiptLine(
        code=code,
        product_id=ord(code[1]) * 100 + int(code[2:]),
        commodity=commodity,
        sub_commodity=sub,
        brand_tier=brand,
        size=size,
        quantity=quantity,
        regular_unit_cents=200,
        loyalty_disc_unit_cents=0,
        coupon_disc_unit_cents=0,
        paid_unit_cents=200,
        reference_cents=200,
    )


LINES = (
    _line('L01', 'YOGURT', sub='GREEK YOGURT', brand=BrandTier.PRIVATE, size='6 OZ'),
    _line('L02', 'YOGURT', sub='REGULAR YOGURT', size='32 OZ'),
    _line('L03', 'COFFEE', quantity=3),
)


def test_split_sentences_keeps_dollar_amounts_together():
    assert split_sentences('I paid $4.99. Also, the coupon!') == [
        'I paid $4.99.',
        'Also, the coupon!',
    ]


def test_leak_errors_flags_codes_and_stray_figures():
    allowed = frozenset({'$4.99'})
    assert {
        'allowed': leak_errors('it cost $4.99 today', allowed),
        'line': leak_errors('see line L03', allowed),
        'coupon': leak_errors('coupon C02 again', allowed),
        'stray': leak_errors('it was $ 5.00', allowed),
        'bare': leak_errors('charged 4.98 for it', allowed),
        'size_ok': leak_errors('the 16.9 OZ one', allowed),
    } == {
        'allowed': [],
        'line': ['line code L03'],
        'coupon': ['coupon code C02'],
        'stray': ['figure $ 5.00'],
        'bare': ['figure 4.98'],
        'size_ok': [],
    }


@pytest.mark.anyio
async def test_render_anchor_happy_path(fake_text: FakeTextModel):
    specs = (
        ClaimSpec(StatedType.PRICE, 'unique', ('L03',), None, None),
        ClaimSpec(StatedType.COUPON, 'clarify', ('L01', 'L02'), None, None),
        ClaimSpec(StatedType.MISSING_ITEM, 'absent', (), 'FROZEN WAFFLES', None),
    )
    outcome = await render_anchor(LINES, specs, fake_text, 'writer', ('v1', 'v2'))
    assert {
        'ok': outcome.ok,
        'n_refs': len(outcome.references),
        'n_sentences': len(outcome.sentences),
        'message_sentences': len(split_sentences(' '.join(outcome.sentences))),
        'discards': outcome.discards,
        'resolutions': outcome.detail['resolutions'],
    } == {
        'ok': True,
        'n_refs': 3,
        'n_sentences': 3,
        'message_sentences': 3,
        'discards': (),
        'resolutions': {0: [['L03'], ['L03']], 1: [['L01', 'L02'], ['L01', 'L02']], 2: [[], []]},
    }


@pytest.mark.anyio
async def test_render_anchor_stated_number_round_trips(fake_text: FakeTextModel):
    specs = (
        ClaimSpec(StatedType.PRICE, 'unique', ('L03',), None, 499),
        ClaimSpec(StatedType.MISSING_ITEM, 'absent', (), 'FROZEN WAFFLES', None),
    )
    outcome = await render_anchor(LINES, specs, fake_text, 'writer', ('v1',))
    assert {
        'ok': outcome.ok,
        'message': outcome.detail['message'],
        'stated': '$4.99' in ' '.join(outcome.sentences),
    } == {
        'ok': True,
        'message': 'Claim 1: it was worth $4.99 to me. Claim 2: trouble with this item.',
        'stated': True,
    }


@pytest.mark.anyio
async def test_disagreement_cleared_by_the_rewrite_round(flaky_text: FakeTextModel):
    specs = (
        ClaimSpec(StatedType.PRICE, 'unique', ('L01',), None, None),
        ClaimSpec(StatedType.PRICE, 'unique', ('L03',), None, None),
    )
    outcome = await render_anchor(LINES, specs, flaky_text, 'writer', ('v1', 'v2'))
    assert {
        'ok': outcome.ok,
        'discards': outcome.discards,
        'first_ref_changed': outcome.references[0] == 'ref L01',
    } == {'ok': True, 'discards': (('reference_mismatch', 'unique'),), 'first_ref_changed': True}


@pytest.mark.anyio
async def test_persistent_disagreement_discards_the_anchor(stubborn_text: FakeTextModel):
    specs = (
        ClaimSpec(StatedType.PRICE, 'unique', ('L01',), None, None),
        ClaimSpec(StatedType.PRICE, 'unique', ('L03',), None, None),
    )
    outcome = await render_anchor(LINES, specs, stubborn_text, 'writer', ('v1', 'v2'))
    assert {
        'ok': outcome.ok,
        'mismatches': sum(1 for stage, _ in outcome.discards if stage == 'reference_mismatch'),
        'empty': (outcome.references, outcome.sentences),
    } == {'ok': False, 'mismatches': 2, 'empty': ((), ())}


@pytest.mark.anyio
async def test_leaky_message_is_rewritten():
    specs = (ClaimSpec(StatedType.PRICE, 'unique', ('L03',), None, None),)
    leaky = FakeTextModel(leak_once=True)
    outcome = await render_anchor(LINES, specs, leaky, 'writer', ('v1',))
    assert {
        'ok': outcome.ok,
        'discards': outcome.discards,
        'no_codes': 'L01' not in ' '.join(outcome.sentences),
    } == {'ok': True, 'discards': (('message_leak', 'all'),), 'no_codes': True}


@pytest.mark.anyio
async def test_wrong_sentence_count_discards():
    specs = (ClaimSpec(StatedType.PRICE, 'unique', ('L03',), None, None),)
    chatty = FakeTextModel(extra_sentence_once=True)
    # the double only fails once and the second attempt succeeds, so retry is observable
    outcome = await render_anchor(LINES, specs, chatty, 'writer', ('v1',))
    assert outcome.discards == (('message_sentence_count', 'all'),) and outcome.ok


@pytest.mark.anyio
async def test_unparseable_writer_reply_discards():
    class _Garbage:
        async def complete(
            self, model: str, prompt: str, *, temperature: float, max_tokens: int
        ) -> str:
            return 'sorry, no json here'

    specs = (ClaimSpec(StatedType.PRICE, 'unique', ('L03',), None, None),)
    outcome = await render_anchor(LINES, specs, _Garbage(), 'writer', ('v1',))
    assert outcome.ok is False and outcome.discards == (('reference_parse', 'all'),)


@pytest.mark.anyio
async def test_extraction_mismatch_retries_the_message():
    specs = (ClaimSpec(StatedType.PRICE, 'unique', ('L03',), None, None),)
    confused = FakeTextModel(wrong_extraction_once=True)
    outcome = await render_anchor(LINES, specs, confused, 'writer', ('v1',))
    assert outcome.discards == (('message_extraction', 'all'),) and outcome.ok
