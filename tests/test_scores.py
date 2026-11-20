import numpy as np
from tef.drift.scores import (page_hinkley_scores, explanation_scores,
                              ks_scores, psi_scores, mmd_scores, matched_far_delay)


def test_mmd_scores_detect_multivariate_shift():
    rng = np.random.default_rng(3)
    n, d = 1500, 4
    pre = rng.normal(0, 1, (900, d))
    post = rng.normal(1.5, 1, (n - 900, d))   # multivariate mean shift
    X = np.vstack([pre, post])
    s = mmd_scores(X, window=100, stride=20)
    assert s[1000:].max() > s[:850].max()


def test_page_hinkley_scores_rise_after_shift():
    x = np.concatenate([np.zeros(500), np.ones(500) * 5])
    s = page_hinkley_scores(x)
    assert s[:500].max() < s[500:].max()


def test_explanation_scores_spike_on_attribution_shift():
    rng = np.random.default_rng(0)
    attr = np.concatenate([rng.normal(0, 0.1, (500, 4)),
                           rng.normal(3, 0.1, (500, 4))])
    s = explanation_scores(attr)
    assert s[520:].mean() > s[:480].mean()


def test_matched_far_calibration_hits_budget():
    rng = np.random.default_rng(1)
    # pure noise pre-onset, a clear jump after: FAR should be ~budget, delay small.
    s = np.concatenate([rng.normal(0, 1, 1000), rng.normal(6, 1, 500)])
    delay, far, tau = matched_far_delay(s, onset=1000, pre_end=1000, target_far=0.05)
    assert abs(far - 0.05) < 0.03
    assert delay is not None and delay < 20


def test_feature_detectors_have_dynamic_range_after_standardization():
    # a smooth (near-disjoint adjacent windows) feature must NOT saturate the score;
    # a feature that jumps at onset should drive it. Standardized-max handles both.
    rng = np.random.default_rng(2)
    n = 1500
    smooth = np.cumsum(rng.normal(0, 0.01, n))            # slow trend (always "drifting")
    jumper = np.concatenate([rng.normal(0, 1, 900), rng.normal(5, 1, n - 900)])
    X = np.column_stack([smooth, jumper])
    for fn in (ks_scores, psi_scores):
        s = fn(X, pre_end=900, window=100, stride=10)
        assert s[1000:].max() > s[:900].max()  # jump detected above pre-onset chatter
