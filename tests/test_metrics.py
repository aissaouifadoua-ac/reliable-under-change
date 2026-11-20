import numpy as np
from tef.metrics.point import mae, rmse, smape
from tef.metrics.interval import picp, pinaw, interval_score, crps_from_quantiles
from tef.metrics.xai import rank_correlation, explanation_drift


def test_point_basic():
    y = np.array([1.0, 2.0, 3.0])
    p = np.array([1.0, 2.0, 3.0])
    assert mae(y, p) == 0.0 and rmse(y, p) == 0.0
    assert mae(y, p + 1) == 1.0
    assert rmse(np.array([0, 0]), np.array([3, 4])) == np.sqrt(12.5)


def test_picp_bounds():
    y = np.array([1.0, 2.0, 3.0, 4.0])
    lo = np.array([0.0, 0.0, 0.0, 0.0])
    hi = np.array([5.0, 5.0, 5.0, 5.0])
    assert picp(y, lo, hi) == 1.0
    assert picp(y, np.zeros(4), np.array([1.5, 1.5, 1.5, 1.5])) == 0.25


def test_pinaw_positive():
    y = np.arange(10.0)
    assert pinaw(y, y - 1, y + 1) > 0


def test_interval_score_penalizes_miss():
    y = np.array([10.0])
    covered = interval_score(y, np.array([9.0]), np.array([11.0]), 0.9)
    missed = interval_score(y, np.array([0.0]), np.array([1.0]), 0.9)
    assert missed > covered


def test_crps_lower_is_better():
    y = np.zeros(50)
    good = np.tile([-0.1, 0.0, 0.1], (50, 1))
    bad = np.tile([-5.0, 0.0, 5.0], (50, 1))
    taus = [0.05, 0.5, 0.95]
    assert crps_from_quantiles(y, good, taus) < crps_from_quantiles(y, bad, taus)


def test_rank_corr_and_drift():
    a = np.array([3.0, 2.0, 1.0])
    assert abs(rank_correlation(a, a) - 1.0) < 1e-9
    assert explanation_drift(a, a) < 1e-9
    assert explanation_drift(a, a[::-1]) > 1.5
