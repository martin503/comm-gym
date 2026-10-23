import json
from pathlib import Path

import pytest
from _mocks.fake_openai import FakeChatCreate

from commgym.core.openrouter import OpenRouterClient
from commgym.core.runner import (
    RECORD_KEYS,
    EvalItem,
    GradeOutcome,
    RunState,
    existing_results,
    resume_keys,
    run_level,
)

PRICES = {'fake/model': {'prompt': '0.000001', 'completion': '0.000002'}}
PARAMS: dict[str, object] = {'temperature': 1.0, 'max_tokens': 2048, 'reasoning_effort': None}


def _items() -> list[EvalItem]:
    return [
        EvalItem('i1', [{'role': 'user', 'content': 'pick'}], 'trap'),
        EvalItem('i2', [{'role': 'user', 'content': 'pick'}], 'no_trap'),
    ]


def _grade(item: EvalItem, completion: str) -> GradeOutcome:
    return GradeOutcome(
        reward=1.0 if 'answer' in completion else 0.0,
        parsed={'ok': True},
        parse_reason=None,
        components={'success': 'answer' in completion, 'n': 2},
    )


def _client(fake: FakeChatCreate) -> OpenRouterClient:
    return OpenRouterClient(acreate=fake)


@pytest.mark.anyio
async def test_run_level_writes_records_and_collects_rewards(tmp_path: Path):
    fake = FakeChatCreate()
    state = RunState()
    out_path = tmp_path / 'roll.jsonl'
    summary = await run_level(
        _items(),
        _grade,
        _client(fake),
        'fake/model',
        'L1',
        out_path,
        PRICES,
        'sys prompt',
        'success',
        state,
        k=2,
        seed=7,
    )
    records = [json.loads(line) for line in out_path.read_text().splitlines()]
    first = records[0]
    assert {
        'n_records': len(records),
        'record_keys': list(first),
        'system_prepended': first['prompt'][0]['role'],
        'stratum_copied': first['stratum'],
        'reward': first['reward'],
        'state_rewards': len(state.rewards),
        'state_successes': sum(state.successes),
        'state_spent_positive': state.spent_usd > 0,
        'summary': (summary.rewards, summary.successes),
    } == {
        'n_records': 4,
        'record_keys': list(RECORD_KEYS),
        'system_prepended': 'system',
        'stratum_copied': 'trap',
        'reward': 1.0,
        'state_rewards': 4,
        'state_successes': 4,
        'state_spent_positive': True,
        'summary': ([1.0] * 4, [True] * 4),
    }


@pytest.mark.anyio
async def test_run_level_resume_skips_saved_rollouts(tmp_path: Path):
    fake = FakeChatCreate()
    state = RunState()
    out_path = tmp_path / 'roll.jsonl'
    await run_level(
        _items(),
        _grade,
        _client(fake),
        'fake/model',
        'L1',
        out_path,
        PRICES,
        'sys',
        'success',
        state,
        k=2,
        seed=7,
    )
    calls_after_first_run = len(fake.calls)
    summary = await run_level(
        _items(),
        _grade,
        _client(fake),
        'fake/model',
        'L1',
        out_path,
        PRICES,
        'sys',
        'success',
        state,
        k=2,
        seed=7,
    )
    assert {
        'no_new_calls': len(fake.calls) - calls_after_first_run,
        'summary_from_existing': (summary.rewards, summary.successes),
        'file_unchanged': len(out_path.read_text().splitlines()),
    } == {
        'no_new_calls': 0,
        'summary_from_existing': ([1.0] * 4, [True] * 4),
        'file_unchanged': 4,
    }


def test_resume_keys_drops_truncated_lines_and_filters_params(tmp_path: Path):
    out_path = tmp_path / 'roll.jsonl'
    good = json.dumps({'instance_id': 'i1', 'rollout_idx': 0, 'sampling_params': PARAMS})
    other_params = json.dumps(
        {
            'instance_id': 'i1',
            'rollout_idx': 1,
            'sampling_params': {'temperature': 0.2, 'max_tokens': 2048, 'reasoning_effort': None},
        }
    )
    out_path.write_text(good + '\n{"instance_id": "i2", "rollout' + '\n' + other_params + '\n')
    assert {
        'same_params': resume_keys(out_path, PARAMS),
        'file_rewritten_without_truncated': out_path.read_text().splitlines(),
    } == {
        'same_params': {('i1', 0)},
        'file_rewritten_without_truncated': [good, other_params],
    }


def test_existing_results_reads_success_key(tmp_path: Path):
    out_path = tmp_path / 'roll.jsonl'
    record = json.dumps(
        {
            'instance_id': 'i1',
            'rollout_idx': 0,
            'reward': 0.5,
            'sampling_params': PARAMS,
            'components': {'success': True},
        }
    )
    out_path.write_text(record + '\n')
    assert existing_results(out_path, PARAMS, 'success') == ([0.5], [True])


def test_resume_helpers_on_missing_file(tmp_path: Path):
    missing = tmp_path / 'nope.jsonl'
    assert {
        'keys': resume_keys(missing, PARAMS),
        'results': existing_results(missing, PARAMS, 'success'),
    } == {'keys': set(), 'results': ([], [])}
