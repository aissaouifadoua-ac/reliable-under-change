#!/usr/bin/env python3
"""Fig 7 — full online compute accounting: retrain (one full model fit) vs the online
monitoring+recalibration stack per 100 steps, broken into its components (attribution/
SHAP-or-IG, explanation-detector, Page-Hinkley, ACI update). This answers the reviewer's
point that the monitor (esp. IG) can dwarf the scalar conformal update, so the honest
comparison is C_monitor + C_ACI vs C_retrain — not C_ACI alone. Each backbone runs in
its OWN subprocess (torch + lightgbm co-loaded segfault on macOS).

Usage: python scripts/measure_efficiency.py
Writes figures/efficiency_seconds.csv and figures/fig7_efficiency.png.
"""
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / "figures" / "efficiency_seconds.csv"

# Per-step timing keys we report (×100 for a 100-step online budget).
KEYS = ["attribution_per_step_s", "explanation_detector_per_step_s",
        "page_hinkley_per_step_s", "recalibrate_per_step_s"]

CHILD = r"""
import sys; sys.path.insert(0, "src")
import warnings; warnings.filterwarnings("ignore")
from tef.experiment.runner import load_config, run
bk = sys.argv[1]
c = load_config("configs/opsd.yaml")
c["dataset"]["name"] = "uci"; c["dataset"]["loader_kwargs"] = {}
c["dataset"]["n"] = 8000
c["model"] = {"backbone": bk, "lookback": 64, "epochs": 8}
t = run(c)["timings"]
keys = ["train_%s_s" % bk, "attribution_per_step_s",
        "explanation_detector_per_step_s", "page_hinkley_per_step_s",
        "recalibrate_per_step_s"]
print(",".join("%.8f" % t.get(k, float("nan")) for k in keys))
"""


def measure(bk):
    env = {**os.environ, "KMP_DUPLICATE_LIB_OK": "TRUE", "OMP_NUM_THREADS": "4"}
    out = subprocess.run([sys.executable, "-c", CHILD, bk], cwd=ROOT, env=env,
                         capture_output=True, text=True)
    line = [l for l in out.stdout.strip().splitlines() if "," in l]
    if not line:
        print(f"  {bk}: FAILED\n{out.stderr[-300:]}"); return None
    retrain, attr, expd, ph, recal = map(float, line[-1].split(","))
    return {"backbone": bk, "retrain": retrain,
            "attribution100": attr * 100, "expdet100": expd * 100,
            "pagehinkley100": ph * 100, "recalibrate100": recal * 100}


def main():
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np, pandas as pd

    # Each backbone is timed REPEATS times in fresh processes and the median is kept: a
    # single cold-start run can be several times slower (seen for the ridge retrain).
    REPEATS = 3
    rows = [r for _ in range(REPEATS) for bk in ["ridge", "gbm", "patchtst"]
            if (r := measure(bk))]
    df = (pd.DataFrame(rows).fillna(0.0)          # ridge has no attributions
          .groupby("backbone", sort=False).median())
    df["monitor_stack100"] = (df["attribution100"] + df["expdet100"]
                              + df["pagehinkley100"] + df["recalibrate100"])
    df.to_csv(CSV)

    # Stacked bar: retrain vs the online monitoring+recalibration stack (per 100 steps).
    fig, ax = plt.subplots(figsize=(8, 4.4))
    x = np.arange(len(df)); w = 0.38
    ax.bar(x - w / 2, df["retrain"], w, label="retrain (one full fit)", color="#d1495b")
    comps = [("attribution100", "attribution (SHAP/IG)", "#2e7d32"),
             ("expdet100", "explanation detector", "#7fb069"),
             ("pagehinkley100", "Page-Hinkley", "#c9c9c9"),
             ("recalibrate100", "ACI update", "#3b6ea5")]
    bottom = np.zeros(len(df))
    for key, lbl, color in comps:
        ax.bar(x + w / 2, df[key], w, bottom=bottom, label=lbl, color=color)
        bottom += df[key].values
    ax.set_yscale("log"); ax.set_xticks(x); ax.set_xticklabels(df.index)
    ax.set_ylabel("seconds (log scale)")
    ax.set_title("Online monitor+recalibrate stack (100 steps) vs one retrain")
    ax.legend(fontsize=8, ncol=2)
    fig.tight_layout()
    fig.savefig(ROOT / "figures" / "fig7_efficiency.png", dpi=300)
    fig.savefig(ROOT / "figures" / "fig7_efficiency.pdf")   # vector copy for the journal
    ratio = (df["retrain"] / df["monitor_stack100"]).round(1).to_dict()
    print("\ncompute accounting (s):")
    print(df.round(5).to_string())
    print("\nretrain / (monitor+recal per 100 steps) ratio:", ratio)


if __name__ == "__main__":
    main()
