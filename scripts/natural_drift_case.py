#!/usr/bin/env python3
"""Natural-drift case study (reviewer #4): a real regime change, no injection.

OPSD German load, 2015-2020. Train/calibration fall in 2015-2019; the last-20% test
window spans 2019-08 -> 2020-09, so it contains the COVID-19 spring-2020 demand
collapse the model never saw. We run the plain `normal` scenario (NO injected drift)
and show static conformal coverage degrades in the natural regime shift while adaptive
conformal holds nominal. This converts the headline from a simulation into a real
event.

Writes figures/fig11_natural_drift_covid.png and prints the monthly coverage table.
Run: PYTHONPATH=src python scripts/natural_drift_case.py
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from tef.experiment.runner import run, load_config

FIG = "figures"
NOMINAL = 0.90
STATIC, ADAPT = "#d1495b", "#2e7d32"
os.makedirs(FIG, exist_ok=True)



def _save(fig, png_path):
    """Write the figure twice: a 300-dpi PNG for previews and a vector PDF for the
    journal, which needs no resolution check."""
    fig.savefig(png_path + ".png", dpi=300)
    fig.savefig(png_path + ".pdf")

def _cov(y, lo, hi):
    return ((y >= np.asarray(lo)) & (y <= np.asarray(hi))).astype(float)


def main():
    cfg = load_config("configs/opsd.yaml")
    cfg["scenario"]["kind"] = "normal"       # <-- no injected drift
    cfg["dataset"].pop("n", None)
    cfg["return_diagnostics"] = True
    res = run(cfg)
    d = res["diagnostics"]
    idx = pd.to_datetime(d["index"])
    y = np.asarray(d["y_test"])

    df = pd.DataFrame({
        "date": idx,
        "static": _cov(y, d["lo_static"], d["hi_static"]),
        "adaptive": _cov(y, d["lo_adaptive"], d["hi_adaptive"]),
        "w_static": np.asarray(d["hi_static"]) - np.asarray(d["lo_static"]),
        "w_adaptive": np.asarray(d["hi_adaptive"]) - np.asarray(d["lo_adaptive"]),
    })
    df["ym"] = df["date"].dt.to_period("M").dt.to_timestamp()
    m = df.groupby("ym").agg(static=("static", "mean"), adaptive=("adaptive", "mean"),
                             w_static=("w_static", "mean"),
                             w_adaptive=("w_adaptive", "mean"))

    print("Overall PICP  static=%.3f  adaptive=%.3f"
          % (res["uq"]["static_conformal"]["overall"]["PICP"],
             res["uq"]["adaptive_conformal"]["overall"]["PICP"]))
    print("\nMonthly coverage (no injection):")
    print(m[["static", "adaptive"]].round(3).to_string())
    covid = m.loc["2020-03":"2020-05"]
    print("\nCOVID lockdown (Mar-May 2020) mean coverage: "
          "static=%.3f  adaptive=%.3f" % (covid.static.mean(), covid.adaptive.mean()))
    print("Adaptive width vs static over COVID: %.2fx"
          % (covid.w_adaptive.mean() / covid.w_static.mean()))

    # Figure: monthly coverage, static vs adaptive, COVID band highlighted.
    fig, ax = plt.subplots(figsize=(10, 4.6))
    ax.axvspan(pd.Timestamp("2020-03-01"), pd.Timestamp("2020-05-31"),
               color="#cccccc", alpha=0.5, label="COVID-19 lockdown")
    ax.plot(m.index, m.static, marker="o", color=STATIC, label="static conformal")
    ax.plot(m.index, m.adaptive, marker="s", color=ADAPT, label="adaptive conformal")
    ax.axhline(NOMINAL, color="0.4", lw=0.9, ls="--", label="nominal 0.90")
    ax.set_ylabel("monthly PICP (empirical coverage)")
    ax.set_xlabel("month of test window (OPSD German load, no injected drift)")
    ax.set_title("Natural regime change: static coverage collapses in the COVID "
                 "demand shift; adaptive holds")
    ax.set_ylim(0.6, 1.0)
    ax.legend(frameon=False, ncol=2, fontsize=9)
    fig.autofmt_xdate()
    fig.tight_layout()
    _save(fig, f"{FIG}/fig11_natural_drift_covid")
    plt.close(fig)
    print("\nwrote figures/fig11_natural_drift_covid.png")


if __name__ == "__main__":
    main()
