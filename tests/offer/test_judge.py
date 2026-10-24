import pytest
from _mocks.fake_openai import FakeScriptedChatCreate

from commgym.core.openrouter import OpenRouterClient
from commgym.offer.config import JudgeConfig
from commgym.offer.judge import JudgeOutcome, judge_pair, parse_verdict, reliability

CFG = JudgeConfig()


def _client(replies: list[str]) -> tuple[OpenRouterClient, FakeScriptedChatCreate]:
    fake = FakeScriptedChatCreate(replies)
    return OpenRouterClient(acreate=fake), fake


@pytest.mark.anyio
async def test_both_orders_average_to_candidate_win():
    client, fake = _client(['A', 'A'])
    outcome = await judge_pair(
        client,
        CFG,
        context_prompt='ctx',
        candidate_selection=('k01',),
        candidate_message='candidate message about milk',
        reference_selection=('k02',),
        reference_message='reference message about pizza',
    )
    assert {
        'win': outcome.judge_win,
        'orders': outcome.order_scores,
        'error': outcome.error,
        'calls': len(fake.calls),
    } == {'win': 0.5, 'orders': (1.0, 0.0), 'error': None, 'calls': 2}


@pytest.mark.anyio
async def test_clean_sweep_and_clean_loss():
    client, _ = _client(['A', 'B'])
    won = await judge_pair(
        client,
        CFG,
        context_prompt='ctx',
        candidate_selection=('k01',),
        candidate_message='m1',
        reference_selection=('k02',),
        reference_message='m2',
    )
    client2, _ = _client(['B', 'A'])
    lost = await judge_pair(
        client2,
        CFG,
        context_prompt='ctx',
        candidate_selection=('k01',),
        candidate_message='m1',
        reference_selection=('k02',),
        reference_message='m2',
    )
    assert {'won': won.judge_win, 'lost': lost.judge_win} == {'won': 1.0, 'lost': 0.0}


@pytest.mark.anyio
async def test_unparseable_verdict_retries_then_errors():
    client, fake = _client(['garbage', 'A', 'garbage', 'garbage'])
    outcome = await judge_pair(
        client,
        CFG,
        context_prompt='ctx',
        candidate_selection=('k01',),
        candidate_message='m1',
        reference_selection=('k02',),
        reference_message='m2',
    )
    assert {'error': outcome.error, 'calls': len(fake.calls)} == {
        'error': 'unparseable_verdict',
        'calls': 4,
    }


def test_parse_verdict_first_word_then_fallback():
    assert {
        'first_line': parse_verdict('B — clearer and more specific.'),
        'tie': parse_verdict('TIE\nboth are fine'),
        'fallback': parse_verdict('I would say a: A'),
        'none': parse_verdict('no verdict at all here'),
    } == {'first_line': 0.0, 'tie': 0.5, 'fallback': 1.0, 'none': None}


def test_reliability_counts_consistency_and_ties():
    stats = reliability(
        [
            JudgeOutcome(0.5, (1.0, 0.0), None, 0, 0),
            JudgeOutcome(1.0, (1.0, 1.0), None, 0, 0),
            JudgeOutcome(0.5, (0.5, 0.5), None, 0, 0),
        ]
    )
    assert stats == {'order_consistency': 2 / 3, 'tie_rate': 2 / 3, 'n': 3.0}
