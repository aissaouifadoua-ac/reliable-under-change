#!/usr/bin/env python3
"""Generate the paper's figures from the saved grid results.

Reads results/opsd_grid_main/raw_cells.csv (+ scenario grid) and writes PNGs to
figures/. All figures aggregate mean±std over the onset×seed replicates. No display
needed (Agg backend). Run: python scripts/make_figures.py
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

FIG = "figures"
NOMINAL = 0.90
os.makedirs(FIG, exist_ok=True)

MAIN = "results/opsd_grid_main/raw_cells.csv"
SCEN = "results/opsd_grid_scenario/raw_cells.csv"



def _save(fig, png_path):
    """Write the figure twice: a 300-dpi PNG for previews and a vector PDF for the
    journal, which needs no resolution check."""
    fig.savefig(png_path + ".png", dpi=300)
    fig.savefig(png_path + ".pdf")

def _load(path):
    if not os.path.exists(path):
        sys.exit(f"missing {path} — run scripts/run_grid.py first")
    return pd.read_csv(path)


def fig_coverage(df):
    """Fig 1 (headline): static vs adaptive drift-coverage, GBM, with nominal line."""
    g = df[df.backbone == "gbm"].groupby(["dataset", "horizon"]).agg(
        s_mean=("static_drift_PICP", "mean"), s_std=("static_drift_PICP", "std"),
        a_mean=("adaptive_drift_PICP", "mean"), a_std=("adaptive_drift_PICP", "std"))
    labels = [f"{d}\nh{h}" for d, h in g.index]
    x = np.arange(len(labels)); w = 0.38
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.bar(x - w / 2, g.s_mean, w, yerr=g.s_std, capsize=3, label="static conformal",
           color="#d1495b")
    ax.bar(x + w / 2, g.a_mean, w, yerr=g.a_std, capsize=3, label="adaptive conformal",
           color="#2e7d32")
    ax.axhline(NOMINAL, ls="--", c="k", lw=1, label="nominal (0.90)")
    ax.set_xticks(x); ax.set_xticklabels(labels)
    ax.set_ylabel("drift-region coverage (PICP)"); ax.set_ylim(0, 1.02)
    ax.set_title("Static conformal miscalibrates under drift (load under-covers, "
                 "PV over-covers); adaptive holds nominal")
    ax.legend(loc="lower right", framealpha=0.95)
    fig.tight_layout(); _save(fig, f"{FIG}/fig1_coverage_static_vs_adaptive")
    plt.close(fig)


def fig_pareto(df):
    """Fig 2 (Pareto / decision rule): coverage error vs interval width (sharpness).
    Good = bottom-left (near-nominal coverage AND narrow). GBM cells.
    """
    d = df[df.backbone == "gbm"].copy()
    fig, ax = plt.subplots(figsize=(7.5, 5.5))
    for method, ce_col, w_col, color, mk in [
            ("static", "static_drift_PICP", "static_PINAW", "#d1495b", "o"),
            ("adaptive", "adaptive_drift_PICP", "adaptive_PINAW", "#2e7d32", "s")]:
        cov_err = (d[ce_col] - NOMINAL).abs()
        ax.scatter(d[w_col], cov_err, c=color, marker=mk, s=70, alpha=0.8,
                   edgecolor="k", linewidth=0.4, label=f"{method} conformal")
    ax.set_xlabel("interval width  PINAW  (→ less sharp)")
    ax.set_ylabel("coverage error |PICP − 0.90|  (→ less reliable)")
    ax.set_title("Reliability–sharpness trade-off (bottom-left = best)")
    ax.axhline(0.05, ls=":", c="grey", lw=1)
    ax.text(ax.get_xlim()[1] * 0.98, 0.052, "5% coverage-error band", ha="right",
            va="bottom", fontsize=8, color="grey")
    ax.legend(); fig.tight_layout()
    _save(fig, f"{FIG}/fig2_pareto_reliability_sharpness")
    plt.close(fig)


def fig_trigger(df):
    """Fig 3: false-alarm rate of error trigger vs explanation trigger (GBM)."""
    g = df[df.backbone == "gbm"].dropna(subset=["explanation_shift_FAR"]).groupby(
        "dataset").agg(ph=("page_hinkley_FAR", "mean"),
                       ex=("explanation_shift_FAR", "mean"))
    x = np.arange(len(g)); w = 0.38
    fig, ax = plt.subplots(figsize=(7, 4.2))
    ax.bar(x - w / 2, g.ph, w, label="Page-Hinkley (error trigger)", color="#d1495b")
    ax.bar(x + w / 2, g.ex, w, label="explanation-shift trigger", color="#2e7d32")
    ax.set_xticks(x); ax.set_xticklabels(g.index)
    ax.set_ylabel("false-alarm rate (lower = better)")
    ax.set_title("Recalibration trigger: false alarms by dataset")
    ax.legend(); fig.tight_layout()
    _save(fig, f"{FIG}/fig3_trigger_false_alarm"); plt.close(fig)


def fig_fidelity(df):
    """Fig 4: explanation fidelity ratio per GBM cell (line at 1 = no better than random)."""
    d = df[(df.backbone == "gbm")].dropna(subset=["fidelity_ratio"])
    g = d.groupby(["dataset", "horizon"]).fidelity_ratio.agg(["mean", "std"])
    labels = [f"{a}\nh{b}" for a, b in g.index]
    x = np.arange(len(labels))
    fig, ax = plt.subplots(figsize=(8, 4.2))
    ax.bar(x, g["mean"], yerr=g["std"], capsize=3, color="#3b6ea5")
    ax.axhline(1.0, ls="--", c="k", lw=1, label="= random removal")
    ax.set_xticks(x); ax.set_xticklabels(labels)
    ax.set_ylabel("fidelity ratio (top-k vs random removal)")
    ax.set_title("Mean faithfulness ratio is above 1 in every configuration")
    ax.legend(); fig.tight_layout()
    _save(fig, f"{FIG}/fig4_explanation_fidelity"); plt.close(fig)


def fig_scenarios(df):
    """Fig 5: robustness across scenarios — static vs adaptive coverage."""
    order = ["normal", "missing", "noise", "injected_drift"]
    g = df.groupby(["dataset", "scenario"]).agg(
        s=("static_drift_PICP", "mean"), a=("adaptive_drift_PICP", "mean"))
    fig, axes = plt.subplots(1, g.index.get_level_values(0).nunique(),
                             figsize=(10, 4), sharey=True)
    for ax, ds in zip(np.atleast_1d(axes), sorted(set(g.index.get_level_values(0)))):
        sub = g.loc[ds].reindex(order)
        x = np.arange(len(order)); w = 0.38
        ax.bar(x - w / 2, sub.s, w, label="static", color="#d1495b")
        ax.bar(x + w / 2, sub.a, w, label="adaptive", color="#2e7d32")
        ax.axhline(NOMINAL, ls="--", c="k", lw=1)
        ax.set_xticks(x); ax.set_xticklabels(["normal", "missing", "noise", "drift"],
                                             rotation=20)
        ax.set_title(ds); ax.set_ylim(0, 1.02)
    np.atleast_1d(axes)[0].set_ylabel("drift-region PICP")
    np.atleast_1d(axes)[0].legend(loc="lower left", fontsize=8)
    fig.suptitle("Adaptive conformal holds coverage across perturbations")
    fig.tight_layout(); _save(fig, f"{FIG}/fig5_scenario_robustness")
    plt.close(fig)


def fig_reliability_timeline():
    """Fig 6: rolling coverage over the test window, static vs adaptive, with the
    drift-onset marker. Runs one representative cell live to get per-step intervals."""
    sys.path.insert(0, "src")
    from tef.experiment.runner import load_config, run
    cfg = load_config("configs/opsd.yaml")
    cfg["dataset"]["name"] = "uci"; cfg["dataset"]["loader_kwargs"] = {}
    cfg["dataset"].pop("n", None); cfg["model"]["backbone"] = "gbm"
    cfg["scenario"]["injected"]["start_frac"] = 0.5
    cfg["return_diagnostics"] = True
    d = run(cfg)["diagnostics"]
    y = np.asarray(d["y_test"]); onset = d["onset_in_test"]
    w = max(len(y) // 20, 50)

    def roll_cov(lo, hi):
        c = ((y >= np.asarray(lo)) & (y <= np.asarray(hi))).astype(float)
        return pd.Series(c).rolling(w, min_periods=w // 2).mean().values

    fig, ax = plt.subplots(figsize=(10, 4.3))
    ax.plot(roll_cov(d["lo_static"], d["hi_static"]), color="#d1495b", label="static conformal")
    ax.plot(roll_cov(d["lo_adaptive"], d["hi_adaptive"]), color="#2e7d32", label="adaptive conformal")
    ax.axhline(NOMINAL, ls="--", c="k", lw=1, label="nominal (0.90)")
    ax.axvline(onset, ls=":", c="purple", lw=1.5, label="drift onset")
    ax.set_xlabel(f"test-set step (rolling {w}-step coverage)")
    ax.set_ylabel("empirical coverage"); ax.set_ylim(0, 1.02)
    ax.set_title("Coverage over time: static drops at drift onset, adaptive recovers (UCI, h1)")
    ax.legend(loc="lower left", ncol=2, fontsize=8)
    fig.tight_layout(); _save(fig, f"{FIG}/fig6_reliability_timeline")
    plt.close(fig)


def main():
    main_df = _load(MAIN)
    fig_coverage(main_df)
    fig_pareto(main_df)
    fig_trigger(main_df)
    fig_fidelity(main_df)
    if os.path.exists(SCEN):
        fig_scenarios(_load(SCEN))
    fig_reliability_timeline()
    # Fig 7 (efficiency) is generated by scripts/measure_efficiency.py, which runs
    # each backbone in its own process (torch + lightgbm co-load segfaults on macOS).
    print("Wrote figures to", FIG + "/:")
    for f in sorted(os.listdir(FIG)):
        print("  ", f)


if __name__ == "__main__":
    main()
