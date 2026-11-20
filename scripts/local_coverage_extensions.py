#!/usr/bin/env python3
"""Local-coverage extensions: a strongly adaptive conformal rung and a
dependence-aware null for the worst rolling window.

Two questions the main grid leaves open, answered on the 16 gradient-boosting
load-dataset cells (OPSD and UCI x horizons 1 and 24 x 2 onsets x 2 seeds):

1. Does a strongly adaptive online conformal method (SAOCP, Bhatnagar et al. 2023),
   which targets coverage on every sub-interval, repair the local under-coverage that
   the long-run-regulating rungs (ACI, AgACI) leave behind?
2. Is that local under-coverage still anomalous once the null respects the serial
   dependence of the coverage indicators? The original null is an i.i.d.
   Bernoulli(0.90) sequence. Here the null is a moving-block bootstrap of each
   method's own PRE-ONSET coverage indicators (a stable period by construction),
   resampled to the test length, so it carries the real autocorrelation.

Writes results/local_extensions/{cells.csv,SUMMARY.md} and
figures/fig14_local_coverage_null.png.
Run: python scripts/local_coverage_extensions.py   (add --tables-only to rebuild the\ntables and figure from a saved cells.csv without rerunning the cells)
"""
import copy
import itertools
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from tef.experiment.runner import run, load_config  # noqa: E402
from tef.experiment.sweep import DATASET_KWARGS  # noqa: E402
from tef.metrics.interval import interval_metrics, picp  # noqa: E402
from tef.uq.conformal import StronglyAdaptiveConformal  # noqa: E402

OUT = "results/local_extensions"
FIG = "figures"
NOMINAL = 0.90
WINDOW = 168
N_BOOT = 1000
BLOCKS = (24, 168)          # one day and one week
METHODS = ["static", "windowed", "adaptive", "agaci", "saocp"]
LABEL = {"static": "Static", "windowed": "Windowed", "adaptive": "ACI",
         "agaci": "AgACI", "saocp": "SAOCP"}



def _save(fig, png_path):
    """Write the figure twice: a 300-dpi PNG for previews and a vector PDF for the
    journal, which needs no resolution check."""
    fig.savefig(png_path + ".png", dpi=300)
    fig.savefig(png_path + ".pdf")

def rolling_mean(flag, w=WINDOW):
    c = np.concatenate([[0.0], np.cumsum(flag)])
    return (c[w:] - c[:-w]) / w


def local_stats(flag):
    r = rolling_mean(flag)
    return {"worst": float(r.min()), "p05": float(np.percentile(r, 5)),
            "below085": float(np.mean(r < 0.85)), "argworst": int(r.argmin()) + WINDOW - 1}


def iid_null(n, rng):
    return np.array([rolling_mean(rng.binomial(1, NOMINAL, n).astype(float)).min()
                     for _ in range(N_BOOT)])


def block_null(pre_flag, n, block, rng):
    """Worst rolling-window coverage of moving-block resamples of the pre-onset
    coverage indicators, each resample as long as the test window."""
    m = len(pre_flag)
    block = min(block, m)
    n_blocks = int(np.ceil(n / block))
    mins = np.empty(N_BOOT)
    for b in range(N_BOOT):
        starts = rng.integers(0, m - block + 1, size=n_blocks)
        series = np.concatenate([pre_flag[s:s + block] for s in starts])[:n]
        mins[b] = rolling_mean(series).min()
    return mins


def one_cell(base, dataset, horizon, onset, seed):
    cfg = copy.deepcopy(base)
    cfg["seed"] = seed
    cfg["dataset"].update(name=dataset, horizon=horizon,
                          loader_kwargs=DATASET_KWARGS.get(dataset, {}))
    cfg["dataset"].pop("n", None)
    cfg["model"]["backbone"] = "gbm"
    cfg["scenario"]["kind"] = "injected_drift"
    cfg["scenario"]["injected"]["start_frac"] = onset
    cfg["return_diagnostics"] = True
    d = run(cfg)["diagnostics"]
    y, yhat, on = np.asarray(d["y_test"]), np.asarray(d["yhat"]), d["onset_in_test"]

    lo_sa, hi_sa = (StronglyAdaptiveConformal(NOMINAL)
                    .seed_residuals(d["y_cal"], d["yhat_cal"]).run(yhat, y, lag=d["lag"]))
    bands = {m: (np.asarray(d[f"lo_{m}"]), np.asarray(d[f"hi_{m}"]))
             for m in METHODS if m != "saocp"}
    bands["saocp"] = (lo_sa, hi_sa)

    rng = np.random.default_rng(seed)
    row = {"dataset": dataset, "horizon": horizon, "onset": onset, "seed": seed,
           "n_test": len(y), "onset_in_test": on,
           "worst_window_end_adaptive": None}
    iid = iid_null(len(y), rng)
    row["null_iid_p05"] = float(np.percentile(iid, 5))
    for m, (lo, hi) in bands.items():
        flag = ((y >= lo) & (y <= hi)).astype(float)
        im = interval_metrics(y, lo, hi, NOMINAL)
        ls = local_stats(flag)
        if m == "adaptive":   # calendar date of the worst ACI window, for interpretation
            row["worst_window_end_adaptive"] = d["index"][ls["argworst"]]
        row.update({f"{m}_drift_PICP": picp(y[on:], lo[on:], hi[on:]),
                    f"{m}_pre_PICP": float(flag[:on].mean()),
                    f"{m}_PINAW": im["PINAW"], f"{m}_IS": im.get("IntervalScore"),
                    f"{m}_worst": ls["worst"], f"{m}_p05": ls["p05"],
                    f"{m}_below085": ls["below085"],
                    f"{m}_worst_after_onset": bool(ls["argworst"] >= on),
                    f"{m}_worst_lag_from_onset": ls["argworst"] - on})
        if m == "static":
            continue
        # Lag-1 autocorrelation of the pre-onset coverage indicators (the dependence
        # the i.i.d. null ignores).
        pre = flag[:on]
        row[f"{m}_pre_acf1"] = float(np.corrcoef(pre[:-1], pre[1:])[0, 1])
        for b in BLOCKS:
            mins = block_null(pre, len(y), b, rng)
            row[f"{m}_null_b{b}_p05"] = float(np.percentile(mins, 5))
            row[f"{m}_null_b{b}_median"] = float(np.median(mins))
            # One-sided bootstrap p-value: how often a stable period of this length
            # produces a worst window at least as bad as the observed one.
            row[f"{m}_p_b{b}"] = float((1 + np.sum(mins <= ls["worst"])) / (N_BOOT + 1))
    return row


def main():
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(FIG, exist_ok=True)
    if "--tables-only" in sys.argv:      # rebuild tables and figure from saved cells
        df = pd.read_csv(f"{OUT}/cells.csv")
    else:
        base = load_config("configs/opsd.yaml")
        rows = []
        for ds, h, on, seed in itertools.product(["opsd", "uci"], [1, 24], [0.4, 0.6],
                                                 [7, 13]):
            print(f"[cell] {ds} h={h} onset={on} seed={seed}", flush=True)
            rows.append(one_cell(base, ds, h, on, seed))
        df = pd.DataFrame(rows)
        df.to_csv(f"{OUT}/cells.csv", index=False)

    g = df.groupby(["dataset", "horizon"])
    md = ["# Local-coverage extensions (auto-generated)\n",
          f"\n16 gradient-boosting load cells; window {WINDOW} h; nominal {NOMINAL}; "
          f"{N_BOOT} null resamples. Values are mean (s.d.) over onset x seed.\n"]

    def tab(title, cols):
        t = g[cols].agg(["mean", "std"]).round(3)
        md.append(f"\n## {title}\n\n" + t.to_markdown() + "\n")

    tab("Drift-region coverage", [f"{m}_drift_PICP" for m in METHODS])
    tab("Worst 168-h window", [f"{m}_worst" for m in METHODS])
    tab("5th-percentile window", [f"{m}_p05" for m in METHODS])
    tab("Fraction of windows below 0.85", [f"{m}_below085" for m in METHODS])
    tab("Normalised width (PINAW)", [f"{m}_PINAW" for m in METHODS])
    tab("Interval score", [f"{m}_IS" for m in METHODS])
    adaptive = [m for m in METHODS if m != "static"]
    tab("Null 5th percentile of the worst window: i.i.d. vs block bootstrap",
        ["null_iid_p05"] + [f"{m}_null_b{b}_p05" for m in adaptive for b in BLOCKS])
    tab("Bootstrap p-value of the observed worst window",
        [f"{m}_p_b{b}" for m in adaptive for b in BLOCKS])
    tab("Pre-onset coverage and lag-1 autocorrelation of the indicators",
        [f"{m}_pre_PICP" for m in adaptive] + [f"{m}_pre_acf1" for m in adaptive])
    tab("Worst window located after onset (fraction of cells)",
        [f"{m}_worst_after_onset" for m in adaptive])
    with open(f"{OUT}/SUMMARY.md", "w") as f:
        f.write("".join(md))

    # Figure: observed worst window per method against the two null bands.
    fig, axes = plt.subplots(1, 4, figsize=(12.5, 3.6), sharey=True)
    colors = {"windowed": "#8d6e63", "adaptive": "#2e7d32", "agaci": "#1565c0",
              "saocp": "#6a1b9a"}
    for ax, ((ds, h), sub) in zip(axes, g):
        for k, m in enumerate(adaptive):
            ax.errorbar(k - 0.12, sub[f"{m}_worst"].mean(), yerr=sub[f"{m}_worst"].std(),
                        fmt="o", color=colors[m], capsize=3, label="observed worst window"
                        if (k == 0) else None)
            ax.errorbar(k + 0.12, sub[f"{m}_null_b168_p05"].mean(),
                        yerr=sub[f"{m}_null_b168_p05"].std(), fmt="s", mfc="white",
                        color=colors[m], capsize=3,
                        label="dependence-aware null, 5th pct." if (k == 0) else None)
        ax.axhline(sub["null_iid_p05"].mean(), color="0.35", ls=":", lw=1.2,
                   label="i.i.d. null, 5th pct.")
        ax.axhline(NOMINAL, color="0.6", ls="--", lw=0.8)
        ax.set_xticks(range(len(adaptive)))
        ax.set_xticklabels([LABEL[m] for m in adaptive], fontsize=9)
        ax.set_title(f"{ds.upper()}, h={h}", fontsize=10)
    axes[0].set_ylabel("worst 168-h window coverage")
    axes[0].legend(frameon=False, fontsize=8, loc="lower left")
    fig.tight_layout()
    _save(fig, f"{FIG}/fig14_local_coverage_null")
    plt.close(fig)
    print("".join(md))


if __name__ == "__main__":
    main()
