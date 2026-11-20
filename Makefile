# One-command reproduction of every table and figure in the paper.
#   make env        create .venv and install pinned dependencies (needs uv)
#   make test       unit tests (core suite + isolated torch suite)
#   make data       download OPSD, UCI and UNISOLAR into data_raw/
#   make grids      run all six experimental grids        -> results/*/
#   make studies    case studies and detector comparisons -> results/, figures/
#   make figures    regenerate the grid-based figures     -> figures/*.pdf, *.png
#   make repro      data + grids + studies + figures
export KMP_DUPLICATE_LIB_OK = TRUE
export OMP_NUM_THREADS = 1
export PYTHONPATH = src
PYTHON ?= $(if $(wildcard .venv/bin/python),.venv/bin/python,python)

GRIDS = main scenario rolling taxonomy family patchtst

.PHONY: help env test data grids $(addprefix grid-,$(GRIDS)) studies figures repro clean

help:
	@sed -n '1,9p' Makefile

env:
	uv venv --python 3.11 .venv
	VIRTUAL_ENV=.venv uv pip install -r requirements-lock.txt

test:
	PATH=$(dir $(PYTHON)):$$PATH bash scripts/run_tests.sh

data:
	$(PYTHON) scripts/download_data.py opsd
	$(PYTHON) scripts/download_data.py uci
	$(PYTHON) scripts/download_data.py unisolar

grids: $(addprefix grid-,$(GRIDS))

# Static pattern rule: plain pattern rules are not applied to .PHONY targets.
$(addprefix grid-,$(GRIDS)): grid-%:
	$(PYTHON) scripts/run_grid.py --grid=$*

studies:
	$(PYTHON) scripts/natural_drift_case.py
	$(PYTHON) scripts/pv_daylight_coverage.py
	$(PYTHON) scripts/detector_comparison.py
	$(PYTHON) scripts/local_coverage_extensions.py
	$(PYTHON) scripts/measure_efficiency.py

figures:
	$(PYTHON) scripts/make_figures.py
	$(PYTHON) scripts/make_taxonomy_figures.py

repro: data grids studies figures
	@echo "Done. Tables in results/*/SUMMARY.md, figures in figures/."

clean:
	rm -rf results figures
