from pathlib import Path

from commgym.core.config import load_models


def test_load_models_parses_per_model_sampling_params(tmp_path: Path):
    path = tmp_path / 'models.yaml'
    path.write_text(
        'models:\n'
        '  openai/gpt-6-luna:\n'
        '    temperature: 1.0\n'
        '    max_tokens: 4096\n'
        '    reasoning_effort: low\n'
        '  qwen/qwen3.8-27b:\n'
        '    temperature: 1.0\n'
        '    max_tokens: 8192\n'
        '    reasoning_effort: null\n'
    )
    models = load_models(path)
    assert {
        'ids': sorted(models),
        'luna': models['openai/gpt-6-luna'].sampling_params(),
        'qwen': models['qwen/qwen3.8-27b'].sampling_params(),
    } == {
        'ids': ['openai/gpt-6-luna', 'qwen/qwen3.8-27b'],
        'luna': {'temperature': 1.0, 'max_tokens': 4096, 'reasoning_effort': 'low'},
        'qwen': {'temperature': 1.0, 'max_tokens': 8192, 'reasoning_effort': None},
    }
