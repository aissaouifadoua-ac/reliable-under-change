import numpy as np
import pandas as pd
from tef.scenarios.perturb import inject_drift, inject_concept_drift


def _synth(n=2000, slope=2.0, noise=0.5, seed=0):
    rng = np.random.default_rng(seed)
    x = rng.normal(0, 1, n)
    target = slope * x + rng.normal(0, noise, n)
    return pd.DataFrame({"driver": x, "target": target})


def _postonset_resid_std(df, onset, slope_fit=None):
    pre = slice(0, onset)
    d, t = df["driver"].values, df["target"].values
    if slope_fit is None:
        dc = d[pre] - d[pre].mean()
        tc = t[pre] - t[pre].mean()
        slope_fit = (dc @ tc) / (dc @ dc)
    post = slice(onset, len(df))
    return (t[post] - slope_fit * d[post]).std()


def test_conditional_drift_breaks_the_map():
    df = _synth()
    d, onset = inject_drift(df, onset_frac=0.5, magnitude=2.0, drift_type="conditional")
    # Concept shift => residuals under the pre-onset map inflate well above noise.
    assert _postonset_resid_std(d, onset) > 0.9


def test_covariate_drift_preserves_the_map():
    df = _synth()
    d, onset = inject_drift(df, onset_frac=0.5, magnitude=2.0, drift_type="covariate")
    # P(X) shifts but P(Y|X) is preserved => residuals stay near the noise level.
    assert _postonset_resid_std(d, onset) < 0.7
    # And the driver's post-onset mean has actually moved (distribution changed).
    assert abs(d["driver"].values[onset:].mean()
               - d["driver"].values[:onset].mean()) > 0.3


def test_gradual_is_milder_than_abrupt():
    df = _synth()
    a, on = inject_drift(df, onset_frac=0.5, magnitude=3.0, drift_type="conditional",
                         transition=0)
    g, _ = inject_drift(df, onset_frac=0.5, magnitude=3.0, drift_type="conditional",
                        transition=500)
    assert _postonset_resid_std(g, on) < _postonset_resid_std(a, on)


def test_conditional_shift_propagates_into_autoregressive_features():
    # The claimed mechanism (a conditional shift acquires an input signature via
    # target lags) requires features to be built AFTER injection, causally from the
    # perturbed target. Verify target_lag1 post-onset reflects the modified target.
    from tef.data.features import build_features
    df = _synth(n=1500)
    d, onset = inject_drift(df, onset_frac=0.5, magnitude=3.0, drift_type="conditional")
    X, y = build_features(d, lags=(1,), rolling=(), calendar=False)
    # target_lag1 at row t must equal the (possibly perturbed) target at t-1.
    t = onset + 50
    assert np.isclose(X["target_lag1"].iloc[t], d["target"].iloc[t - 1])
    # and the perturbation actually moved the post-onset target vs the original.
    assert not np.allclose(d["target"].values[onset:], df["target"].values[onset:])


def test_backward_compatible_alias():
    df = _synth()
    a, on1 = inject_concept_drift(df, onset_frac=0.5, magnitude=2.0)
    b, on2 = inject_drift(df, onset_frac=0.5, magnitude=2.0, drift_type="conditional",
                          transition=0)
    assert on1 == on2
    assert np.allclose(a["target"].values, b["target"].values)
