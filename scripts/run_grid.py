#!/usr/bin/env python3
"""Run one experimental grid and write its tables.

Usage:
    python scripts/run_grid.py --grid=NAME [base_config] [--quick]

NAME is one of: main, scenario, rolling, taxonomy, family, patchtst (see
src/tef/experiment/sweep.py for each grid's cells). base_config defaults to
configs/opsd.yaml and supplies only the non-grid settings (features, split, uq, drift,
stats); the grid overrides dataset, horizon, backbone, scenario, onset and seed.
Each grid writes results/<dir>/raw_cells.csv and SUMMARY.md; --quick runs a 2-cell
smoke test instead.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tef.experiment.runner import load_config       # noqa: E402
from tef.experiment.sweep import (run_grid, default_grid, scenario_grid,  # noqa: E402
                                  rolling_grid, drift_taxonomy_grid, family_grid,
                                  patchtst_grid)

GRIDS = {
    # name: (grid factory, output directory read by the figure scripts)
    "main": (default_grid, "results/opsd_grid_main"),
    "scenario": (scenario_grid, "results/opsd_grid_scenario"),
    "rolling": (rolling_grid, "results/opsd_grid_rolling"),
    "taxonomy": (drift_taxonomy_grid, "results/drift_taxonomy"),
    "family": (family_grid, "results/family_grid_lag"),
    "patchtst": (patchtst_grid, "results/patchtst_grid"),
}


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    quick = "--quick" in sys.argv
    which = next((a.split("=")[1] for a in sys.argv if a.startswith("--grid=")), "main")
    if which not in GRIDS:
        sys.exit(f"unknown grid {which!r}; choose one of {', '.join(GRIDS)}")
    base = load_config(args[0] if args else "configs/opsd.yaml")
    factory, out = GRIDS[which]
    grid = factory()
    if quick:
        grid = {"dataset": ["opsd", "uci"], "horizon": [1],
                "backbone": ["gbm"], "scenario": ["injected_drift"],
                "onset_frac": [0.5], "seed": [7]}
        out = "results/quick_smoke"
    df = run_grid(base, grid, output_dir=out)
    print("\nDone. Rows:", len(df), "| Tables + SUMMARY.md under:", out)


if __name__ == "__main__":
    main()
