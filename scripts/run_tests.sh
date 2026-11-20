#!/usr/bin/env bash
# Run the full test suite with torch tests isolated in their own process.
# torch + lightgbm co-loaded in one process segfault on macOS (duplicate libomp),
# so we run the deep-model tests in a separate interpreter.
set -e
export KMP_DUPLICATE_LIB_OK=TRUE
export OMP_NUM_THREADS=1

echo "== core suite (no torch) =="
python -m pytest -q          # test_patchtst is ignored via pyproject addopts

echo "== deep-model suite (torch, isolated process) =="
python -m pytest -q tests/test_patchtst.py -o addopts=""

echo "All suites passed."
