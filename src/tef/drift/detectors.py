"""Concept/data-drift detectors in pure NumPy (no `river` dependency).

Families:
- PageHinkley  : cumulative-deviation change detector on a 1-D stream (errors).
- ADWIN        : adaptive windowing; simplified two-subwindow mean-change test.
- ks_test      : distributional shift between reference and current windows.
- psi          : Population Stability Index between reference and current.
- ExplanationShiftDetector : Teixeira et al. (2026) SHAP-drift-score, rerouted.

Each streaming detector exposes .update(x)->bool (alarm this step) and .reset().
`fit_stream` returns the list of alarm indices over an array.
"""
from __future__ import annotations
import numpy as np
from scipy.stats import ks_2samp


class PageHinkley:
    def __init__(self, delta=0.005, lambda_=50.0, alpha=0.9999):
        self.delta, self.lambda_, self.alpha = delta, lambda_, alpha
        self.reset()

    def reset(self):
        self.mean = 0.0
        self.n = 0
        self.m_t = 0.0
        self.m_min = 0.0

    def update(self, x: float) -> bool:
        self.n += 1
        self.mean += (x - self.mean) / self.n
        self.m_t = self.alpha * self.m_t + (x - self.mean - self.delta)
        self.m_min = min(self.m_min, self.m_t)
        return (self.m_t - self.m_min) > self.lambda_


class ADWIN:
    """Simplified ADWIN: keep a bounded window, split it, flag if the two halves'
    means differ beyond a Hoeffding-style bound. Drops the older half on alarm.
    Good enough as a research baseline; use `river.ADWIN` for the canonical version.
    """

    def __init__(self, delta=0.002, max_window=1000, min_sub=30):
        self.delta, self.max_window, self.min_sub = delta, max_window, min_sub
        self.reset()

    def reset(self):
        self.w = []

    def update(self, x: float) -> bool:
        self.w.append(float(x))
        if len(self.w) > self.max_window:
            self.w.pop(0)
        n = len(self.w)
        if n < 2 * self.min_sub:
            return False
        arr = np.asarray(self.w)
        for cut in range(self.min_sub, n - self.min_sub + 1):
            n0, n1 = cut, n - cut
            m0, m1 = arr[:cut].mean(), arr[cut:].mean()
            var = arr.var() + 1e-12
            m = 1.0 / (1.0 / n0 + 1.0 / n1)
            eps = np.sqrt(2.0 / m * var * np.log(2.0 / self.delta)) \
                + 2.0 / (3.0 * m) * np.log(2.0 / self.delta)
            if abs(m0 - m1) > eps:
                self.w = self.w[cut:]  # forget the stale part
                return True
        return False


def fit_stream(detector, stream) -> list:
    """Run a streaming detector over `stream`; return indices where it alarmed."""
    detector.reset()
    alarms = []
    for i, x in enumerate(np.asarray(stream, float).ravel()):
        if detector.update(x):
            alarms.append(i)
    return alarms


def ks_test(reference, current, alpha=0.05):
    """Two-sample KS test. Returns (is_drift, p_value)."""
    stat, p = ks_2samp(np.asarray(reference, float), np.asarray(current, float))
    return bool(p < alpha), float(p)


def psi(reference, current, bins=10, eps=1e-6) -> float:
    """Population Stability Index using quantile bins of the reference."""
    ref = np.asarray(reference, float)
    cur = np.asarray(current, float)
    edges = np.quantile(ref, np.linspace(0, 1, bins + 1))
    edges[0], edges[-1] = -np.inf, np.inf
    r_prop = np.histogram(ref, edges)[0] / max(len(ref), 1) + eps
    c_prop = np.histogram(cur, edges)[0] / max(len(cur), 1) + eps
    return float(np.sum((c_prop - r_prop) * np.log(c_prop / r_prop)))


class ExplanationShiftDetector:
    """SHAP-drift-score detector (Teixeira et al. 2026), rerouted to trigger
    conformal recalibration. Detector logic is theirs and is CITED, not claimed.

    Maintains an EMA baseline mean SHAP vector `mu`, computes drift score
    D_t = ||phi_t - mu||_2, and alarms when D_t > mean(D) + k*std(D) over a
    rolling window of recent scores.
    """

    def __init__(self, n_base=200, k=2.0, ema_alpha=0.5, score_window=200):
        self.n_base, self.k, self.ema_alpha = n_base, k, ema_alpha
        self.score_window = score_window
        self.reset()

    def reset(self):
        self.mu = None
        self.n = 0
        self.scores = []

    def update(self, phi_t) -> bool:
        phi = np.asarray(phi_t, float).ravel()
        if self.mu is None:
            self.mu = phi.copy()
            self.n = 1
            self.scores.append(0.0)
            return False
        d = float(np.linalg.norm(phi - self.mu))
        alarm = False
        if self.n >= self.n_base and len(self.scores) >= 2:
            recent = np.asarray(self.scores[-self.score_window:])
            thr = recent.mean() + self.k * (recent.std() + 1e-12)
            alarm = d > thr
        # EMA update of baseline and score history.
        self.mu = (1 - self.ema_alpha) * self.mu + self.ema_alpha * phi
        self.n += 1
        self.scores.append(d)
        return alarm
