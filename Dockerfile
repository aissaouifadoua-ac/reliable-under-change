# Reproducible environment for "Reliable under change".
# Build:  docker build -t ruc .
# Test:   docker run --rm ruc
# Repro:  docker run --rm -v "$PWD/data_raw:/app/data_raw" -v "$PWD/results:/app/results" \
#                    -v "$PWD/figures:/app/figures" ruc make repro
FROM python:3.11-slim

# libgomp: OpenMP runtime for LightGBM.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libgomp1 make && rm -rf /var/lib/apt/lists/*

# Single-threaded BLAS/OpenMP keeps LightGBM deterministic; KMP_DUPLICATE_LIB_OK lets
# torch and LightGBM share a process.
ENV KMP_DUPLICATE_LIB_OK=TRUE OMP_NUM_THREADS=1 PYTHONPATH=/app/src

WORKDIR /app
COPY requirements-lock.txt .
RUN pip install --no-cache-dir -r requirements-lock.txt

COPY . .
CMD ["bash", "scripts/run_tests.sh"]
