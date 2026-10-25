from pathlib import Path

import pytest
from _mocks.fake_openai import FakeChatCreate

from commgym.core.config import ModelParams
from commgym.core.eval import LevelSpec, SweepPlan, run_sweep, select_models
from commgym.core.openrouter import OpenRouterClient
from commgym.core.runner import EvalItem, GradeOutcome

PRICES = {
    'fake/luna': {'prompt': '0.000001', 'completion': '0.000002'},
    'fake/qwen': {'prompt': '0.000001', 'completion': '0.000002'},
}


def _spec() -> LevelSpec:
    def grade_fn(item: EvalItem, completion: str) -> GradeOutcome:
        return GradeOutcome(
            reward=1.0,
            parsed={'ok': True},
            parse_reason=None,
            components={'success': True},
        )

    return LevelSpec(
        items=[EvalItem('i1', [{'role': 'user', 'content': 'pick'}], 's')],
        grade_fn=grade_fn,
        system_message='sys',
        success_key='success',
    )


@pytest.mark.anyio
async def test_run_sweep_scores_each_model_with_its_own_sampling_params(tmp_path: Path):
    fake = FakeChatCreate()
    models = {
        'fake/luna': ModelParams(temperature=1.0, max_tokens=4096, reasoning_effort='low'),
        'fake/qwen': ModelParams(temperature=0.5, max_tokens=1024, reasoning_effort=None),
    }
    state = await run_sweep(
        models,
        ['L1', 'L2'],
        {'L1': _spec(), 'L2': _spec()},
        env_file=Path('.env'),
        plan=SweepPlan(full_n=10, full_k=2),
        split='dev',
        rollouts_dir=tmp_path,
        k=1,
        client=OpenRouterClient(acreate=fake),
        prices=PRICES,
    )
    assert {
        'n_rollouts': len(state.rewards),
        'calls': [(c['model'], c['max_tokens'], c['reasoning_effort']) for c in fake.calls],
        'rollout_files': sorted(p.name for p in tmp_path.rglob('*.jsonl')),
    } == {
        'n_rollouts': 4,
        'calls': [
            ('fake/luna', 4096, 'low'),
            ('fake/luna', 4096, 'low'),
            ('fake/qwen', 1024, None),
            ('fake/qwen', 1024, None),
        ],
        'rollout_files': ['dev_L1.jsonl', 'dev_L1.jsonl', 'dev_L2.jsonl', 'dev_L2.jsonl'],
    }


@pytest.mark.anyio
async def test_run_sweep_requires_pricing_for_every_model(tmp_path: Path):
    with pytest.raises(AssertionError, match='no pricing'):
        await run_sweep(
            {'fake/unknown': ModelParams()},
            ['L1'],
            {'L1': _spec()},
            env_file=Path('.env'),
            plan=SweepPlan(full_n=10, full_k=2),
            split='dev',
            rollouts_dir=tmp_path,
            k=1,
            client=OpenRouterClient(acreate=FakeChatCreate()),
            prices=PRICES,
        )


def test_select_models_filters_and_rejects_unknown_names():
    models = {'a': ModelParams(max_tokens=1), 'b': ModelParams(max_tokens=2)}
    assert {
        'subset': select_models(models, ['b']),
        'all': select_models(models, []),
    } == {
        'subset': {'b': ModelParams(max_tokens=2)},
        'all': models,
    }
    with pytest.raises(AssertionError, match='not in the models config'):
        select_models(models, ['c'])
