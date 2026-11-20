import numpy as np
from tef.data.synthetic import make_synthetic
from tef.data.features import build_features, make_supervised
from tef.data.split import chronological_split, assert_no_leakage
from tef.experiment.runner import run, load_config


def test_split_is_chronological_and_leakfree():
    df, _ = make_synthetic(n=2000, seed=0)
    X, y = build_features(df)
    Xs, ys, _ = make_supervised(X, y, horizon=1)
    sp = chronological_split(Xs, ys)
    assert assert_no_leakage(sp)
    # scaler fit on train only => train mean ~0
    assert abs(np.nanmean(sp.X_train.values)) < 0.2


def test_no_nan_after_supervise():
    df, _ = make_synthetic(n=1500, seed=1)
    X, y = build_features(df)
    Xs, ys, _ = make_supervised(X, y, horizon=6)
    assert not Xs.isna().any().any()
    assert not ys.isna().any()


def test_runner_end_to_end():
    cfg = load_config("configs/demo.yaml")
    cfg["dataset"]["n"] = 2500  # fast
    res = run(cfg)
    assert "point_metrics" in res and "uq" in res
    # coverage keys present
    assert "drift_PICP" in res["uq"]["static_conformal"]


def test_naive_baselines_are_scale_correct():
    # Regression guard for the scaling bug: naive baselines read a target-lag column
    # as a raw-unit forecast, so they MUST use unscaled features. If they saw the
    # standardized frame, persistence MAE would inflate to the scale of the target
    # (mean|y|), i.e. many times the GBM error. Assert it stays on a sane scale.
    cfg = load_config("configs/demo.yaml")
    cfg["dataset"]["n"] = 2500
    res = run(cfg)
    pm = res["point_metrics"]
    assert pm["persistence"]["MAE"] < 5 * pm["gbm"]["MAE"]
    assert pm["seasonal_naive"]["MAE"] < 5 * pm["gbm"]["MAE"]
