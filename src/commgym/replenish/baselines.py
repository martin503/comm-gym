from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True, slots=True)
class LogisticFit:
    coefficients: np.ndarray  # intercept first, on standardized features
    means: np.ndarray
    scales: np.ndarray


def irls_logistic(
    features: np.ndarray, y: np.ndarray, *, max_iter: int = 100, tol: float = 1e-10
) -> LogisticFit:
    """Fit logistic regression by iteratively reweighted least squares.

    Features are standardized for conditioning; the tiny diagonal term keeps the Newton
    system invertible when a feature separates the classes.
    """
    assert len(features) == len(y), 'feature matrix and labels must align'
    means = features.mean(axis=0)
    scales = features.std(axis=0)
    scales[scales == 0.0] = 1.0
    z = np.column_stack([np.ones(len(features)), (features - means) / scales])
    w = np.zeros(z.shape[1])
    for _ in range(max_iter):
        probs = _sigmoid(z @ w)
        weights = probs * (1.0 - probs)
        gradient = z.T @ (y - probs)
        hessian = z.T @ (weights[:, None] * z) + 1e-8 * np.eye(z.shape[1])
        step = np.linalg.solve(hessian, gradient)
        w += step
        if np.max(np.abs(step)) < tol:
            break
    return LogisticFit(w, means, scales)


def logistic_probs(fit: LogisticFit, features: np.ndarray) -> np.ndarray:
    x = np.column_stack([np.ones(len(features)), (features - fit.means) / fit.scales])
    return _sigmoid(x @ fit.coefficients)


def _sigmoid(z: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(z, -35.0, 35.0)))
