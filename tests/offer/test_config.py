import pytest
from pydantic import ValidationError

from commgym.offer.config import RewardConfig, TaskConfig


def test_pool_size_is_the_largest_level():
    assert TaskConfig().pool_size == 20


def test_level_sizes_must_be_distinct():
    with pytest.raises(ValidationError, match='distinct'):
        TaskConfig(level_sizes={'L1': 5, 'L2': 5, 'L3': 20})


def test_relevant_coupons_must_fit_smallest_level():
    with pytest.raises(ValidationError, match='relevant'):
        TaskConfig(relevant_coupons=6)


def test_reward_weights_must_stay_within_one():
    with pytest.raises(ValidationError, match='0, 1'):
        RewardConfig(w_base=0.5, w_affinity=0.3, w_judge=0.4)


def test_reward_config_requires_positive_base():
    with pytest.raises(ValidationError, match='w_base'):
        RewardConfig(w_base=0.0)
