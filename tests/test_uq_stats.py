import numpy as np
from tef.uq.conformal import (SplitConformal, WindowedConformal,
                             AdaptiveConformalInference, AgACI)
from tef.metrics.interval import picp
from tef.stats.tests import (diebold_mariano, block_bootstrap_ci,
                             paired_bootstrap_diff, friedman_nemenyi, holm_bonferroni)
from tef.drift.detectors import PageHinkley, psi, ks_test, fit_stream


def test_split_conformal_coverage():
    rng = np.random.default_rng(0)
    y_cal = rng.normal(0, 1, 2000)
    yhat_cal = np.zeros(2000)
    sc = SplitConformal(0.90).calibrate(y_cal, yhat_cal)
    y_test = rng.normal(0, 1, 5000)
    lo, hi = sc.intervals(np.zeros(5000))
    assert 0.87 <= picp(y_test, lo, hi) <= 0.93


def test_aci_recovers_coverage_under_shift():
    rng = np.random.default_rng(1)
    # residual scale doubles midway (drift). ACI should hold coverage better than static.
    n = 4000
    scale = np.where(np.arange(n) < n // 2, 1.0, 3.0)
    y = rng.normal(0, scale)
    yhat = np.zeros(n)
    aci = AdaptiveConformalInference(0.90, gamma=0.05)
    aci.seed_residuals(y[:200], yhat[:200])
    lo, hi = aci.run(yhat, y)
    # coverage on the post-shift half should stay reasonably near nominal.
    cov = picp(y[n // 2 + 200:], lo[n // 2 + 200:], hi[n // 2 + 200:])
    assert cov >= 0.82


def test_aci_delayed_feedback_no_lookahead():
    # With a 24-step feedback lag, ACI must not peek at the label of the forecast just
    # issued; it should still hold coverage reasonably (long-run) under a scale shift.
    rng = np.random.default_rng(7)
    n = 6000
    scale = np.where(np.arange(n) < n // 2, 1.0, 3.0)
    y = rng.normal(0, scale)
    yhat = np.zeros(n)
    aci = AdaptiveConformalInference(0.90, gamma=0.05).seed_residuals(y[:300], yhat[:300])
    lo, hi = aci.run(yhat, y, lag=24)
    # Bound the interval only using residuals older than `lag` — sanity: still covers.
    cov = picp(y[n // 2 + 400:], lo[n // 2 + 400:], hi[n // 2 + 400:])
    assert cov >= 0.80
    # lag=24 must differ from the look-ahead lag=1 pass (proves feedback is delayed).
    aci1 = AdaptiveConformalInference(0.90, gamma=0.05).seed_residuals(y[:300], yhat[:300])
    lo1, _ = aci1.run(yhat, y, lag=1)
    assert not np.allclose(lo, lo1)


def test_windowed_conformal_adapts_scale_but_lags_feedback():
    # Under a pure residual-scale shift, windowed conformal recovers reasonably
    # (it re-estimates the quantile on recent residuals) — the non-trivial baseline.
    rng = np.random.default_rng(11)
    n = 4000
    scale = np.where(np.arange(n) < n // 2, 1.0, 3.0)
    y = rng.normal(0, scale)
    yhat = np.zeros(n)
    lo, hi = (WindowedConformal(0.90, window=300)
              .seed_residuals(y[:200], yhat[:200]).run(yhat, y))
    cov = picp(y[n // 2 + 400:], lo[n // 2 + 400:], hi[n // 2 + 400:])
    assert cov >= 0.80  # trailing-window re-estimation handles a scale shift


def test_agaci_recovers_without_gamma_tuning():
    rng = np.random.default_rng(12)
    n = 4000
    scale = np.where(np.arange(n) < n // 2, 1.0, 3.0)
    y = rng.normal(0, scale)
    yhat = np.zeros(n)
    lo, hi = (AgACI(0.90).seed_residuals(y[:200], yhat[:200]).run(yhat, y))
    cov = picp(y[n // 2 + 200:], lo[n // 2 + 200:], hi[n // 2 + 200:])
    assert cov >= 0.82  # aggregate over the gamma grid holds coverage


def test_dm_sign():
    rng = np.random.default_rng(2)
    y = rng.normal(0, 1, 500)
    good = y + rng.normal(0, 0.1, 500)
    bad = y + rng.normal(0, 1.0, 500)
    dm, p = diebold_mariano(y, good, bad)
    assert dm < 0 and p < 0.05  # pred1 (good) significantly better


def test_bootstrap_ci_contains_mean():
    rng = np.random.default_rng(3)
    x = rng.normal(5.0, 1.0, 1000)
    pt, lo, hi = block_bootstrap_ci(x, n_boot=300, block=10)
    assert lo < 5.0 < hi and abs(pt - x.mean()) < 1e-9


def test_paired_bootstrap_detects_diff():
    rng = np.random.default_rng(4)
    a = rng.normal(1.0, 0.5, 800)
    b = rng.normal(0.0, 0.5, 800)
    d, lo, hi = paired_bootstrap_diff(a, b, n_boot=300, block=10)
    assert lo > 0  # CI excludes 0


def test_friedman_and_holm():
    scores = np.array([[1.0, 2.0, 3.0], [1.1, 2.1, 2.9], [0.9, 2.2, 3.1]])
    out = friedman_nemenyi(scores)
    assert out["avg_ranks"][0] < out["avg_ranks"][2]  # model0 best
    rej = holm_bonferroni([0.001, 0.04, 0.5])
    assert rej[0] and not rej[2]


def test_page_hinkley_alarms_on_shift():
    stream = np.concatenate([np.zeros(500), np.ones(500) * 5])
    alarms = fit_stream(PageHinkley(delta=0.01, lambda_=10), stream)
    assert any(a >= 500 for a in alarms)


def test_psi_and_ks_detect_shift():
    rng = np.random.default_rng(5)
    ref = rng.normal(0, 1, 2000)
    same = rng.normal(0, 1, 2000)
    shifted = rng.normal(3, 1, 2000)
    assert psi(ref, shifted) > psi(ref, same)
    assert ks_test(ref, shifted)[0] and not ks_test(ref, same)[0]


def test_saocp_tracks_scale_shift_with_delay():
    # Strongly adaptive conformal should hold coverage near nominal after a residual
    # scale shift, under a 24-step feedback lag, and differ from the lag-1 pass.
    from tef.uq.conformal import StronglyAdaptiveConformal
    rng = np.random.default_rng(3)
    n = 6000
    scale = np.where(np.arange(n) < n // 2, 1.0, 3.0)
    y = rng.normal(0, scale)
    yhat = np.zeros(n)
    sa = StronglyAdaptiveConformal(0.90).seed_residuals(y[:300], yhat[:300])
    lo, hi = sa.run(yhat, y, lag=24)
    assert 0.85 <= picp(y[:n // 2], lo[:n // 2], hi[:n // 2]) <= 0.95
    assert picp(y[n // 2 + 400:], lo[n // 2 + 400:], hi[n // 2 + 400:]) >= 0.85
    sa1 = StronglyAdaptiveConformal(0.90).seed_residuals(y[:300], yhat[:300])
    lo1, _ = sa1.run(yhat, y, lag=1)
    assert not np.allclose(lo, lo1)
