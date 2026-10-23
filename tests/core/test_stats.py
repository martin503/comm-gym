import math

from commgym.core.stats import (
    bootstrap_mean_ci,
    pass_at_k,
    within_instance_sd,
    zero_variance_fraction,
)


def test_pass_at_k_hand_computed():
    # mixed k=1: (1/2 + 1) / 2; k=n draws every rollout, so any success passes
    assert {
        'mixed_k1': pass_at_k([[True, False], [True, True]], 1),
        'mixed_k2_only_full_groups': pass_at_k([[True, False], [True, True]], 2),
        'k_equals_n_any_success': pass_at_k([[True, False, False]], 3),
        'k_equals_n_all_fail': pass_at_k([[False, False, False]], 3),
        'no_group_large_enough': pass_at_k([[True]], 2),
        'n8_c2_k4': pass_at_k([[True, True] + [False] * 6], 4),
    } == {
        'mixed_k1': 0.75,
        'mixed_k2_only_full_groups': 1.0,
        'k_equals_n_any_success': 1.0,
        'k_equals_n_all_fail': 0.0,
        'no_group_large_enough': None,
        'n8_c2_k4': 55 / 70,  # 1 - C(6,4)/C(8,4) = 1 - 15/70
    }


def test_bootstrap_mean_ci_degenerate_inputs():
    assert {
        'single': bootstrap_mean_ci([0.5]),
        'empty': bootstrap_mean_ci([]),
    } == {
        'single': (0.5, 0.5, 0.5),
        'empty': (0.0, 0.0, 0.0),
    }


def test_dispersion_metrics():
    # sd([1, 3], ddof=1) = sqrt(2); singleton groups contribute nothing
    assert {
        'zero_var': zero_variance_fraction([[1.0, 1.0], [1.0, 2.0], [0.5]]),
        'zero_var_empty': zero_variance_fraction([]),
        'within_sd': within_instance_sd([[1.0, 3.0]]),
        'within_sd_ignores_singletons': within_instance_sd([[1.0, 3.0], [7.0]]),
        'within_sd_empty': within_instance_sd([]),
    } == {
        'zero_var': 2 / 3,
        'zero_var_empty': 0.0,
        'within_sd': math.sqrt(2.0),
        'within_sd_ignores_singletons': math.sqrt(2.0),
        'within_sd_empty': 0.0,
    }
