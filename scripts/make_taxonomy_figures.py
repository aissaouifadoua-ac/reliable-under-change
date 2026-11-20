#!/usr/bin/env python3
"""Drift-taxonomy figures (reviewer #2): drift as a first-class variable.

Reads results/drift_taxonomy/raw_cells.csv and writes:
  fig8  severity (magnitude) -> static coverage deficit, conditional vs covariate
  fig9  speed (transition_frac) -> static coverage deficit, by severity

Style matches scripts/make_figures.py (same palette). Run:
  PYTHONPATH=src python scripts/make_taxonomy_figures.py
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

FIG = "figures"
os.makedirs(FIG, exist_ok=True)
SRC = "results/drift_taxonomy/raw_cells.csv"
COND, COV = "#d1495b", "#2e7d32"   # conditional (concept) red, covariate green



def _save(fig, png_path):
    """Write the figure twice: a 300-dpi PNG for previews and a vector PDF for the
    journal, which needs no resolution check."""
    fig.savefig(png_path + ".png", dpi=300)
    fig.savefig(png_path + ".pdf")

def _load():
    if not os.path.exists(SRC):
        sys.exit(f"missing {SRC} — run the drift_taxonomy grid first")
    df = pd.read_csv(SRC)
    return df[df.get("error").isna()] if "error" in df.columns else df


def fig_severity(df):
    """Fig 8: severity -> coverage deficit, abrupt drift, conditional vs covariate."""
    sub = df[df.transition_frac == 0.0]
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for dtype, color, marker in [("conditional", COND, "o"), ("covariate", COV, "s")]:
        g = (sub[sub.drift_type == dtype]
             .groupby("magnitude")["static_coverage_deficit"].agg(["mean", "std"]))
        ax.errorbar(g.index, g["mean"], yerr=g["std"], marker=marker, capsize=3,
                    color=color, label=f"{dtype}  (P(Y|X)" +
                    (" change)" if dtype == "conditional" else " fixed, P(X) change)"))
    ax.axhline(0.0, color="0.6", lw=0.8, ls=":")
    ax.set_xlabel("drift magnitude (severity)")
    ax.set_ylabel("static coverage deficit  (nominal − drift PICP)")
    ax.set_title("Concept shift breaks calibration; covariate shift barely does")
    ax.legend(frameon=False)
    fig.tight_layout(); _save(fig, f"{FIG}/fig8_severity_deficit")
    plt.close(fig)


def fig_speed(df):
    """Fig 9: drift speed -> static coverage deficit (conditional), by severity;
    adaptive shown as a speed-invariant reference at nominal."""
    sub = df[df.drift_type == "conditional"]
    fig, ax = plt.subplots(figsize=(7, 4.5))
    mags = [1.5, 2.0, 3.0]
    shades = ["#e39aa6", "#d1495b", "#8f2233"]  # light->dark red by severity
    for m, c in zip(mags, shades):
        g = (sub[sub.magnitude == m]
             .groupby("transition_frac")["static_coverage_deficit"].agg(["mean", "std"]))
        ax.errorbar(g.index, g["mean"], yerr=g["std"], marker="o", capsize=3,
                    color=c, label=f"static, m={m}")
    # Adaptive: flat near zero deficit regardless of speed.
    ga = (sub[sub.magnitude == 2.0].assign(
        adef=lambda d: 0.90 - d["adaptive_drift_PICP"])
        .groupby("transition_frac")["adef"].mean())
    ax.plot(ga.index, ga.values, marker="s", color=COV, lw=2,
            label="adaptive (ACI), m=2")
    ax.axhline(0.0, color="0.6", lw=0.8, ls=":")
    ax.set_xlabel("drift speed  (transition width as fraction of test window; 0 = abrupt)")
    ax.set_ylabel("static coverage deficit  (nominal − drift PICP)")
    ax.set_title("Gradual drift is less damaging; adaptive is speed-invariant")
    ax.legend(frameon=False, ncol=2, fontsize=9)
    fig.tight_layout(); _save(fig, f"{FIG}/fig9_speed_deficit")
    plt.close(fig)


def fig_leadtime():
    """Fig 10: coverage-failure lead-time vs false-alarm rate, per (dataset,horizon).
    The label-free explanation trigger warns early at low FAR; Page-Hinkley's apparent
    lead on grid load is an artefact of near-continuous firing (FAR ~ 1)."""
    fam = "results/family_grid_lag/raw_cells.csv"
    if not os.path.exists(fam):
        print(f"skip fig10 — missing {fam}")
        return
    df = pd.read_csv(fam)
    df = df[df["error"].isna()] if "error" in df.columns else df
    g = df.groupby(["dataset", "horizon"]).mean(numeric_only=True)
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    for det, color, lbl in [("page_hinkley", COND, "Page-Hinkley (needs $y_t$)"),
                            ("explanation_shift", COV, "explanation shift (label-free)")]:
        ax.scatter(g[f"{det}_FAR"], g[f"{det}_lead"], s=90, color=color,
                   edgecolor="k", lw=0.5, label=lbl, zorder=3)
        for (d, h), r in g.iterrows():
            ax.annotate(f"{d} h{h}", (r[f"{det}_FAR"], r[f"{det}_lead"]),
                        fontsize=7, xytext=(4, 3), textcoords="offset points")
    ax.axhline(0, color="0.6", lw=0.8, ls=":")
    ax.set_xlabel("false-alarm rate  (→ chatty, unusable as a trigger)")
    ax.set_ylabel("coverage-failure lead-time  (steps; >0 = early warning)")
    ax.set_title("Label-free explanation trigger warns early at low false-alarm rate")
    ax.legend(frameon=False, loc="upper center")
    fig.tight_layout(); _save(fig, f"{FIG}/fig10_leadtime_far")
    plt.close(fig)


def main():
    df = _load()
    fig_severity(df)
    fig_speed(df)
    fig_leadtime()
    print("wrote figures/fig8_severity_deficit.png, figures/fig9_speed_deficit.png, "
          "figures/fig10_leadtime_far.png")


if __name__ == "__main__":
    main()
