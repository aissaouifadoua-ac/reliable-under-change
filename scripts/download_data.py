#!/usr/bin/env python3
"""Fetch raw datasets into $TEF_DATA_DIR (default: data_raw/).

Usage:
    python scripts/download_data.py opsd
    python scripts/download_data.py uci
    python scripts/download_data.py unisolar     # Kaggle mirror, no login needed

These are large public files; we stream to disk. Re-runs are skipped if present.
Licenses: OPSD (open, cite OPSD); UCI (CC BY 4.0, cite the UCI ML Repository);
UNISOLAR (cite Wimalaratne et al. 2022). The data are not redistributed with this code.
"""
import os
import sys
import urllib.request

DATA_DIR = os.environ.get("TEF_DATA_DIR", "data_raw")

SOURCES = {
    "opsd": {
        "url": "https://data.open-power-system-data.org/time_series/latest/time_series_60min_singleindex.csv",
        "dest": "opsd_time_series_60min.csv",
    },
    "uci": {
        # UCI household power consumption (zip); we extract the .txt.
        "url": "https://archive.ics.uci.edu/static/public/235/individual+household+electric+power+consumption.zip",
        "dest": "household_power_consumption.zip",
        "extract": "household_power_consumption.txt",
    },
    "unisolar": {
        "url": "https://www.kaggle.com/api/v1/datasets/download/cdaclab/unisolar",
        "dest": "UNISOLAR.zip",
        "extract_dir": "unisolar",   # the four CSVs land in data_raw/unisolar/
    },
}


def _download(url, dest):
    os.makedirs(DATA_DIR, exist_ok=True)
    out = os.path.join(DATA_DIR, dest)
    if os.path.exists(out):
        print(f"[skip] {out} already exists")
        return out
    print(f"[get ] {url}\n   -> {out}")
    with urllib.request.urlopen(url) as r, open(out, "wb") as f:  # noqa: S310
        while True:
            chunk = r.read(1 << 20)
            if not chunk:
                break
            f.write(chunk)
    print(f"[done] {os.path.getsize(out)/1e6:.1f} MB")
    return out


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in SOURCES:
        print("choose one of:", ", ".join(SOURCES))
        sys.exit(1)
    key = sys.argv[1]
    spec = SOURCES[key]
    if spec.get("manual"):
        print("UNISOLAR: download from the authors' release "
              "(Wimalaratne et al., 2022, 'UNISOLAR' dataset) and place the CSV at "
              f"{os.path.join(DATA_DIR, 'unisolar.csv')}. "
              "Expected columns: a timestamp + a PV/power column (+ optional weather).")
        return
    path = _download(spec["url"], spec["dest"])
    if spec.get("extract_dir") and path.endswith(".zip"):
        import zipfile
        dest = os.path.join(DATA_DIR, spec["extract_dir"])
        os.makedirs(dest, exist_ok=True)
        with zipfile.ZipFile(path) as z:
            for name in z.namelist():
                if name.endswith(".csv"):
                    with open(os.path.join(dest, os.path.basename(name)), "wb") as f:
                        f.write(z.read(name))
        print(f"[unzip] CSVs -> {dest}")
    if spec.get("extract") and path.endswith(".zip"):
        import zipfile
        with zipfile.ZipFile(path) as z:
            z.extract(spec["extract"], DATA_DIR)
        print(f"[unzip] {spec['extract']} -> {DATA_DIR}")


if __name__ == "__main__":
    main()
