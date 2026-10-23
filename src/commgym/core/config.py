from pathlib import Path

import yaml
from pydantic import BaseModel


def load_config[T: BaseModel](model: type[T], path: Path) -> T:
    """Parse a YAML config file into the given pydantic model."""
    data = yaml.safe_load(path.read_text())
    assert isinstance(data, dict), f'config {path} must be a YAML mapping'
    return model.model_validate(data)
