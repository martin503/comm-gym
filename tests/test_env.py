import json
from pathlib import Path

import pytest

from cartgym.config import RewardConfig
from cartgym.env import (
    _completion_text,
    _load_rows,
    load_environment,
    metric_exact_opt,
    metric_parse_ok,
    reward_total,
)
from cartgym.generator import GeneratedInstance, instance_to_record, record_to_instance
from cartgym.instance import BrandQuota, BrandTier, SkuCoupon
from cartgym.pricing import cost
from cartgym.solver import optimal_cart, solve

# CAT A1 Private 200 / A2 National 280 (coupon 30c) ; DOG B1 Private 150 / B2 National 210
# quota >= 1 National -> C* = A2+B1 = 400, median feasible = 410, greedy A1+B1 infeasible


@pytest.fixture
def instances_dir(tmp_path: Path, make_sku, make_instance) -> Path:
    instance = make_instance(
        {
            'CAT': [
                make_sku('A1', 'CAT', shelf_cents=200),
                make_sku('A2', 'CAT', shelf_cents=280, brand_tier=BrandTier.NATIONAL),
            ],
            'DOG': [
                make_sku('B1', 'DOG', shelf_cents=150),
                make_sku('B2', 'DOG', shelf_cents=210, brand_tier=BrandTier.NATIONAL),
            ],
        },
        coupons=(SkuCoupon('K0', 'A2', 30),),
        constraints=(BrandQuota(BrandTier.NATIONAL, 1),),
    )
    solution = solve(instance)
    record = instance_to_record(
        GeneratedInstance(
            instance,
            {'instance_id': 'dev_T1#0', 'is_trap': True, 'c_star_cents': solution.c_star_cents()},
        )
    )
    directory = tmp_path / 'instances'
    directory.mkdir()
    (directory / 'dev_T1.jsonl').write_text(json.dumps(record) + '\n')
    return directory


def test_env_reward_funcs_match_verifiers_call_contract(instances_dir: Path):
    record_json = (instances_dir / 'dev_T1.jsonl').read_text().strip()
    # verifiers calls funcs with completion positional-style plus row columns by name
    kwargs = {
        'record': record_json,
        'reward_cfg': RewardConfig().model_dump_json(),
        'c_star_cents': 400,
        'c_ref_cents': 410,
    }
    instance = record_to_instance(json.loads(record_json))
    best = optimal_cart(instance, solve(instance), 1)
    oracle = (
        f'<answer>{json.dumps({"cart": best, "total": cost(best, instance).total_cents / 100})}'
        '</answer>'
    )
    assert {
        'total': reward_total(oracle, **kwargs),
        'parse_ok': metric_parse_ok(oracle, **kwargs),
        'exact': metric_exact_opt(oracle, **kwargs),
        'garbage_total': reward_total('I pick the cheapest items.', **kwargs),
        'garbage_parse': metric_parse_ok('I pick the cheapest items.', **kwargs),
    } == {
        'total': 1.0,
        'parse_ok': 1.0,
        'exact': 1.0,
        'garbage_total': 0.0,
        'garbage_parse': 0.0,
    }


def test_env_builds_single_turn_env_with_context_columns(instances_dir: Path):
    env = load_environment('T1', 'dev', n=1, seed=0, instances_dir=instances_dir)
    dataset = env.eval_dataset
    assert dataset is not None, 'eval dataset must build eagerly from a raw Dataset'
    assert {
        'type': type(env).__name__,
        'env_id': env.env_id,
        'columns': sorted(dataset.column_names),
        'n': dataset.num_rows,
    } == {
        'type': 'SingleTurnEnv',
        'env_id': 'cart-optimizer/dev/T1',
        'columns': [
            'c_ref_cents',
            'c_star_cents',
            'example_id',
            'instance_id',
            'is_trap',
            'level',
            'prompt',
            'record',
            'reward_cfg',
        ],
        'n': 1,
    }


def test_rows_carry_prompt_and_grading_context(instances_dir: Path):
    rows = _load_rows('T1', 'dev', 1, 0, instances_dir, RewardConfig().model_dump_json())
    row = rows[0]
    prompt = row['prompt']
    record = row['record']
    assert isinstance(prompt, list), 'prompt rows are message lists'
    assert isinstance(record, str), 'record rows are JSON strings'
    roles = [message['role'] for message in prompt if isinstance(message, dict)]
    user_turn = prompt[-1]
    assert isinstance(user_turn, dict), 'last prompt message is the user turn'
    user_text = user_turn['content']
    assert isinstance(user_text, str), 'message content is text'
    assert {
        'roles': roles,
        'user_mentions_menu': 'A2' in user_text,
        'c_star': row['c_star_cents'],
        'c_ref': row['c_ref_cents'],
        'trap': row['is_trap'],
        'record_round_trips': record_to_instance(json.loads(record)).commodities,
    } == {
        'roles': ['user'],
        'user_mentions_menu': True,
        'c_star': 400,
        'c_ref': 410,
        'trap': True,
        'record_round_trips': ('CAT', 'DOG'),
    }


def test_completion_text_normalizes_verifiers_shapes():
    messages = [
        {'role': 'system', 'content': 'sys'},
        {'role': 'assistant', 'content': 'first'},
        {'role': 'assistant', 'content': 'second'},
    ]

    class _Msg:
        role = 'assistant'
        content = 'model'

    assert {
        'plain': _completion_text('raw'),
        'dicts': _completion_text(messages),
        'models': _completion_text([_Msg()]),
    } == {'plain': 'raw', 'dicts': 'first\nsecond', 'models': 'model'}
