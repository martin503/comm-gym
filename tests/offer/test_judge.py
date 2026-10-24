import pytest
from _mocks.fake_openai import FakeScriptedChatCreate

from commgym.core.openrouter import OpenRouterClient
from commgym.offer.config import JudgeConfig
from commgym.offer.judge import JudgeOutcome, judge_pair, parse_verdict, reliability

CFG = JudgeConfig()


def _client(replies: list[str]) -> tuple[OpenRouterClient, FakeScriptedChatCreate]:
    fake = FakeScriptedChatCreate(replies)
    return OpenRouterClient(acreate=fake), fake


async def _pair(
    client: OpenRouterClient, candidate: str = 'm1', reference: str = 'm2'
) -> JudgeOutcome:
    return await judge_pair(
        client,
        CFG,
        context_prompt='ctx',
        candidate_selection=('k01',),
        candidate_message=candidate,
        reference_selection=('k02',),
        reference_message=reference,
    )


@pytest.mark.anyio
async def test_judge_pair_averages_both_orders_and_recovers():
    client, _ = _client(['A', 'A'])
    split = await _pair(client, candidate='candidate message about milk')
    won = await _pair(_client(['A', 'B'])[0])
    lost = await _pair(_client(['B', 'A'])[0])
    error_client, error_fake = _client(['garbage', 'A', 'garbage', 'garbage'])
    errored = await _pair(error_client)
    assert {
        'split_win': split.judge_win,
        'split_orders': split.order_scores,
        'clean_sweep': won.judge_win,
        'clean_loss': lost.judge_win,
        'error': errored.error,
        'retry_calls': len(error_fake.calls),
    } == {
        'split_win': 0.5,
        'split_orders': (1.0, 0.0),
        'clean_sweep': 1.0,
        'clean_loss': 0.0,
        'error': 'unparseable_verdict',
        'retry_calls': 4,
    }


def test_verdict_parsing_first_word_then_fallback():
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
