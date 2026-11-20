"""Detector *score streams* for a matched-false-alarm-rate comparison.

Each detector reduces to a scalar statistic s_t; an alarm is s_t > tau. To compare
detectors fairly we calibrate tau per detector on a no-drift (pre-onset) segment to a
common false-alarm budget, then measure detection delay. This isolates detection power
from threshold choice, and lets us ask whether explanation-space monitoring adds
information beyond monitoring the raw inputs X (KS/PSI).

Families:
- page_hinkley_scores : residual change statistic (label-dependent).
- ks_scores, psi_scores : max over features of a windowed distribution distance vs a
  fixed pre-drift reference window (label-free — functions of X only).
- explanation_scores  : ||phi_t - mu_t||, the SHAP/IG-drift score (label-free).
"""
from __future__ import annotations
import numpy as np
from scipy.stats import ks_2samp


def page_hinkley_scores(x, delta=0.005, alpha=0.9999) -> np.ndarray:
    """Page-Hinkley statistic m_t - min_s m_s at each step (higher = more drift)."""
    x = np.asarray(x, float).ravel()
    mean = m_t = m_min = 0.0
    out = np.empty(len(x))
    for i, xi in enumerate(x):
        mean += (xi - mean) / (i + 1)
        m_t = alpha * m_t + (xi - mean - delta)
        m_min = min(m_min, m_t)
        out[i] = m_t - m_min
    return out


def explanation_scores(attr, ema_alpha=0.5) -> np.ndarray:
    """D_t = ||phi_t - mu_t||_2 with an EMA baseline mu (Teixeira et al. score)."""
    attr = np.asarray(attr, float)
    mu = None
    out = np.empty(len(attr))
    for i, phi in enumerate(attr):
        phi = phi.ravel()
        if mu is None:
            mu = phi.copy()
            out[i] = 0.0
        else:
            out[i] = float(np.linalg.norm(phi - mu))
            mu = (1 - ema_alpha) * mu + ema_alpha * phi
    return out


def _feature_drift_matrix(features, window=168, stride=6, kind="ks"):
    """Per-feature drift score between the current window and the immediately preceding
    (trailing-reference) window — *local* change detection, matching the explanation
    detector's EMA-baseline design. Returns an (n, p) matrix. A fixed early reference is
    unusable on seasonal energy series (winter reference vs summer window saturates the
    distance); a trailing reference compares like season to like season."""
    X = np.asarray(features, float)
    n, p = X.shape
    out = np.zeros((n, p))
    for t in range(2 * window, n, stride):
        ref = X[t - 2 * window:t - window]
        cur = X[t - window:t]
        for j in range(p):
            if kind == "ks":
                s = ks_2samp(ref[:, j], cur[:, j]).statistic
            else:  # psi
                s = _psi_pair(ref[:, j], cur[:, j])
            out[t:t + stride, j] = s
    return out


def _standardized_max(mat, pre_end):
    """Aggregate a per-feature score matrix into one stream: z-score each feature vs its
    own pre-drift baseline, then take the max across features. This gives every feature
    a common scale so a smooth feature whose adjacent windows always differ (a constant
    high KS) does not dominate — only a feature that departs from *its own* baseline
    contributes. Mirrors the explanation detector's 'deviation from baseline' logic."""
    mat = np.asarray(mat, float)
    mu = mat[:pre_end].mean(axis=0)
    sd = mat[:pre_end].std(axis=0) + 1e-9
    z = (mat - mu) / sd
    return z.max(axis=1)


def _psi_pair(ref, cur, bins=10, eps=1e-6) -> float:
    edges = np.quantile(ref, np.linspace(0, 1, bins + 1))
    edges[0], edges[-1] = -np.inf, np.inf
    r = np.histogram(ref, edges)[0] / max(len(ref), 1) + eps
    c = np.histogram(cur, edges)[0] / max(len(cur), 1) + eps
    return float(np.sum((c - r) * np.log(c / r)))


def _rbf_gram(A, B, gamma):
    d2 = (A * A).sum(1)[:, None] + (B * B).sum(1)[None, :] - 2.0 * A @ B.T
    return np.exp(-gamma * np.maximum(d2, 0.0))


def mmd_scores(features, window=96, stride=12) -> np.ndarray:
    """Squared MMD (RBF kernel) between the current and preceding window — a proper
    *multivariate* two-sample statistic on the raw inputs X. This is the strong
    raw-input comparator: if explanation monitoring beats MMD too, the gain is not
    merely 'a multivariate transform beats marginal tests'. Bandwidth via the median
    heuristic on the first reference window; features standardized column-wise first."""
    X = np.asarray(features, float)
    X = (X - X.mean(0)) / (X.std(0) + 1e-9)
    n = len(X)
    out = np.zeros(n)
    # median-heuristic bandwidth from an early reference window.
    ref0 = X[window:2 * window]
    d2 = ((ref0[:, None, :] - ref0[None, :, :]) ** 2).sum(-1)
    med = np.median(d2[d2 > 0]) if np.any(d2 > 0) else 1.0
    gamma = 1.0 / (med + 1e-9)
    for t in range(2 * window, n, stride):
        A, B = X[t - 2 * window:t - window], X[t - window:t]
        mmd2 = _rbf_gram(A, A, gamma).mean() + _rbf_gram(B, B, gamma).mean() \
            - 2.0 * _rbf_gram(A, B, gamma).mean()
        out[t:t + stride] = max(mmd2, 0.0)
    return out


def ks_scores(features, pre_end, window=168, stride=6) -> np.ndarray:
    """Standardized-max KS drift score across features (label-free, monitors X)."""
    return _standardized_max(_feature_drift_matrix(features, window, stride, "ks"), pre_end)


def psi_scores(features, pre_end, window=168, stride=6) -> np.ndarray:
    """Standardized-max PSI drift score across features (label-free, monitors X)."""
    return _standardized_max(_feature_drift_matrix(features, window, stride, "psi"), pre_end)


def matched_far_delay(scores, onset, pre_end, target_far, extra_lag=0):
    """Calibrate tau on pre-drift scores[:pre_end] to hit `target_far`, then measure
    detection delay after `onset`. Returns (delay, measured_far, tau).

    - tau = the (1 - target_far) quantile of the pre-onset score distribution, so a
      `target_far` fraction of no-drift steps cross it.
    - delay = first post-onset crossing - onset (+ extra_lag for label-dependent
      detectors whose statistic is only observable `extra_lag` steps late). None if
      the detector never fires after onset.
    """
    s = np.asarray(scores, float)
    pre = s[:pre_end]
    tau = float(np.quantile(pre, 1.0 - target_far)) if len(pre) else np.inf
    measured_far = float(np.mean(pre > tau)) if len(pre) else float("nan")
    post = np.where(s[onset:] > tau)[0]
    delay = int(post.min() + extra_lag) if len(post) else None
    return delay, measured_far, tau
