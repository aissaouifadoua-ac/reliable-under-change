"""Significance testing — the rigor layer (Arabzadeh & Frank 2025 note these are
'rarely reported' in energy-XAI). Diebold-Mariano, block bootstrap CIs,
Friedman + Nemenyi, and Holm-Bonferroni correction.
"""
from __future__ import annotations
import numpy as np
from scipy.stats import norm, t as student_t, rankdata, friedmanchisquare


def diebold_mariano(y_true, pred1, pred2, h=1, loss="squared"):
    """DM test of equal predictive accuracy of pred1 vs pred2.

    Returns (dm_stat, p_value). Negative dm_stat => pred1 more accurate.
    Uses Harvey-Leybourne-Newbold small-sample correction and Student-t p-values.
    """
    y = np.asarray(y_true, float).ravel()
    e1 = y - np.asarray(pred1, float).ravel()
    e2 = y - np.asarray(pred2, float).ravel()
    if loss == "squared":
        d = e1 ** 2 - e2 ** 2
    elif loss == "absolute":
        d = np.abs(e1) - np.abs(e2)
    else:
        raise ValueError(loss)
    n = len(d)
    dbar = d.mean()
    # Newey-West style variance up to lag h-1.
    gamma0 = np.mean((d - dbar) ** 2)
    var = gamma0
    for k in range(1, h):
        cov = np.mean((d[k:] - dbar) * (d[:-k] - dbar))
        var += 2.0 * (1 - k / h) * cov
    var = var / n
    if var <= 0:
        return 0.0, 1.0
    dm = dbar / np.sqrt(var)
    # HLN correction.
    corr = np.sqrt((n + 1 - 2 * h + h * (h - 1) / n) / n)
    dm *= corr
    p = 2.0 * student_t.cdf(-abs(dm), df=n - 1)
    return float(dm), float(p)


def block_bootstrap_ci(values, statistic=np.mean, n_boot=1000, block=24,
                       alpha=0.05, seed=0):
    """Moving-block bootstrap CI for a statistic of a (time-dependent) 1-D series.
    Returns (point, lo, hi).
    """
    rng = np.random.default_rng(seed)
    x = np.asarray(values, float).ravel()
    n = len(x)
    if n == 0:
        return float("nan"), float("nan"), float("nan")
    n_blocks = int(np.ceil(n / block))
    max_start = max(n - block, 0)
    stats = np.empty(n_boot)
    for b in range(n_boot):
        starts = rng.integers(0, max_start + 1, size=n_blocks)
        sample = np.concatenate([x[s:s + block] for s in starts])[:n]
        stats[b] = statistic(sample)
    lo, hi = np.quantile(stats, [alpha / 2, 1 - alpha / 2])
    return float(statistic(x)), float(lo), float(hi)


def paired_bootstrap_diff(a, b, statistic=np.mean, n_boot=1000, block=24,
                          alpha=0.05, seed=0):
    """Bootstrap CI for statistic(a) - statistic(b) with paired blocks.
    CI excluding 0 => significant difference. Returns (diff, lo, hi)."""
    rng = np.random.default_rng(seed)
    a = np.asarray(a, float).ravel()
    b = np.asarray(b, float).ravel()
    n = min(len(a), len(b))
    a, b = a[:n], b[:n]
    n_blocks = int(np.ceil(n / block))
    max_start = max(n - block, 0)
    diffs = np.empty(n_boot)
    for i in range(n_boot):
        starts = rng.integers(0, max_start + 1, size=n_blocks)
        idx = np.concatenate([np.arange(s, s + block) for s in starts])[:n]
        idx = np.clip(idx, 0, n - 1)
        diffs[i] = statistic(a[idx]) - statistic(b[idx])
    lo, hi = np.quantile(diffs, [alpha / 2, 1 - alpha / 2])
    return float(statistic(a) - statistic(b)), float(lo), float(hi)


def friedman_nemenyi(score_matrix):
    """Friedman test across models over datasets/folds + Nemenyi critical difference.

    score_matrix: (n_datasets, n_models), lower = better (e.g. MAE).
    Returns dict with friedman p, avg ranks, and Nemenyi CD (alpha=0.05).
    """
    M = np.asarray(score_matrix, float)
    n_sets, n_models = M.shape
    ranks = np.vstack([rankdata(row) for row in M])  # per-dataset ranks
    avg_ranks = ranks.mean(axis=0)
    stat, p = friedmanchisquare(*[M[:, j] for j in range(n_models)])
    # Nemenyi critical difference; q_alpha for alpha=0.05 (studentized range/sqrt2).
    q_alpha = {2: 1.960, 3: 2.343, 4: 2.569, 5: 2.728, 6: 2.850,
               7: 2.949, 8: 3.031, 9: 3.102, 10: 3.164}.get(n_models, 3.164)
    cd = q_alpha * np.sqrt(n_models * (n_models + 1) / (6.0 * n_sets))
    return {"friedman_p": float(p), "avg_ranks": avg_ranks.tolist(),
            "nemenyi_cd": float(cd)}


def holm_bonferroni(pvals, alpha=0.05):
    """Holm-Bonferroni step-down. Returns boolean array of rejections aligned to input."""
    p = np.asarray(pvals, float)
    order = np.argsort(p)
    m = len(p)
    reject = np.zeros(m, bool)
    for rank, idx in enumerate(order):
        thresh = alpha / (m - rank)
        if p[idx] <= thresh:
            reject[idx] = True
        else:
            break
    return reject
