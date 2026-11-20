#!/usr/bin/env python3
"""Daylight-conditioned PV coverage (reviewer #4).

A global 90% interval on PV can look calibrated because ~40% of observations are
night/near-zero generation and almost trivially predictable. We therefore condition
coverage on the generation regime — all hours vs daylight (output above 5% of capacity)
vs night — for each conformal method on the UNISOLAR PV target.

Writes figures/fig13_pv_daylight_coverage.png and prints the regime table.
Run: PYTHONPATH=src python scripts/pv_daylight_coverage.py
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from tef.experiment.runner import run, load_config

FIG = "figures"
NOMINAL = 0.90
os.makedirs(FIG, exist_ok=True)
METHODS = [("static", "static conformal", "#d1495b"),
           ("adaptive", "adaptive conformal", "#2e7d32")]



def _save(fig, png_path):
    """Write the figure twice: a 300-dpi PNG for previews and a vector PDF for the
    journal, which needs no resolution check."""
    fig.savefig(png_path + ".png", dpi=300)
    fig.savefig(png_path + ".pdf")

def _picp(y, lo, hi, mask):
    lo, hi = np.asarray(lo), np.asarray(hi)
    c = (y >= lo) & (y <= hi)
    return float(c[mask].mean()) if mask.any() else float("nan")


def main():
    cfg = load_config("configs/unisolar.yaml")
    cfg["scenario"]["kind"] = "injected_drift"
    cfg["dataset"].pop("n", None)
    cfg["return_diagnostics"] = True
    res = run(cfg)
    d = res["diagnostics"]
    y = np.asarray(d["y_test"])
    thr = 0.05 * y.max()
    day = y > thr                      # daylight = generation above 5% of capacity
    regimes = {"all hours": np.ones_like(y, bool), "daylight": day, "night": ~day}

    print("PV coverage by solar regime (UNISOLAR, injected drift; nominal 0.90):")
    print(f"  daylight fraction = {day.mean():.2f}\n")
    header = "method      " + "  ".join(f"{r:>10}" for r in regimes)
    print(header)
    data = {}
    for key, label, _ in METHODS:
        lo, hi = d[f"lo_{key}"], d[f"hi_{key}"]
        vals = {r: _picp(y, lo, hi, m) for r, m in regimes.items()}
        data[key] = vals
        print(f"{label:<12}" + "  ".join(f"{vals[r]:>10.3f}" for r in regimes))

    # Grouped bar chart: regimes on x, static vs adaptive bars, nominal line.
    labels = list(regimes)
    x = np.arange(len(labels))
    w = 0.38
    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    for i, (key, label, color) in enumerate(METHODS):
        ax.bar(x + (i - 0.5) * w, [data[key][r] for r in labels], w,
               label=label, color=color)
    ax.axhline(NOMINAL, color="0.35", ls="--", lw=1, label="nominal 0.90")
    ax.set_xticks(x); ax.set_xticklabels(labels)
    ax.set_ylabel("PICP (empirical coverage)")
    ax.set_ylim(0.7, 1.0)
    ax.set_title("PV: global coverage hides daylight under-coverage")
    ax.legend(frameon=False, ncol=3, fontsize=9)
    fig.tight_layout()
    _save(fig, f"{FIG}/fig13_pv_daylight_coverage")
    plt.close(fig)
    print(f"\nwrote {FIG}/fig13_pv_daylight_coverage.png")


if __name__ == "__main__":
    main()
