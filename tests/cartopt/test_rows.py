import json
from pathlib import Path

import pytest

from commgym.cartopt.generator import GeneratedInstance, instance_to_record, record_to_instance
from commgym.cartopt.instance import BrandQuota, BrandTier, SkuCoupon
from commgym.cartopt.rows import load_rows
from commgym.cartopt.solver import solve

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


def test_rows_carry_prompt_and_grading_context(instances_dir: Path):
    rows = load_rows('T1', 'dev', 1, 0, instances_dir, '{}')
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
