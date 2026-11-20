"""Drift-evaluation metrics: detection delay, false-alarm rate, recovery time,
and rolling-window helpers. Operate on time-indexed detector alarms and errors.
"""
from __future__ import annotations
import numpy as np


def detection_delay(alarm_idx, true_drift_idx) -> float:
    """Steps between true drift onset and the first alarm at/after it.

    Returns np.inf if no alarm occurs after onset. Requires injected/labeled drift.
    """
    alarms = np.sort(np.asarray(alarm_idx, dtype=int))
    after = alarms[alarms >= true_drift_idx]
    return float(after[0] - true_drift_idx) if after.size else float("inf")


def false_alarm_rate(alarm_idx, true_drift_idx, n_steps, guard: int = 0) -> float:
    """Fraction of steps (before true drift, minus a guard band) that raised an alarm.

    A detector that fires in the stable pre-drift region is false-alarming.
    """
    alarms = np.asarray(alarm_idx, dtype=int)
    pre = alarms[alarms < max(true_drift_idx - guard, 0)]
    denom = max(true_drift_idx - guard, 1)
    return float(len(np.unique(pre)) / denom)


def rolling_mae(y_true, y_pred, window: int) -> np.ndarray:
    """Trailing rolling MAE aligned to the right edge (NaN until `window` filled)."""
    e = np.abs(np.asarray(y_true, float).ravel() - np.asarray(y_pred, float).ravel())
    out = np.full_like(e, np.nan, dtype=float)
    csum = np.concatenate([[0.0], np.cumsum(e)])
    for i in range(window - 1, len(e)):
        out[i] = (csum[i + 1] - csum[i + 1 - window]) / window
    return out


def recovery_time(metric_series, drift_idx, baseline, tol=0.10, consecutive=3):
    """Steps after drift until `metric_series` returns within (1+tol)*baseline
    for `consecutive` steps. baseline = acceptable pre-drift level (e.g. pre-drift MAE).

    Returns np.inf if never recovered. Lower metric is assumed better (error-like).
    """
    m = np.asarray(metric_series, dtype=float)
    thr = (1.0 + tol) * baseline
    run = 0
    for i in range(int(drift_idx), len(m)):
        if np.isnan(m[i]):
            continue
        if m[i] <= thr:
            run += 1
            if run >= consecutive:
                return float(i - consecutive + 1 - drift_idx)
        else:
            run = 0
    return float("inf")


def onset_index(metric_series, ref_level, tol, consecutive=3):
    """First index where an error-like series degrades past (1+tol)*ref_level for
    `consecutive` steps. Used for RQ5 (compare onset of PICP-loss vs MAE-loss).
    Returns np.inf if no onset. For coverage (higher better) negate & adjust upstream.
    """
    m = np.asarray(metric_series, dtype=float)
    thr = (1.0 + tol) * ref_level
    run = 0
    for i in range(len(m)):
        if np.isnan(m[i]):
            continue
        if m[i] > thr:
            run += 1
            if run >= consecutive:
                return float(i - consecutive + 1)
        else:
            run = 0
    return float("inf")
