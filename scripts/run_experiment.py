#!/usr/bin/env python3
"""Run one experiment cell from a YAML config and print a compact summary.

Usage: python scripts/run_experiment.py configs/demo.yaml
"""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tef.experiment.runner import run_from_file  # noqa: E402


def main():
    cfg_path = sys.argv[1] if len(sys.argv) > 1 else "configs/demo.yaml"
    res = run_from_file(cfg_path)
    print("=" * 68)
    print("Backbone used:", res["backbone_used"], "| n_test:", res["n_test"])
    print("-" * 68)
    print("RQ1  Point (MAE):")
    for k, v in res["point_metrics"].items():
        print(f"   {k:16s} MAE={v['MAE']:.3f}  RMSE={v['RMSE']:.3f}")
    print("-" * 68)
    print("RQ2/RQ3  Coverage (nominal = target):")
    for k, v in res["uq"].items():
        print(f"   {k:20s} overall PICP={v['overall']['PICP']:.3f} "
              f"PINAW={v['overall']['PINAW']:.3f} | stable={v['stable_PICP']} "
              f"drift={v['drift_PICP']:.3f}")
    print("-" * 68)
    print(f"RQ5  coverage-before-accuracy (steps, >0 => coverage fails first): "
          f"{res['rq5_coverage_before_accuracy_steps']}")
    print(f"     detail: {res['rq5_detail']}")
    print("-" * 68)
    gt = res["drift_eval"].get("has_ground_truth", True)
    print(f"RQ4/RQ6  Drift detection (delay / false-alarm / #alarms) "
          f"[ground-truth onset: {gt}]:")
    for k, v in res["drift_eval"].items():
        if isinstance(v, dict) and "delay" in v:
            far = "n/a" if v["false_alarm_rate"] is None else f"{v['false_alarm_rate']:.3f}"
            print(f"   {k:20s} delay={v['delay']} FAR={far} n={v['n_alarms']}")
    print("   onset_in_test:", res["drift_eval"]["onset_in_test"])
    print("-" * 68)
    if res["xai_fidelity"]:
        f = res["xai_fidelity"]
        print(f"RQ7  Explanation fidelity ratio (>1 => faithful): "
              f"{f['fidelity_ratio']:.2f}  "
              f"(top-k ΔMAE {f['topk_mae']-f['base_mae']:.3f} vs "
              f"random {f['random_mae']-f['base_mae']:.3f})")
    print("=" * 68)
    print("Full JSON written under results/. Keys:", list(res.keys()))


if __name__ == "__main__":
    main()
