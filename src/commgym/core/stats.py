import math
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

BOOTSTRAP_RESAMPLES = 10_000
PASS_KS = (1, 4, 8)


@dataclass(frozen=True, slots=True)
class InstanceStats:
    """Aggregates over per-instance rollout groups, shared by the eval analyzers."""

    n_instances: int
    reward_mean: float
    reward_lo: float
    reward_hi: float
    pass_at: dict[int, float | None]
    zero_var: float
    within_sd: float


def instance_stats(
    rewards: Sequence[Sequence[float]], successes: Sequence[Sequence[bool]]
) -> InstanceStats:
    """Bootstrap CI, pass@k ladder, and variance summaries over instance groups."""
    mean, lo, hi = bootstrap_mean_ci([float(np.mean(group)) for group in rewards])
    return InstanceStats(
        n_instances=len(rewards),
        reward_mean=mean,
        reward_lo=lo,
        reward_hi=hi,
        pass_at={k: pass_at_k(successes, k) for k in PASS_KS},
        zero_var=zero_variance_fraction(rewards),
        within_sd=within_instance_sd(rewards),
    )


def pass_at_k(successes: Sequence[Sequence[bool]], k: int) -> float | None:
    """Unbiased pass@k averaged over instances with at least k rollouts."""
    estimates = []
    for group in successes:
        if len(group) < k:
            continue
        correct = sum(1 for success in group if success)
        n = len(group)
        estimates.append(1.0 - math.comb(n - correct, k) / math.comb(n, k))
    return float(np.mean(estimates)) if estimates else None


def bootstrap_mean_ci(
    values: Sequence[float], *, resamples: int = BOOTSTRAP_RESAMPLES, seed: int = 42
) -> tuple[float, float, float]:
    """Mean and 95% percentile CI from resampling the values with replacement."""
    rewards = np.asarray(values, dtype=float)
    rng = np.random.default_rng(seed)
    n = len(rewards)
    mean = float(rewards.mean()) if n else 0.0
    if n > 1:
        resampled = rewards[rng.integers(0, n, size=(resamples, n))].mean(axis=1)
        lo, hi = np.percentile(resampled, [2.5, 97.5])
    else:
        lo = hi = mean
    return mean, float(lo), float(hi)


def zero_variance_fraction(groups: Sequence[Sequence[float]]) -> float:
    """Share of groups whose rewards are all identical (dead GRPO signal)."""
    if not groups:
        return 0.0
    constant = sum(1 for group in groups if len(set(group)) == 1)
    return constant / len(groups)


def within_instance_sd(groups: Sequence[Sequence[float]]) -> float:
    """Mean per-instance reward SD over groups with more than one rollout."""
    sds = [float(np.std(group, ddof=1)) for group in groups if len(group) > 1]
    return float(np.mean(sds)) if sds else 0.0
