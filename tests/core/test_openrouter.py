from pathlib import Path

import pytest
from _mocks.fake_openai import FakeChatCreate

from commgym.core.openrouter import OpenRouterClient, estimate_cost_usd, load_api_key


@pytest.fixture
def fake_create() -> FakeChatCreate:
    return FakeChatCreate()


@pytest.mark.anyio
async def test_chat_normalizes_response_and_builds_params(fake_create: FakeChatCreate):
    client = OpenRouterClient(acreate=fake_create)
    result = await client.chat(
        'qwen/qwen3.7-flash', [{'role': 'user', 'content': 'hi'}], max_tokens=99
    )
    await client.chat(
        'openai/gpt-6-luna', [{'role': 'user', 'content': 'hi'}], reasoning_effort='low'
    )
    default_call, effort_call = fake_create.calls[0], fake_create.calls[1]
    messages = default_call['messages']
    assert isinstance(messages, list), 'fake records the messages it was called with'
    assert {
        'text': result.text,
        'tokens_in': result.prompt_tokens,
        'tokens_out': result.completion_tokens,
        'model': result.model,
        'latency_positive': result.latency_s >= 0,
        'passed_through': {
            'model': default_call['model'],
            'temperature': default_call['temperature'],
            'max_tokens': default_call['max_tokens'],
            'n_messages': len(messages),
            'reasoning_effort_default': default_call['reasoning_effort'],
        },
        'effort_forwarded': effort_call['reasoning_effort'],
    } == {
        'text': '<answer>{"cart": {}, "total": 0}</answer>',
        'tokens_in': 120,
        'tokens_out': 45,
        'model': 'qwen/qwen3.7-flash',
        'latency_positive': True,
        'passed_through': {
            'model': 'qwen/qwen3.7-flash',
            'temperature': 1.0,
            'max_tokens': 99,
            'n_messages': 1,
            'reasoning_effort_default': None,
        },
        'effort_forwarded': 'low',
    }


def test_estimate_cost_usd_hand_computed():
    prices = {'m/x': {'prompt': '0.0000005', 'completion': '0.000002'}}
    assert {
        'known': round(estimate_cost_usd(prices, 'm/x', 1000, 500), 9),
        'unknown': estimate_cost_usd(prices, 'm/other', 1000, 500),
    } == {'known': 0.0015, 'unknown': 0.0}


def test_load_api_key_env_var_wins_over_dotenv(tmp_path: Path):
    env_file = tmp_path / 'dotenv.txt'
    env_file.write_text('OPENROUTER_API_KEY=from-file\nOTHER=1\n')
    assert {
        'env': load_api_key({'OPENROUTER_API_KEY': 'from-env'}, env_file),
        'file': load_api_key({}, env_file),
        'quoted': load_api_key({}, _write(tmp_path, 'OPENROUTER_API_KEY="quoted"\n')),
    } == {'env': 'from-env', 'file': 'from-file', 'quoted': 'quoted'}


def _write(tmp_path: Path, content: str) -> Path:
    env_file = tmp_path / f'dotenv_{abs(hash(content)) % 1000}.txt'
    env_file.write_text(content)
    return env_file
