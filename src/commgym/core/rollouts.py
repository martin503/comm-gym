import json
from pathlib import Path


def read_jsonl(path: Path) -> list[dict[str, object]]:
    """Parse a JSONL file of object rows; blank lines are skipped."""
    rows = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        assert isinstance(row, dict), f'{path}: rows must be JSON objects'
        rows.append(row)
    return rows


def model_slug(model: str) -> str:
    """Filesystem-safe directory name for a model id."""
    return model.replace('/', '__')


def rollouts_path(rollouts_dir: Path, model: str, split: str, level: str) -> Path:
    """Rollout file convention shared by the eval writer and the analyze readers."""
    return rollouts_dir / model_slug(model) / f'{split}_{level}.jsonl'
