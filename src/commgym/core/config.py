from pathlib import Path

import yaml
from pydantic import BaseModel


class ModelParams(BaseModel):
    """Sampling settings for one model; the runner writes them verbatim into rollout records."""

    temperature: float = 1.0
    max_tokens: int = 2048
    reasoning_effort: str | None = None

    def sampling_params(self) -> dict[str, object]:
        return {
            'temperature': self.temperature,
            'max_tokens': self.max_tokens,
            'reasoning_effort': self.reasoning_effort,
        }


class ModelsConfig(BaseModel):
    models: dict[str, ModelParams]


def load_config[T: BaseModel](model: type[T], path: Path) -> T:
    """Parse a YAML config file into the given pydantic model."""
    data = yaml.safe_load(path.read_text())
    assert isinstance(data, dict), f'config {path} must be a YAML mapping'
    return model.model_validate(data)


def load_models(path: Path) -> dict[str, ModelParams]:
    """Models to evaluate, keyed by OpenRouter id, from a task's models.yaml."""
    return load_config(ModelsConfig, path).models
