import json
from pathlib import Path

import numpy as np

from commgym.cartopt.generator import record_to_instance
from commgym.cartopt.prompts import user_prompt
from commgym.cartopt.solver import solve


def load_rows(
    level: str, split: str, n: int, seed: int, instances_dir: Path, reward_cfg: str
) -> list[dict[str, object]]:
    """Eval rows for one split and level: prompt, record, reward cfg, solver-derived cents."""
    path = instances_dir / f'{split}_{level}.jsonl'
    records = [json.loads(line) for line in path.read_text().splitlines()]
    assert records, f'no instances in {path}'
    rng = np.random.default_rng(seed)
    chosen = rng.permutation(len(records))[:n] if n < len(records) else range(len(records))
    rows: list[dict[str, object]] = []
    for i in chosen:
        record = records[int(i)]
        info = record['info']
        assert isinstance(info, dict), f'{path}: record info must be a mapping'
        row: dict[str, object] = {
            'prompt': [{'role': 'user', 'content': user_prompt(record_to_instance(record))}],
            'record': json.dumps(record),
            'reward_cfg': reward_cfg,
            'instance_id': str(info['instance_id']),
            'level': level,
            'is_trap': bool(info['is_trap']),
            'c_star_cents': int(info['c_star_cents']),
            'c_ref_cents': solve(record_to_instance(record)).c_ref_cents(),
        }
        rows.append(row)
    return rows
