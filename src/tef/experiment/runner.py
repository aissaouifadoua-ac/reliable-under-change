"""Config-driven experiment runner.

Ties the pipeline together for one (dataset, horizon, backbone, scenario) cell and
emits the RQ-aligned result records. Designed so a full confirmatory sweep just
loops this over the frozen grid. Runs end-to-end with core deps only.
"""
from __future__ import annotations
import json
import os
import time
from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd
import yaml

from tef.data.synthetic import make_synthetic
from tef.data.features import build_features, make_supervised, remap_index
from tef.data.split import chronological_split, assert_no_leakage
from tef.models.baselines import Persistence, SeasonalNaive, Ridge
from tef.models.gbm import GBMRegressor
from tef.uq.conformal import (SplitConformal, WindowedConformal,
                              AdaptiveConformalInference, AgACI)
from tef.drift.detectors import (PageHinkley, ExplanationShiftDetector, fit_stream)
from tef.xai.attributions import tree_attributions, global_importance
from tef.metrics.point import point_metrics
from tef.metrics.interval import interval_metrics, picp
from tef.metrics.drift import rolling_mae, detection_delay, false_alarm_rate, onset_index
from tef.metrics.xai import feature_removal_degradation
from tef.stats.tests import diebold_mariano, paired_bootstrap_diff, block_bootstrap_ci


def load_config(path):
    with open(path) as f:
        return yaml.safe_load(f)


def _load_dataset(cfg):
    name = cfg["dataset"]["name"]
    train = cfg["split"]["train"]
    cal = cfg["split"]["calibrate"]
    test_frac = 1.0 - train - cal
    inj = cfg["scenario"]["injected"]
    start = inj["start_frac"]
    onset_full = (train + cal) + start * test_frac  # onset inside the test window
    mag = inj["magnitude"]
    drift_type = inj.get("drift_type", "conditional")  # conditional | covariate
    transition_frac = float(inj.get("transition_frac", 0.0))  # 0 = abrupt; >0 = gradual
    kind = cfg["scenario"]["kind"]

    # Rolling-origin: `frac_end` truncates the series to an earlier endpoint, so each
    # fold trains on a different (expanding) history and tests on a different period —
    # giving genuine data-level variance (vs onset/seed alone).
    frac_end = float(cfg["dataset"].get("frac_end", 1.0))

    if name == "synthetic":
        n = int(cfg["dataset"]["n"] * frac_end)
        df, onset = make_synthetic(n=n, seed=cfg["seed"],
                                   drift_onset_frac=onset_full, drift_magnitude=mag)
        return df, onset

    # Real datasets: thin loader → truncate to endpoint → optional drift overlay.
    from tef.data.loaders import load
    from tef.scenarios.perturb import inject_drift
    df, _ = load(name, **cfg["dataset"].get("loader_kwargs", {}))
    if cfg["dataset"].get("n"):  # optional fixed-row truncation for quick runs
        df = df.iloc[: int(cfg["dataset"]["n"])]
    if frac_end < 1.0:
        df = df.iloc[: int(len(df) * frac_end)]
    if kind == "injected_drift":
        # Speed: ramp width in steps = transition_frac of the test window.
        transition = int(transition_frac * test_frac * len(df))
        df, onset = inject_drift(df, onset_frac=onset_full, magnitude=mag,
                                 drift_type=drift_type, transition=transition)
        return df, onset
    return df, None  # natural-drift / normal scenario: no ground-truth onset


def run(cfg: dict) -> dict:
    rng_seed = cfg["seed"]
    np.random.seed(rng_seed)

    # 1. Data + features + leakage-safe supervised framing.
    df, raw_onset = _load_dataset(cfg)
    X, y = build_features(df, lags=tuple(cfg["features"]["lags"]),
                          rolling=tuple(cfg["features"]["rolling"]),
                          calendar=cfg["features"]["calendar"])
    # Anti-leakage guard: features are built AFTER any drift injection, so an injected
    # conditional shift enters the autoregressive (target-lag) inputs causally — the
    # mechanism the explanation detector relies on. Verify a post-onset lag matches the
    # perturbed target (the driver was already selected pre-onset in inject_drift).
    if raw_onset is not None and "target_lag1" in X.columns:
        _t = min(raw_onset + 50, len(df) - 1)
        assert np.isclose(X["target_lag1"].iloc[_t], df["target"].iloc[_t - 1]), \
            "autoregressive features are not causal w.r.t. the injected target"
    Xs, ys, kept = make_supervised(X, y, horizon=cfg["dataset"]["horizon"])

    sp = chronological_split(Xs, ys, cfg["split"]["train"], cfg["split"]["calibrate"])
    assert_no_leakage(sp)

    # 1b. Robustness scenarios (Pre-Registration §5): perturb TEST features only
    # (train/calibrate untouched) to test whether reliability degrades. `normal`
    # and `injected_drift` need no feature perturbation here.
    kind = cfg["scenario"]["kind"]
    if kind == "missing":
        from tef.scenarios.perturb import inject_missing
        frac = cfg["scenario"].get("missing_frac", 0.10)
        sp.X_test.loc[:, :] = inject_missing(sp.X_test, frac=frac, seed=rng_seed).values
    elif kind == "noise":
        from tef.scenarios.perturb import add_noise
        snr = cfg["scenario"].get("snr_db", 20.0)
        sp.X_test.loc[:, :] = add_noise(sp.X_test, snr_db=snr, seed=rng_seed).values
    # Onset position within the TEST frame (for drift metrics). None => natural
    # drift with no ground truth: detection-delay/false-alarm are not computed.
    has_onset = raw_onset is not None
    if has_onset:
        onset_sup = remap_index(raw_onset, kept)
        onset_in_test = int(np.clip(onset_sup - sp.cal_end, 0, len(sp.y_test) - 1))
    else:
        onset_in_test = len(sp.y_test) // 2  # region split only; not ground truth

    # 2. Backbone + baselines. Baselines always train on tabular features.
    backbone = cfg["model"]["backbone"]
    models = {"persistence": Persistence(), "seasonal_naive": SeasonalNaive(),
              "ridge": Ridge()}
    if backbone == "gbm":
        models["gbm"] = GBMRegressor(random_state=rng_seed)
    main_key = {"gbm": "gbm", "ridge": "ridge", "patchtst": "patchtst"}[backbone]

    # Naive baselines read a target-lag column directly as a raw-unit forecast, so they
    # must see the UNSCALED features; learned models (ridge/gbm) use the scaled frames.
    naive = {"persistence", "seasonal_naive"}
    preds_test, preds_cal = {}, {}
    timings = {}
    for k, m in models.items():
        Xtr = sp.X_train  # naive .fit is a no-op, so the scaled train frame is harmless
        Xte = sp.X_test_raw if k in naive else sp.X_test
        Xca = sp.X_cal_raw if k in naive else sp.X_cal
        t0 = time.perf_counter()
        m.fit(Xtr, sp.y_train)
        timings[f"train_{k}_s"] = time.perf_counter() - t0
        t1 = time.perf_counter()
        preds_test[k] = m.predict(Xte)
        timings[f"infer_{k}_s"] = time.perf_counter() - t1
        preds_cal[k] = m.predict(Xca)

    # PatchTST: a sequence backbone trained on lookback windows of the target,
    # aligned 1:1 with the tabular split so it shares the conformal/drift pipeline.
    seq_test = patch_model = None
    if backbone == "patchtst":
        from tef.models.patchtst import PatchTSTForecaster, build_sequences
        L = int(cfg["model"].get("lookback", 96))
        tgt_ft = y.reindex(Xs.index).to_numpy()          # feature-time target
        seqs = build_sequences(tgt_ft, lookback=L)
        seq_tr, seq_cal, seq_te = (seqs[:sp.train_end],
                                   seqs[sp.train_end:sp.cal_end], seqs[sp.cal_end:])
        t0 = time.perf_counter()
        patch_model = PatchTSTForecaster(
            lookback=L, epochs=int(cfg["model"].get("epochs", 40)),
            random_state=rng_seed).fit(seq_tr, sp.y_train.values)
        timings["train_patchtst_s"] = time.perf_counter() - t0
        t1 = time.perf_counter()
        preds_test["patchtst"] = patch_model.predict(seq_te)
        timings["infer_patchtst_s"] = time.perf_counter() - t1
        preds_cal["patchtst"] = patch_model.predict(seq_cal)
        seq_test = seq_te

    y_test = sp.y_test.values
    y_cal = sp.y_cal.values

    # 3. Point metrics (RQ1) — over all trained predictors, baselines + main.
    point = {k: point_metrics(y_test, v) for k, v in preds_test.items()}

    # 4. UQ: static split conformal vs adaptive conformal (RQ2/RQ3).
    nominal = cfg["uq"]["nominal"]
    yhat = preds_test[main_key]
    yhat_cal = preds_cal[main_key]

    gamma = cfg["uq"]["adaptive_conformal"]["gamma"]
    cf_window = int(cfg["uq"].get("window", 500))
    # Delayed feedback: a horizon-h forecast's label is observed h steps after issuance,
    # so every label-driven update (ACI/AgACI/windowed) lags by the horizon — no
    # look-ahead at multi-step horizons. lag=1 recovers the one-step-ahead setting.
    lag = int(cfg["dataset"]["horizon"])

    t0 = time.perf_counter()
    static = SplitConformal(nominal).calibrate(y_cal, yhat_cal)
    lo_s, hi_s = static.intervals(yhat)
    timings["static_conformal_s"] = time.perf_counter() - t0

    # The adaptation family, benchmarked head-to-head against the static baseline:
    # windowed (rolling quantile) → ACI (coverage feedback) → AgACI (gamma-aggregated).
    t0 = time.perf_counter()
    lo_w, hi_w = (WindowedConformal(nominal, window=cf_window)
                  .seed_residuals(y_cal, yhat_cal).run(yhat, y_test, lag=lag))
    timings["windowed_conformal_s"] = time.perf_counter() - t0

    t0 = time.perf_counter()
    aci = AdaptiveConformalInference(nominal, gamma=gamma, window=cf_window
                                     ).seed_residuals(y_cal, yhat_cal)
    lo_a, hi_a = aci.run(yhat, y_test, lag=lag)
    timings["adaptive_conformal_s"] = time.perf_counter() - t0
    # Per-step recalibration cost (the adaptive layer is one scalar update per point):
    timings["recalibrate_per_step_s"] = timings["adaptive_conformal_s"] / max(len(y_test), 1)

    t0 = time.perf_counter()
    lo_g, hi_g = (AgACI(nominal, window=cf_window)
                  .seed_residuals(y_cal, yhat_cal).run(yhat, y_test, lag=lag))
    timings["agaci_s"] = time.perf_counter() - t0

    # Coverage in stable vs drift regions.
    lw = min(168, len(y_test) // 4 or 1)  # local-coverage window

    def _regional(lo, hi):
        stable = slice(0, onset_in_test)
        drift = slice(onset_in_test, len(y_test))
        # Worst-window LOCAL coverage: ACI regulates long-run (aggregate) coverage by
        # construction, so the operationally meaningful question is how low coverage
        # dips in any rolling window — this exposes local miscalibration the aggregate
        # PICP hides.
        flag = ((y_test >= lo) & (y_test <= hi)).astype(float)
        roll = pd.Series(flag).rolling(lw).mean().values
        rv = roll[np.isfinite(roll)]
        worst_local = float(np.nanmin(roll)) if rv.size else float("nan")
        # Richer local summaries: a minimum over many overlapping windows is an extreme
        # statistic, so we also report the 5th-percentile local coverage and the fraction
        # of windows below 0.85. `local_coverage_null` (below) gives what the minimum
        # would be under a stable nominal process, making these values interpretable.
        p05_local = float(np.percentile(rv, 5)) if rv.size else float("nan")
        frac_below_085 = float(np.mean(rv < 0.85)) if rv.size else float("nan")
        return {
            "overall": interval_metrics(y_test, lo, hi, nominal),
            "stable_PICP": picp(y_test[stable], lo[stable], hi[stable])
            if onset_in_test > 0 else float("nan"),
            "drift_PICP": picp(y_test[drift], lo[drift], hi[drift]),
            "worst_local_PICP": worst_local,
            "p05_local_PICP": p05_local,
            "frac_local_below_085": frac_below_085,
        }

    uq = {"static_conformal": _regional(lo_s, hi_s),
          "windowed_conformal": _regional(lo_w, hi_w),
          "adaptive_conformal": _regional(lo_a, hi_a),
          "agaci": _regional(lo_g, hi_g)}
    # Null band: worst 168-h rolling coverage under a *stable* nominal-coverage process
    # (iid Bernoulli(nominal) of the same length). This is what "min local coverage"
    # looks like with no drift at all, so an observed minimum is only meaningful if it
    # falls below this band. (iid understates autocorrelation, so it is a conservative
    # — narrow — reference.)
    _rng = np.random.default_rng(rng_seed)
    _null_mins = [np.nanmin(pd.Series(_rng.binomial(1, nominal, len(y_test)).astype(float))
                            .rolling(lw).mean().values) for _ in range(200)]
    uq["local_coverage_null"] = {
        "worst_p05": float(np.percentile(_null_mins, 5)),
        "worst_median": float(np.median(_null_mins)),
        "window": int(lw),
    }

    # 5. Drift detection + RQ5 (coverage-before-accuracy) using the main model.
    # The residual of a horizon-h forecast is only observable h steps after issuance,
    # so a residual-based alarm at issuance-index i is actionable only at i+lag. The
    # explanation-shift trigger (label-free, from inputs x_t) has no such delay.
    resid = np.abs(y_test - yhat)
    t0 = time.perf_counter()
    _ph_raw = fit_stream(PageHinkley(**cfg["drift"]["page_hinkley"]), resid)
    timings["page_hinkley_per_step_s"] = (time.perf_counter() - t0) / max(len(resid), 1)
    ph_alarms = [a + lag for a in _ph_raw]

    win = 168
    rmae = rolling_mae(y_test, yhat, window=min(win, len(y_test) // 4 or 1))
    # rolling coverage-loss series for static intervals (1-PICP over window).
    cov_flag = ((y_test >= lo_s) & (y_test <= hi_s)).astype(float)
    miscov = 1.0 - pd.Series(cov_flag).rolling(min(win, len(y_test) // 4 or 1)).mean().values
    pre = slice(0, onset_in_test) if onset_in_test > 10 else slice(0, len(y_test) // 3)
    mae_base = np.nanmean(rmae[pre]) if np.isfinite(np.nanmean(rmae[pre])) else np.nanmean(rmae)
    mis_base = np.nanmean(miscov[pre]) if np.isfinite(np.nanmean(miscov[pre])) else np.nanmean(miscov)
    mae_onset = onset_index(rmae, mae_base, tol=0.20)
    cov_onset = onset_index(miscov, mis_base + 1e-9, tol=0.50)
    coverage_before_accuracy = float(mae_onset - cov_onset)  # >0 => coverage first

    # Drift severity/speed characterization: coverage deficit (how far static falls)
    # and recovery time (how long each method's rolling coverage stays broken after
    # onset). Recovery = steps from onset to the last point still below nominal-tol.
    w_cov = min(win, len(y_test) // 4 or 1)

    def _recovery_steps(lo, hi, delta=0.05, hold=24):
        """Operational recovery: steps from onset until rolling coverage first re-enters
        the tolerance band [nominal±delta] AND stays inside it for `hold` consecutive
        windows (so a single noisy up-crossing does not count). Uses the same delta as
        the practical-calibration test. Censored at the post-onset length if it never
        recovers (e.g. static under a persistent shift)."""
        flag = ((y_test >= lo) & (y_test <= hi)).astype(float)
        roll = pd.Series(flag).rolling(w_cov).mean().values
        inband = (roll >= nominal - delta) & (roll <= nominal + delta)
        post_len = len(y_test) - onset_in_test
        for t in range(onset_in_test, len(roll) - hold):
            if inband[t:t + hold].all():
                return int(t - onset_in_test)
        return int(post_len)

    drift_char = {
        "static_coverage_deficit": float(nominal - uq["static_conformal"]["drift_PICP"]),
        "recovery_static": _recovery_steps(lo_s, hi_s),
        "recovery_windowed": _recovery_steps(lo_w, hi_w),
        "recovery_adaptive": _recovery_steps(lo_a, hi_a),
        "recovery_agaci": _recovery_steps(lo_g, hi_g),
    }

    # 6. Explanation-shift detector on streaming attributions (RQ6/RQ7). SHAP for
    # the tree model; Integrated Gradients for the deep sequence model.
    exp_alarms = []
    fidelity = None
    attr_test = X_attr = predict_attr = None
    t0 = time.perf_counter()
    if backbone == "gbm":
        attr_test = tree_attributions(models["gbm"], sp.X_test.values)
        X_attr, predict_attr = sp.X_test.values, models["gbm"].predict
    elif backbone == "patchtst" and patch_model is not None:
        attr_test = patch_model.integrated_gradients(seq_test)
        X_attr, predict_attr = seq_test, patch_model.predict
    if attr_test is not None:
        # Per-step attribution (monitor) cost — TreeSHAP for GBM, IG for PatchTST. This
        # is the compute the explanation monitor adds on top of the scalar ACI update.
        timings["attribution_per_step_s"] = (time.perf_counter() - t0) / max(len(attr_test), 1)
        t1 = time.perf_counter()
        esd = ExplanationShiftDetector(**cfg["drift"]["explanation_shift"])
        for t in range(attr_test.shape[0]):
            if esd.update(attr_test[t]):
                exp_alarms.append(t)
        timings["explanation_detector_per_step_s"] = (
            time.perf_counter() - t1) / max(attr_test.shape[0], 1)
        imp = global_importance(attr_test)
        fidelity = feature_removal_degradation(
            predict_attr, X_attr, y_test, imp,
            top_k=max(1, X_attr.shape[1] // 4), rng=rng_seed)

    # 7. Detection metrics vs ground-truth onset (RQ4). Only meaningful when the
    # onset is known (synthetic or injected_drift); for natural drift we report
    # alarm counts only.
    n_test = len(y_test)
    drift_eval = {"onset_in_test": int(onset_in_test), "has_ground_truth": has_onset}

    # Coverage-failure index: first step AT/AFTER the true onset where static rolling
    # coverage drops >5 points below nominal. Anchoring the search at the true onset
    # makes this robust to pre-onset noise (unlike a global change-point on miscov).
    roll_static_cov = pd.Series(cov_flag).rolling(w_cov).mean().values
    if has_onset:
        post_ix = np.arange(onset_in_test, n_test)
        broke = post_ix[roll_static_cov[onset_in_test:] < nominal - 0.05]
        cov_fail = int(broke.min()) if len(broke) else n_test
    else:
        cov_fail = None
    drift_eval["coverage_fail_index"] = cov_fail

    def _det(alarms, label_free):
        rec = {"n_alarms": len(alarms), "label_free": label_free}
        if has_onset:
            # Coverage-failure lead-time: does the detector fire (after the true onset)
            # BEFORE static coverage visibly breaks (cov_fail)? Pre-onset chatter is
            # excluded — that is what false_alarm_rate captures — so a positive lead is
            # a genuine early warning of impending miscalibration.
            post = [a for a in alarms if a >= onset_in_test]
            first_post = min(post) if post else None
            lead = int(cov_fail - first_post) if first_post is not None else None
            rec.update({"delay": detection_delay(alarms, onset_in_test),
                        "false_alarm_rate": false_alarm_rate(alarms, onset_in_test, n_test),
                        "coverage_lead": lead})
        else:
            rec.update({"delay": None, "false_alarm_rate": None, "coverage_lead": None})
        return rec

    # The explanation-shift signal is LABEL-FREE (attributions depend on inputs x_t
    # only); the residual detector needs the realized y_t. That is the operational edge.
    drift_eval["page_hinkley"] = _det(ph_alarms, label_free=False)
    if attr_test is not None:
        drift_eval["explanation_shift"] = _det(exp_alarms, label_free=True)

    # 8. Per-cell significance (the rigor layer; aggregated across seeds later).
    # RQ1: Diebold-Mariano, main model vs each baseline (negative dm => main better).
    rq1_dm = {}
    for base in ("persistence", "seasonal_naive", "ridge"):
        if base in preds_test and base != main_key:
            dm, p = diebold_mariano(y_test, yhat, preds_test[base], h=cfg["dataset"]["horizon"])
            rq1_dm[f"{main_key}_vs_{base}"] = {"dm": dm, "p": p}
    # RQ3: paired bootstrap of (method covered - static covered) in the drift region,
    # for every adaptive competitor in the family.
    d = slice(onset_in_test, len(y_test))
    cov_s = ((y_test[d] >= lo_s[d]) & (y_test[d] <= hi_s[d])).astype(float)

    def _paired_vs_static(lo, hi):
        cov_m = ((y_test[d] >= lo[d]) & (y_test[d] <= hi[d])).astype(float)
        diff, lo_ci, hi_ci = paired_bootstrap_diff(
            cov_m, cov_s, n_boot=cfg["stats"]["n_boot"], block=cfg["stats"]["block"],
            seed=rng_seed)
        return {"minus_static_drift_coverage": diff, "ci_lo": lo_ci, "ci_hi": hi_ci,
                "significant": bool(lo_ci > 0 or hi_ci < 0)}

    rq3_family = {"windowed_conformal": _paired_vs_static(lo_w, hi_w),
                  "adaptive_conformal": _paired_vs_static(lo_a, hi_a),
                  "agaci": _paired_vs_static(lo_g, hi_g)}
    # Back-compat: keep the flat adaptive-vs-static record the sweep/figures read.
    _a = rq3_family["adaptive_conformal"]
    rq3_paired = {"adaptive_minus_static_drift_coverage": _a["minus_static_drift_coverage"],
                  "ci_lo": _a["ci_lo"], "ci_hi": _a["ci_hi"],
                  "significant": _a["significant"]}

    # Equivalence-to-nominal (practical calibration): the operational question is not
    # "better than static" but |coverage - nominal| < delta. We form a dependence-aware
    # block-bootstrap CI for each method's drift-region coverage and declare it
    # practically calibrated at tolerance delta iff the whole CI lies in [nominal±delta]
    # (a CI-in-interval / TOST-style test). Blocks are drawn within the drift region.
    def _equivalence(lo, hi):
        cov = ((y_test[d] >= lo[d]) & (y_test[d] <= hi[d])).astype(float)
        pt, clo, chi = block_bootstrap_ci(cov, n_boot=cfg["stats"]["n_boot"],
                                          block=cfg["stats"]["block"], seed=rng_seed)
        return {"picp": pt, "ci_lo": clo, "ci_hi": chi,
                "equiv_02": bool(clo >= nominal - 0.02 and chi <= nominal + 0.02),
                "equiv_05": bool(clo >= nominal - 0.05 and chi <= nominal + 0.05)}

    equivalence = {"static_conformal": _equivalence(lo_s, hi_s),
                   "windowed_conformal": _equivalence(lo_w, hi_w),
                   "adaptive_conformal": _equivalence(lo_a, hi_a),
                   "agaci": _equivalence(lo_g, hi_g)}

    result = {
        "config": {k: cfg[k] for k in ("seed", "dataset", "model", "uq", "scenario")},
        "backbone_used": getattr(models.get("gbm"), "backend", "n/a"),
        "n_test": int(n_test),
        "point_metrics": point,
        "uq": uq,
        "rq5_coverage_before_accuracy_steps": coverage_before_accuracy,
        "rq5_detail": {"mae_onset": mae_onset, "cov_onset": cov_onset},
        "drift_char": drift_char,
        "drift_eval": drift_eval,
        "xai_fidelity": fidelity,
        "rq1_dm": rq1_dm,
        "rq3_paired": rq3_paired,
        "rq3_family": rq3_family,
        "equivalence": equivalence,
        "timings": timings,
        "main_key": main_key,
    }
    # Optional per-step arrays for the reliability-over-time figure (opt-in; large).
    if cfg.get("return_diagnostics"):
        result["diagnostics"] = {
            "y_test": y_test, "lo_static": lo_s, "hi_static": hi_s,
            "lo_windowed": lo_w, "hi_windowed": hi_w,
            "lo_adaptive": lo_a, "hi_adaptive": hi_a,
            "lo_agaci": lo_g, "hi_agaci": hi_g, "onset_in_test": int(onset_in_test),
            # Point forecasts and calibration residual inputs, so further conformal
            # rungs can be run on exactly the same forecasts without refitting.
            "yhat": yhat, "y_cal": y_cal, "yhat_cal": yhat_cal, "lag": int(lag),
            "index": [str(x) for x in sp.y_test.index],
        }
    # Optional raw streams for the matched-FAR detector comparison (opt-in; large).
    # Residuals are label-dependent (lagged); feature/attribution streams are label-free.
    if cfg.get("return_detector_streams"):
        result["detector_streams"] = {
            "resid": np.abs(y_test - yhat),
            "features": sp.X_test.values,
            "feature_names": list(sp.X_test.columns),
            "attributions": attr_test,
            "onset_in_test": int(onset_in_test),
            "cov_fail_index": cov_fail,
            "horizon": int(lag),
        }
    return result


def run_from_file(path, out=None):
    cfg = load_config(path)
    res = run(cfg)
    out_dir = out or cfg.get("output_dir", "results/demo")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "result.json"), "w") as f:
        json.dump(res, f, indent=2, default=str)
    return res
