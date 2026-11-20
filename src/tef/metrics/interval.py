"""Interval / calibration metrics: PICP, PINAW, interval score, CWC, CRPS, coverage error.

Conventions:
- lower, upper: arrays of interval bounds.
- nominal: target coverage in (0,1), e.g. 0.90.
- CRPS via the quantile (pinball) approximation given a set of quantile forecasts.
"""
from __future__ import annotations
import numpy as np


def _arr(x):
    return np.asarray(x, dtype=float).ravel()


def picp(y_true, lower, upper) -> float:
    """Prediction Interval Coverage Probability: fraction of y inside [lower, upper]."""
    y, lo, hi = _arr(y_true), _arr(lower), _arr(upper)
    return float(np.mean((y >= lo) & (y <= hi)))


def pinaw(y_true, lower, upper) -> float:
    """Prediction Interval Normalized Average Width (normalized by range of y_true)."""
    y, lo, hi = _arr(y_true), _arr(lower), _arr(upper)
    rng = np.ptp(y)
    return float(np.mean(hi - lo) / rng) if rng > 0 else float("nan")


def coverage_error(y_true, lower, upper, nominal: float) -> float:
    """Signed coverage error PICP - nominal. Negative => overconfident (under-covers)."""
    return float(picp(y_true, lower, upper) - nominal)


def interval_score(y_true, lower, upper, nominal: float) -> float:
    """Winkler/interval score for a central (1-alpha) interval. Lower is better."""
    y, lo, hi = _arr(y_true), _arr(lower), _arr(upper)
    alpha = 1.0 - nominal
    width = hi - lo
    penalty_lo = (2.0 / alpha) * (lo - y) * (y < lo)
    penalty_hi = (2.0 / alpha) * (y - hi) * (y > hi)
    return float(np.mean(width + penalty_lo + penalty_hi))


def cwc(y_true, lower, upper, nominal: float, eta: float = 50.0) -> float:
    """Coverage Width-based Criterion. Penalizes PINAW unless PICP >= nominal."""
    p = picp(y_true, lower, upper)
    w = pinaw(y_true, lower, upper)
    gamma = 0.0 if p >= nominal else 1.0
    return float(w * (1.0 + gamma * np.exp(-eta * (p - nominal))))


def crps_from_quantiles(y_true, quantile_preds, quantile_levels) -> float:
    """Approximate CRPS as the mean pinball loss across a set of quantile levels.

    quantile_preds: array (n_samples, n_quantiles).
    quantile_levels: array (n_quantiles,) in (0,1).
    This is the standard quantile-decomposition estimator of CRPS (up to a factor);
    lower is better and it is order-consistent with CRPS.
    """
    y = _arr(y_true)
    q = np.asarray(quantile_preds, dtype=float)
    taus = _arr(quantile_levels)
    if q.ndim == 1:
        q = q[:, None]
    losses = []
    for j, tau in enumerate(taus):
        e = y - q[:, j]
        losses.append(np.mean(np.maximum(tau * e, (tau - 1.0) * e)))
    return float(2.0 * np.mean(losses))


def interval_metrics(y_true, lower, upper, nominal: float) -> dict:
    return {
        "PICP": picp(y_true, lower, upper),
        "PINAW": pinaw(y_true, lower, upper),
        "CoverageError": coverage_error(y_true, lower, upper, nominal),
        "IntervalScore": interval_score(y_true, lower, upper, nominal),
        "CWC": cwc(y_true, lower, upper, nominal),
    }
