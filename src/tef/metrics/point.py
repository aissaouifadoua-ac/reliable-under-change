"""Point-forecast metrics. All accept 1-D array-likes of equal length."""
from __future__ import annotations
import numpy as np


def _arr(x):
    return np.asarray(x, dtype=float).ravel()


def mae(y_true, y_pred) -> float:
    y, p = _arr(y_true), _arr(y_pred)
    return float(np.mean(np.abs(y - p)))


def rmse(y_true, y_pred) -> float:
    y, p = _arr(y_true), _arr(y_pred)
    return float(np.sqrt(np.mean((y - p) ** 2)))


def smape(y_true, y_pred, eps: float = 1e-8) -> float:
    """Symmetric MAPE in percent; robust near zero via eps floor on the denom."""
    y, p = _arr(y_true), _arr(y_pred)
    denom = np.maximum(np.abs(y) + np.abs(p), eps)
    return float(100.0 * np.mean(2.0 * np.abs(y - p) / denom))


def nrmse(y_true, y_pred) -> float:
    """RMSE normalized by the range of y_true (for cross-dataset comparison)."""
    y = _arr(y_true)
    rng = np.ptp(y)
    return float(rmse(y_true, y_pred) / rng) if rng > 0 else float("nan")


def point_metrics(y_true, y_pred) -> dict:
    return {"MAE": mae(y_true, y_pred), "RMSE": rmse(y_true, y_pred),
            "sMAPE": smape(y_true, y_pred), "NRMSE": nrmse(y_true, y_pred)}
