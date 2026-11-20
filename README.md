# Reliable under change

Code and experiments for the paper

> F. Aissaoui, E.M. Abdelmalek. *Reliable under change: adaptive conformal calibration
> and attribution-based drift monitoring for energy forecasting under distribution
> shift.* Submitted to *Sustainable Energy, Grids and Networks*, 2026.

The paper measures how far, how fast and in which direction conformal prediction
intervals for energy forecasts lose their coverage under distribution shift, what
restores it, and whether a label-free attribution signal warns before labels arrive.
This repository regenerates every table and figure in it from the public data.

<!-- PLACEHOLDER: add the Zenodo DOI badge after the first release. -->

## Quick start

```bash
make env       # .venv with the exact package versions used for the paper (needs uv)
make test      # unit tests: core suite + isolated PyTorch suite
make data      # download OPSD, UCI household and UNISOLAR into data_raw/ (~280 MB)
make repro     # every grid, case study and figure
```

Without `uv`: `python -m venv .venv && .venv/bin/pip install -r requirements-lock.txt`.
A Docker image is also provided (`docker build -t ruc .`, see the `Dockerfile` header).

`make repro` takes roughly three hours run sequentially. The six grids are independent,
so `make -j6 grids` runs them in parallel (about 30 minutes on a 32-core workstation),
followed by `make studies figures` (about 40 minutes, most of it the bootstrap nulls and
three timing repeats). No GPU is needed.

## What reproduces what

| Paper | Produced by | Output |
|---|---|---|
| Table 3, Figs. 1, 5, 8, 13 (accuracy, coverage, triggers, faithfulness, Pareto) | `make grid-main` (48 cells) + `make figures` | `results/opsd_grid_main/` |
| Tables 4, 5, equivalence, Fig. 6 (coverage, ladder, lead time) | `make grid-family` (16 cells) | `results/family_grid_lag/` |
| Tables 6, 7, Fig. 2 (local coverage, SAOCP, dependence-aware null) | `scripts/local_coverage_extensions.py` | `results/local_extensions/` |
| Table 9, Fig. 9 (robustness scenarios) | `make grid-scenario` (24 cells) | `results/opsd_grid_scenario/` |
| Rolling-origin backtest | `make grid-rolling` (16 cells) | `results/opsd_grid_rolling/` |
| Figs. 10, 11 (drift type, severity, speed) | `make grid-taxonomy` (60 cells) | `results/drift_taxonomy/` |
| Deep backbone (PatchTST) | `make grid-patchtst` (8 cells) | `results/patchtst_grid/` |
| Fig. 3 (coverage over time) | `scripts/make_figures.py` | `figures/fig6_reliability_timeline.*` |
| Fig. 4 (daylight-conditioned PV coverage) | `scripts/pv_daylight_coverage.py` | `figures/fig13_pv_daylight_coverage.*` |
| Fig. 7 (matched false-alarm detector comparison) | `scripts/detector_comparison.py` | `figures/fig12_detector_delay_vs_far.*` |
| Fig. 12 (natural drift, spring 2020) | `scripts/natural_drift_case.py` | `figures/fig11_natural_drift_covid.*` |
| Fig. 14 (compute accounting) | `scripts/measure_efficiency.py` | `figures/fig7_efficiency.*` |

Figure file names predate the paper's final numbering; the table above is the mapping.

Each grid directory holds `raw_cells.csv` (one row per cell) and `SUMMARY.md` (the
aggregated tables, mean and standard deviation over onset and seed). Every figure is
written as a vector PDF, used in the paper, and a 300-dpi PNG.

## Data

All three datasets are public and are downloaded by `make data`; none is redistributed
here. Provenance, licences and preprocessing are in [DATA_CARDS.md](DATA_CARDS.md).

| Dataset | Target | Source |
|---|---|---|
| OPSD time series, 2020-10-06 | German load | Open Power System Data, doi:10.25832/time_series/2020-10-06 |
| Individual household electric power consumption | active power | UCI ML Repository, doi:10.24432/C58K54 |
| UNISOLAR | PV generation | Wimalaratne et al. (2022), Kaggle mirror `cdaclab/unisolar` |


## Determinism

Seeds are set in each grid. `OMP_NUM_THREADS=1` (set by the Makefile) keeps LightGBM
deterministic, so coverage and accuracy numbers reproduce exactly on the pinned versions.
PatchTST trained on CPU can differ in the last digits across machines. Timings in
`figures/efficiency_seconds.csv` depend on the machine; the paper reports ratios.

## Layout

```
src/tef/
  data/        loaders (OPSD, UCI, UNISOLAR), leakage-safe features, chronological split
  models/      persistence, seasonal naive, ridge, LightGBM, PatchTST
  uq/          static, windowed, ACI, AgACI and SAOCP conformal intervals
  drift/       Page-Hinkley, ADWIN, KS, PSI, MMD, attribution-shift detector
  xai/         SHAP (trees) and Integrated Gradients (PatchTST)
  metrics/     point, interval, drift and attribution metrics
  stats/       Diebold-Mariano, block bootstrap, Friedman/Nemenyi, Holm-Bonferroni
  scenarios/   drift injection, missing data, input noise
  experiment/  one-cell runner and grid sweep
scripts/       grids, case studies, figures, data download
configs/       per-dataset settings
tests/         unit tests
```

## Citation

See [CITATION.cff](CITATION.cff). Please cite the paper and, once released, the archived
version of this code.

## Licence

Code: MIT, see [LICENSE](LICENSE). The datasets keep their own licences.
