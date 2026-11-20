"""Grid sweep + aggregation → the paper's master tables.

Loops the frozen confirmatory grid (datasets × horizons × backbones × scenarios ×
seeds), runs each cell via `runner.run`, flattens results into tidy records, then
aggregates across seeds (mean ± std) and applies the significance layer:
- RQ1 point accuracy + DM win-rate across seeds
- RQ2/RQ3 static vs adaptive coverage (stable/drift) + paired-bootstrap significance
- RQ4/RQ6 detector delay / false-alarm (error vs explanation trigger)
- RQ5 coverage-before-accuracy lead-time
- RQ7 explanation fidelity
Across datasets, RQ1 ranks models with Friedman + Nemenyi.

Outputs CSVs + a Markdown summary under `output_dir`.
"""
from __future__ import annotations
import copy
import itertools
import os

import numpy as np
import pandas as pd

from tef.experiment.runner import run
from tef.stats.tests import friedman_nemenyi


# Per-dataset loader kwargs (loaders auto-detect when empty).
DATASET_KWARGS = {
    "opsd": {"country": "DE", "target": "load"},
    "uci": {},
    "unisolar": {},
    "synthetic": {},
}


def default_grid():
    """The confirmatory grid (Pre-Registration §2). Trim for quick runs.

    `onset_frac` is a resampling dimension: drift is injected at different points
    of the test window, so aggregate metrics have genuine variance (the seed alone
    only perturbs model init on identical data). Report mean±std over seed×onset.
    """
    return {
        "dataset": ["opsd", "uci", "unisolar"],  # unisolar = exploratory PV target
        "horizon": [1, 24],                       # drop 6 to bound cell count
        "backbone": ["gbm", "ridge"],             # two backbones => Friedman ranking
        "scenario": ["injected_drift"],
        "onset_frac": [0.4, 0.6],                 # drift-location Monte Carlo
        "seed": [7, 13],                          # model-init replicates
    }                                             # = 3*2*2*1*2*2 = 48 cells


def rolling_grid():
    """Rolling-origin evaluation: variance comes from the data period (frac_end
    truncates to an expanding endpoint), not just drift-onset location. This is the
    reviewer-expected backtest and the fix for the onset-only error-bar caveat."""
    return {
        "dataset": ["opsd", "uci"],
        "horizon": [1, 24],
        "backbone": ["gbm"],
        "scenario": ["injected_drift"],
        "frac_end": [0.6, 0.73, 0.87, 1.0],  # 4 expanding-window folds
        "onset_frac": [0.5],
        "seed": [7],
    }                                        # = 2*2*1*1*4*1*1 = 16 cells


def drift_taxonomy_grid():
    """Drift as a first-class variable (reviewer #2): sweep severity (magnitude) ×
    speed (transition_frac) × type (conditional P(Y|X) vs covariate P(X)). Produces
    the severity→coverage-deficit and speed→recovery-time curves. One dataset +
    backbone so the axes — not dataset noise — drive the variation."""
    return {
        "dataset": ["opsd"],
        "horizon": [1],
        "backbone": ["gbm"],
        "scenario": ["injected_drift"],
        "drift_type": ["conditional", "covariate"],
        "magnitude": [1.0, 1.25, 1.5, 2.0, 3.0],   # severity
        "transition_frac": [0.0, 0.1, 0.3],         # speed: abrupt → gradual
        "onset_frac": [0.4],
        "seed": [7, 13],
    }   # = 1*1*1*1*2*5*3*1*2 = 60 cells


def family_grid():
    """The adaptation ladder under delayed feedback (static, windowed, ACI, AgACI) on the
    gradient-boosting load cells. Feeds the ladder, equivalence and local-coverage tables
    and the lead-time figure."""
    return {
        "dataset": ["opsd", "uci"],
        "horizon": [1, 24],
        "backbone": ["gbm"],
        "scenario": ["injected_drift"],
        "onset_frac": [0.4, 0.6],
        "seed": [7, 13],
    }                                             # = 2*2*1*1*2*2 = 16 cells


def patchtst_grid():
    """Deep backbone through the identical calibration, drift and attribution pipeline.
    One seed: PatchTST training dominates the compute of the whole study."""
    return {
        "dataset": ["opsd", "uci"],
        "horizon": [1, 24],
        "backbone": ["patchtst"],
        "scenario": ["injected_drift"],
        "onset_frac": [0.4, 0.6],
        "seed": [7],
    }                                             # = 2*2*1*1*2*1 = 8 cells


def scenario_grid():
    """Robustness across scenarios (Pre-Registration §5) on the confirmatory sets.
    missing/noise perturb the test features; seeds give the variance."""
    return {
        "dataset": ["opsd", "uci"],
        "horizon": [1],
        "backbone": ["gbm"],
        "scenario": ["injected_drift", "normal", "missing", "noise"],
        "onset_frac": [0.5],
        "seed": [7, 11, 13],
    }                                             # = 2*1*1*4*1*3 = 24 cells


def _flatten(res: dict, cell: dict) -> dict:
    """One tidy row per (cell) with the headline numbers for every RQ."""
    u = res["uq"]
    row = dict(cell)
    row["backbone_used"] = res["backbone_used"]
    row["n_test"] = res["n_test"]
    # RQ1
    pm = res["point_metrics"]
    main = cell["backbone"]
    row["MAE_main"] = pm.get(main, {}).get("MAE")
    row["MAE_persistence"] = pm.get("persistence", {}).get("MAE")
    for k, v in res.get("rq1_dm", {}).items():
        row[f"DM_{k}_p"] = v["p"]
        row[f"DM_{k}_stat"] = v["dm"]
    # RQ2/RQ3 — the whole adaptation family (static baseline + 3 adaptive competitors).
    method_keys = {"static": "static_conformal", "windowed": "windowed_conformal",
                   "adaptive": "adaptive_conformal", "agaci": "agaci"}
    for short, key in method_keys.items():
        m = u.get(key)
        if m is None:
            continue
        row[f"{short}_stable_PICP"] = m["stable_PICP"]
        row[f"{short}_drift_PICP"] = m["drift_PICP"]
        row[f"{short}_worst_local_PICP"] = m.get("worst_local_PICP")
        row[f"{short}_PINAW"] = m["overall"]["PINAW"]
        row[f"{short}_interval_score"] = m["overall"].get("IntervalScore")
    rp = res.get("rq3_paired", {})
    row["rq3_adaptive_minus_static_drift_cov"] = rp.get("adaptive_minus_static_drift_coverage")
    row["rq3_significant"] = rp.get("significant")
    for short in ("windowed", "adaptive", "agaci"):
        fam = (res.get("rq3_family") or {}).get(method_keys[short], {})
        row[f"rq3_{short}_significant"] = fam.get("significant")
    # Equivalence-to-nominal (practical calibration) per method: CI ⊂ [0.90±delta].
    for short, key in method_keys.items():
        eq = (res.get("equivalence") or {}).get(key, {})
        row[f"{short}_equiv02"] = eq.get("equiv_02")
        row[f"{short}_equiv05"] = eq.get("equiv_05")
    # RQ4/RQ6
    de = res["drift_eval"]
    for det in ("page_hinkley", "explanation_shift"):
        d = de.get(det, {})
        row[f"{det}_delay"] = d.get("delay")
        row[f"{det}_FAR"] = d.get("false_alarm_rate")
        row[f"{det}_nalarms"] = d.get("n_alarms")
        row[f"{det}_lead"] = d.get("coverage_lead")       # coverage-failure lead-time
        row[f"{det}_label_free"] = d.get("label_free")
    # RQ5 / RQ7
    row["rq5_cov_before_acc"] = res.get("rq5_coverage_before_accuracy_steps")
    row["fidelity_ratio"] = (res.get("xai_fidelity") or {}).get("fidelity_ratio")
    # Drift taxonomy: severity (coverage deficit) + speed (recovery time per method).
    for k, v in (res.get("drift_char") or {}).items():
        row[k] = v
    return row


def run_grid(base_cfg: dict, grid: dict | None = None,
             output_dir="results/grid") -> pd.DataFrame:
    grid = grid or default_grid()
    keys = list(grid)
    rows = []
    combos = list(itertools.product(*[grid[k] for k in keys]))
    for i, combo in enumerate(combos, 1):
        cell = dict(zip(keys, combo))
        cfg = copy.deepcopy(base_cfg)
        cfg["seed"] = cell["seed"]
        cfg["dataset"]["name"] = cell["dataset"]
        cfg["dataset"]["horizon"] = cell["horizon"]
        cfg["dataset"]["loader_kwargs"] = DATASET_KWARGS.get(cell["dataset"], {})
        cfg["dataset"].pop("n", None)
        cfg["model"]["backbone"] = cell["backbone"]
        cfg["scenario"]["kind"] = cell["scenario"]
        if "onset_frac" in cell:
            cfg["scenario"]["injected"]["start_frac"] = cell["onset_frac"]
        if "frac_end" in cell:                       # rolling-origin fold endpoint
            cfg["dataset"]["frac_end"] = cell["frac_end"]
        for k in ("magnitude", "drift_type", "transition_frac"):  # drift-taxonomy axes
            if k in cell:
                cfg["scenario"]["injected"][k] = cell[k]
        print(f"[{i}/{len(combos)}] {cell}")
        try:
            res = run(cfg)
            rows.append(_flatten(res, cell))
        except Exception as e:  # keep the sweep going; record the failure
            print(f"   FAILED: {type(e).__name__}: {e}")
            rows.append({**cell, "error": f"{type(e).__name__}: {e}"})
    df = pd.DataFrame(rows)
    os.makedirs(output_dir, exist_ok=True)
    df.to_csv(os.path.join(output_dir, "raw_cells.csv"), index=False)
    _write_tables(df, output_dir)
    return df


def rebuild_tables(raw_csv, output_dir=None):
    """Regenerate the aggregate tables + SUMMARY.md from a saved raw_cells.csv
    (so a table-writing failure doesn't require rerunning the whole grid)."""
    df = pd.read_csv(raw_csv)
    output_dir = output_dir or os.path.dirname(raw_csv)
    _write_tables(df, output_dir)
    return df


def _agg(df, group, cols):
    """mean±std across seeds, flattened to readable 'col_mean'/'col_std' columns."""
    present = [c for c in cols if c in df.columns]
    g = df.groupby(group)[present].agg(["mean", "std"])
    g.columns = [f"{c}_{stat}" for c, stat in g.columns]
    return g


def _write_tables(df: pd.DataFrame, output_dir: str):
    if "error" in df.columns:
        ok = df[df["error"].isna()] if df["error"].isna().any() else df.iloc[0:0]
    else:
        ok = df
    md = ["# Grid results (auto-generated)\n",
          f"Cells: {len(df)}  |  successful: {len(ok)}\n"]

    if len(ok) == 0:
        md.append("\n**All cells failed.** See `raw_cells.csv`.\n")
        _dump(output_dir, md, {})
        return

    # Group by design factors; aggregate (mean±std) over onset_frac × seed replicates.
    gcols = [c for c in ["dataset", "backbone", "scenario", "horizon"]
             if c in ok.columns and ok[c].nunique() > 1] or ["dataset"]

    # RQ1 — accuracy + DM win-rate.
    t1 = _agg(ok, gcols, ["MAE_main", "MAE_persistence"])
    dm_p_cols = [c for c in ok.columns if c.startswith("DM_") and c.endswith("_p")]
    if dm_p_cols:
        winrate = ok.groupby(gcols)[dm_p_cols].apply(lambda g: (g < 0.05).mean())
        winrate.to_csv(os.path.join(output_dir, "rq1_dm_winrate.csv"))
    t1.to_csv(os.path.join(output_dir, "rq1_point.csv"))
    md.append("\n## RQ1 Point accuracy (mean MAE across seeds)\n")
    md.append(t1.round(2).to_markdown())

    # RQ2/RQ3 — coverage across the adaptation family (static + windowed + ACI + AgACI).
    fam_cols = []
    for short in ("static", "windowed", "adaptive", "agaci"):
        fam_cols += [f"{short}_drift_PICP", f"{short}_PINAW", f"{short}_interval_score"]
    t23 = _agg(ok, gcols, fam_cols)
    t23.to_csv(os.path.join(output_dir, "rq23_coverage.csv"))
    md.append("\n\n## RQ2/RQ3 Adaptation family: drift-region coverage, width, interval score\n")
    md.append("Static baseline vs windowed / ACI / AgACI competitors. "
              "Drift-PICP target 0.90; lower interval score is better.\n\n")
    md.append(t23.round(3).to_markdown())
    # Significant-improvement fraction vs static for each adaptive competitor.
    sig_cols = [c for c in ["rq3_windowed_significant", "rq3_adaptive_significant",
                            "rq3_agaci_significant"] if c in ok.columns]
    if sig_cols:
        sig_rate = ok.groupby(gcols)[sig_cols].mean()
        md.append("\n\nPaired-bootstrap fraction where each method's drift coverage "
                  "differs significantly from static:\n\n")
        md.append(sig_rate.round(2).to_markdown())

    # Equivalence-to-nominal: fraction of cells practically calibrated (CI ⊂ [0.90±δ]).
    eq_cols = [c for c in ok.columns if c.endswith("_equiv02") or c.endswith("_equiv05")]
    if eq_cols:
        eq_rate = ok[eq_cols].mean().to_frame("fraction_calibrated")
        eq_rate.to_csv(os.path.join(output_dir, "equivalence_to_nominal.csv"))
        md.append("\n\n## Equivalence to nominal (practical calibration)\n")
        md.append("Fraction of cells whose block-bootstrap drift-coverage CI lies "
                  "entirely within [0.90±δ] — superiority over static is not the same "
                  "as being *practically calibrated*.\n\n")
        md.append(eq_rate.round(2).to_markdown())

    # RQ4/RQ6 — detectors / triggers, incl. coverage-failure lead-time (label-free
    # explanation signal vs residual-based Page-Hinkley which needs the realized y).
    t46 = _agg(ok, gcols, ["page_hinkley_FAR", "page_hinkley_lead",
                           "explanation_shift_FAR", "explanation_shift_lead"])
    t46.to_csv(os.path.join(output_dir, "rq46_detection.csv"))
    md.append("\n\n## RQ4/RQ6 Detection: label-free explanation trigger vs residual trigger\n")
    md.append("Lead = steps the trigger fires before static coverage visibly breaks "
              "(positive = early warning). Explanation signal is label-free.\n\n")
    md.append(t46.round(3).to_markdown())

    # RQ5 / RQ7.
    t57 = _agg(ok, gcols, ["rq5_cov_before_acc", "fidelity_ratio"])
    t57.to_csv(os.path.join(output_dir, "rq57_cov_before_acc_and_fidelity.csv"))
    md.append("\n\n## RQ5 coverage-before-accuracy (steps, >0 = coverage first) & "
              "RQ7 fidelity (>1 = faithful)\n")
    md.append(t57.round(2).to_markdown())

    # Cross-config model ranking on MAE. Friedman+Nemenyi needs >=3 models;
    # with exactly 2 backbones use the Wilcoxon signed-rank test instead.
    if ok["backbone"].nunique() > 1:
        idx = [c for c in ["dataset", "horizon", "onset_frac", "seed"] if c in ok.columns]
        piv = ok.pivot_table(index=idx, columns="backbone", values="MAE_main").dropna()
        if piv.shape[1] >= 3 and len(piv) >= 2:
            fn = friedman_nemenyi(piv.values)
            md.append("\n\n## Cross-config model ranking (Friedman+Nemenyi on MAE)\n")
            md.append(f"- Friedman p = {fn['friedman_p']:.4g}; Nemenyi CD = {fn['nemenyi_cd']:.3f}\n")
            md.append(f"- avg ranks ({list(piv.columns)}): "
                      f"{[round(r, 2) for r in fn['avg_ranks']]}\n")
        elif piv.shape[1] == 2 and len(piv) >= 3:
            from scipy.stats import wilcoxon
            a, b = piv.columns[0], piv.columns[1]
            try:
                stat, p = wilcoxon(piv[a].values, piv[b].values)
                better = a if piv[a].mean() < piv[b].mean() else b
                md.append("\n\n## Backbone comparison (Wilcoxon signed-rank on MAE)\n")
                md.append(f"- {a} mean MAE {piv[a].mean():.3g} vs {b} {piv[b].mean():.3g}; "
                          f"lower/better = **{better}**; p = {p:.4g} (n={len(piv)} configs)\n")
            except ValueError as e:
                md.append(f"\n\n## Backbone comparison\n- Wilcoxon not computable: {e}\n")

    _dump(output_dir, md, {})


def _dump(output_dir, md_parts, _):
    with open(os.path.join(output_dir, "SUMMARY.md"), "w") as f:
        f.write("".join(md_parts))
