"""Feature attributions with fallback.

Prefers SHAP TreeExplainer for the GBM backbone; if SHAP is unavailable, falls
back to a fast per-sample local linear attribution (gradient x input around a
mean baseline via finite differences on the model's predict). Returns a matrix
(n_samples, n_features) of signed contributions, matching the ExplanationShift
detector's expectation of a signed SHAP-like vector.
"""
from __future__ import annotations
import numpy as np

try:  # optional
    import shap
    _HAS_SHAP = True
except Exception:  # pragma: no cover
    _HAS_SHAP = False


def tree_attributions(model, X):
    """SHAP values for a tree model, or a finite-difference fallback."""
    X = np.asarray(X, float)
    if _HAS_SHAP:
        try:
            inner = getattr(model, "model", model)
            explainer = shap.TreeExplainer(inner)
            vals = explainer.shap_values(X)
            return np.asarray(vals, float)
        except Exception:
            pass
    return _finite_difference_attributions(model, X)


def _finite_difference_attributions(model, X, eps_frac=0.01):
    """Local sensitivity: contribution_j ~= dpred/dx_j * (x_j - baseline_j).
    Baseline = column mean. Cheap, signed, model-agnostic; a stand-in for SHAP.
    """
    X = np.asarray(X, float)
    n, d = X.shape
    baseline = X.mean(axis=0)
    base_pred = model.predict(X)
    attr = np.zeros((n, d))
    scale = np.maximum(np.abs(X).mean(axis=0), 1e-6) * eps_frac
    for j in range(d):
        Xp = X.copy()
        Xp[:, j] += scale[j]
        grad = (model.predict(Xp) - base_pred) / scale[j]
        attr[:, j] = grad * (X[:, j] - baseline[j])
    return attr


def global_importance(attributions):
    """Mean absolute attribution per feature (global importance ranking)."""
    return np.mean(np.abs(np.asarray(attributions, float)), axis=0)
