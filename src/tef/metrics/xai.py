"""XAI-validation metrics: feature-removal degradation, explanation stability,
rank correlation, and explanation-drift magnitude. Model-agnostic given a
`predict_fn(X)->yhat` and an attribution matrix.
"""
from __future__ import annotations
import numpy as np
from scipy.stats import kendalltau

from .point import mae


def feature_removal_degradation(predict_fn, X, y, importance, top_k, n_random=5, rng=None):
    """Compare MAE increase from removing (mean-imputing) the top-k important features
    vs removing k random features. Ratio > 1 => explanation has fidelity.

    importance: 1-D array of per-feature importance (e.g. mean |SHAP|).
    Returns dict with base_mae, topk_mae, random_mae, fidelity_ratio.
    """
    rng = np.random.default_rng(rng)
    X = np.asarray(X, dtype=float)
    d = X.shape[1]
    order = np.argsort(-np.asarray(importance, dtype=float))
    top = order[:top_k]

    def _ablate(cols):
        Xa = X.copy()
        Xa[:, cols] = X[:, cols].mean(axis=0, keepdims=True)
        return mae(y, predict_fn(Xa))

    base = mae(y, predict_fn(X))
    topk_mae = _ablate(top)
    rand_maes = []
    for _ in range(n_random):
        cols = rng.choice(d, size=top_k, replace=False)
        rand_maes.append(_ablate(cols))
    rand_mae = float(np.mean(rand_maes))
    d_top = topk_mae - base
    d_rand = rand_mae - base
    ratio = float(d_top / d_rand) if d_rand > 1e-12 else float("inf")
    return {"base_mae": base, "topk_mae": topk_mae, "random_mae": rand_mae,
            "fidelity_ratio": ratio}


def rank_correlation(imp_a, imp_b) -> float:
    """Kendall's tau between two feature-importance rankings (stability / drift)."""
    a = np.asarray(imp_a, dtype=float)
    b = np.asarray(imp_b, dtype=float)
    tau, _ = kendalltau(a, b)
    return float(tau) if tau == tau else 0.0  # NaN -> 0


def explanation_stability(attributions) -> float:
    """Mean pairwise Kendall tau across a set of attribution vectors for similar
    inputs. attributions: (n_samples, n_features). Higher => more stable.
    """
    A = np.asarray(attributions, dtype=float)
    n = A.shape[0]
    if n < 2:
        return float("nan")
    taus = []
    for i in range(n):
        for j in range(i + 1, n):
            taus.append(rank_correlation(A[i], A[j]))
    return float(np.mean(taus))


def explanation_drift(imp_reference, imp_current) -> float:
    """Magnitude of explanation drift = 1 - Kendall tau of importance rankings
    (0 = identical ordering, up to 2 = fully reversed). Complements RQ5/RQ6.
    """
    return float(1.0 - rank_correlation(imp_reference, imp_current))
