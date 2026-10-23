import json
from pathlib import Path

import pytest

from commgym.cartopt.config import RewardConfig
from commgym.cartopt.env import (
    load_rows,
    metric_exact_opt,
    metric_parse_ok,
    reward_total,
)
from commgym.cartopt.generator import GeneratedInstance, instance_to_record, record_to_instance
from commgym.cartopt.instance import BrandQuota, BrandTier, SkuCoupon
from commgym.cartopt.pricing import cost
from commgym.cartopt.solver import optimal_cart, solve
from commgym.core.vfenv import completion_text

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


def test_rows_carry_prompt_and_grading_context(instances_dir: Path):
    rows = load_rows('T1', 'dev', 1, 0, instances_dir, RewardConfig().model_dump_json())
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
        'plain': completion_text('raw'),
        'dicts': completion_text(messages),
        'models': completion_text([_Msg()]),
    } == {'plain': 'raw', 'dicts': 'first\nsecond', 'models': 'model'}
