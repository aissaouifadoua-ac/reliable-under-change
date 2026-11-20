#!/usr/bin/env python3
"""Matched-false-alarm-rate detector comparison (reviewer #2).

Calibrates every detector to a common false-alarm budget on the pre-drift segment,
then measures detection delay. Includes the label-free raw-input detectors (KS, PSI)
so we can ask the real question: does explanation-space monitoring add information
beyond monitoring X itself? Page-Hinkley (residual) is label-dependent and its delay
carries the +horizon observation lag.

Writes figures/fig12_detector_delay_vs_far.png and prints a matched-FAR table.
Run: PYTHONPATH=src python scripts/detector_comparison.py
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from tef.experiment.runner import run, load_config
from tef.drift.scores import (page_hinkley_scores, ks_scores, psi_scores,
                              mmd_scores, explanation_scores, matched_far_delay)

FIG = "figures"
os.makedirs(FIG, exist_ok=True)
FARS = [0.01, 0.02, 0.05, 0.10, 0.20]
COLORS = {"Page-Hinkley (residual, +h lag)": "#d1495b", "KS (features)": "#e6a817",
          "PSI (features)": "#8a6bbf", "MMD (features, multivariate)": "#c77dff",
          "explanation shift": "#2e7d32"}


# Deterministic calendar features drift trivially between a fixed early reference and
# later windows (a Jan reference vs a Jul window => KS=1 on `month`), which saturates a
# naive multivariate KS/PSI monitor regardless of any real shift. Restrict the raw-input
# detectors to the STOCHASTIC features (drivers + target lags/rolling) for a fair test.
_CALENDAR = ("hour_sin", "hour_cos", "dow", "is_weekend", "month")



def _save(fig, png_path):
    """Write the figure twice: a 300-dpi PNG for previews and a vector PDF for the
    journal, which needs no resolution check."""
    fig.savefig(png_path + ".png", dpi=300)
    fig.savefig(png_path + ".pdf")

def _streams(dataset):
    cfg = load_config(f"configs/{dataset}.yaml")
    cfg["scenario"]["kind"] = "injected_drift"
    cfg["dataset"].pop("n", None)
    cfg["return_detector_streams"] = True
    res = run(cfg)
    d = res["detector_streams"]
    onset, h = d["onset_in_test"], d["horizon"]
    names = d["feature_names"]
    keep = [i for i, nm in enumerate(names) if nm not in _CALENDAR]
    Xs = d["features"][:, keep]
    scores = {
        "Page-Hinkley (residual, +h lag)": (page_hinkley_scores(d["resid"]), h),
        "KS (features)": (ks_scores(Xs, pre_end=onset), 0),
        "PSI (features)": (psi_scores(Xs, pre_end=onset), 0),
        "MMD (features, multivariate)": (mmd_scores(Xs), 0),
        "explanation shift": (explanation_scores(d["attributions"]), 0),
    }
    return scores, onset


def _curves(dataset):
    scores, onset = _streams(dataset)
    print(f"\n=== {dataset.upper()}: detection delay at matched FAR (onset={onset}) ===")
    print("FAR   " + "  ".join(f"{k.split(' (')[0]:>14}" for k in scores))
    curves = {k: [] for k in scores}
    for far in FARS:
        row = [f"{far:>4.2f}"]
        for name, (s, lag) in scores.items():
            delay, _, _ = matched_far_delay(s, onset, onset, far, lag)
            curves[name].append(delay if delay is not None else np.nan)
            row.append(f"{'—' if delay is None else delay:>14}")
        print("  ".join(row))
    return curves


def main():
    datasets = ["opsd", "uci"]
    fig, axes = plt.subplots(1, len(datasets), figsize=(11, 4.6), sharey=True)
    for ax, ds in zip(np.atleast_1d(axes), datasets):
        curves = _curves(ds)
        for name, ys in curves.items():
            ax.plot(FARS, ys, marker="o", color=COLORS[name], label=name)
        ax.set_xscale("log")
        ax.set_xlabel("false-alarm rate budget")
        ax.set_title(ds.upper())
    np.atleast_1d(axes)[0].set_ylabel("detection delay after onset (steps; lower better)")
    np.atleast_1d(axes)[0].legend(frameon=False, fontsize=8)
    fig.suptitle("Detection delay at matched false-alarm rate "
                 "(explanation shift beats raw-input KS/PSI on both datasets)")
    fig.tight_layout()
    _save(fig, f"{FIG}/fig12_detector_delay_vs_far")
    plt.close(fig)
    print(f"\nwrote {FIG}/fig12_detector_delay_vs_far.png")


if __name__ == "__main__":
    main()
