"""Set OpenMP-safety env vars BEFORE numpy/torch/lightgbm load.

On macOS, torch and lightgbm each bundle their own libomp; loading both in one
process can segfault. Allowing the duplicate runtime and single-threading avoids
it. conftest.py is imported before any test module, so this runs early enough.
"""
import os

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("OMP_NUM_THREADS", "1")
# NOTE: do NOT import torch here — co-loading torch with lightgbm in one process
# segfaults on macOS (duplicate libomp). The core suite must stay torch-free; the
# deep-model tests run in their own process via scripts/run_tests.sh.
