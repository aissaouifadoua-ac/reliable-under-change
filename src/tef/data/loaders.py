"""Real-dataset loaders. Each returns (df, drift_onset) with the SAME schema as
`data/synthetic.make_synthetic`:

    df: DatetimeIndex (hourly), columns = ['target', <exogenous…>]
    drift_onset: int | None  — ground-truth onset if known (natural drift => None)

For natural datasets there is no injected ground-truth onset, so `drift_onset`
is None and RQ4/RQ5/RQ6 detection-delay/false-alarm are computed only for the
`injected_drift` scenario (which overlays a controlled change — see
`scenarios.inject_concept_drift`). Loaders are offline: point them at a local
CSV downloaded by `scripts/download_data.py`.

Design notes:
- We resample to hourly, coerce a single target column, and keep a small set of
  exogenous drivers. Feature engineering (lags/rolling/calendar) happens later in
  `data/features.build_features`, so loaders stay thin.
- Missing values: short gaps interpolated, long gaps left for the scenario layer.
"""
from __future__ import annotations
import os
import numpy as np
import pandas as pd


DATA_DIR = os.environ.get("TEF_DATA_DIR", "data_raw")


def _finalize(df: pd.DataFrame, target: str, exog: list[str],
              interp_limit: int = 6) -> pd.DataFrame:
    """Common post-processing → a CONTIGUOUS hourly grid (so positional lag/rolling
    features are time-correct), target+exog columns, gap fill.

    We reindex to a complete hourly range and interpolate; interior gaps are
    filled (short via interpolation, residual via ffill/bfill) rather than dropped,
    which would corrupt lag alignment. Only leading/trailing all-NaN rows are cut.
    """
    df = df.sort_index()
    df = df[~df.index.duplicated(keep="first")]
    keep = [target] + [c for c in exog if c in df.columns]
    out = df[keep].rename(columns={target: "target"})
    # Trim to the span with real target data, then build a full hourly grid.
    valid = out["target"].dropna()
    if valid.empty:
        raise ValueError("target column is entirely missing after selection")
    out = out.loc[valid.index.min():valid.index.max()]
    full = pd.date_range(out.index.min(), out.index.max(), freq="h")
    out = out.reindex(full)
    out["target"] = out["target"].interpolate(limit=interp_limit).ffill().bfill()
    for c in out.columns:
        if c != "target":
            out[c] = out[c].interpolate(limit=interp_limit).ffill().bfill()
    out = out.dropna(subset=["target"])
    out.index.freq = "h"
    return out


def load_opsd(path=None, country="DE", target="load"):
    """Open Power System Data — country load (+ optional weather if present).

    Expects the OPSD 'time_series' CSV (60min). Column names look like
    'DE_load_actual_entsoe_transparency'. Adjust `country` to match your file.
    """
    path = path or os.path.join(DATA_DIR, "opsd_time_series_60min.csv")
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"OPSD file not found at {path}. Run scripts/download_data.py opsd")
    df = pd.read_csv(path, index_col=0, parse_dates=True)
    load_col = next((c for c in df.columns
                     if c.startswith(f"{country}_load") and "actual" in c), None)
    if load_col is None:
        raise ValueError(f"No '{country}_load_actual…' column in {path}. "
                         f"Available sample: {list(df.columns)[:8]}")
    # Only the top-level country solar/wind aggregates as exog — not the per-TSO
    # breakdowns (DE_50hertz_…, DE_amprion_…, DE_LU_…), which are redundant.
    ren = {load_col: "load"}
    exog = []
    for kind in ("solar_generation_actual", "wind_generation_actual"):
        col = f"{country}_{kind}"
        if col in df.columns:
            ren[col] = kind
            exog.append(kind)
    sub = df[list(ren)].rename(columns=ren)
    return _finalize(sub, target=target, exog=exog), None


def load_uci_household(path=None):
    """UCI Individual Household Electric Power Consumption (1-min) → hourly kW.

    File: household_power_consumption.txt (';'-separated, '?' = missing).
    Target = Global_active_power (hourly mean); exog = sub-metering & voltage.
    """
    path = path or os.path.join(DATA_DIR, "household_power_consumption.txt")
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"UCI file not found at {path}. Run scripts/download_data.py uci")
    df = pd.read_csv(path, sep=";", na_values="?", low_memory=False)
    ts = pd.to_datetime(df["Date"] + " " + df["Time"], format="%d/%m/%Y %H:%M:%S")
    df = df.set_index(ts).drop(columns=["Date", "Time"])
    for c in df.columns:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    hourly = df.resample("h").mean()
    hourly = hourly.rename(columns={"Global_active_power": "gap"})
    exog = [c for c in ("Voltage", "Global_intensity", "Sub_metering_1",
                        "Sub_metering_2", "Sub_metering_3") if c in hourly.columns]
    return _finalize(hourly, target="gap", exog=exog), None


def load_unisolar(path=None, campus=None, site=None):
    """UNISOLAR — multi-campus PV generation bundle (Wimalaratne et al. 2022).

    `path` is the DIRECTORY holding the 4 CSVs:
      Solar_Energy_Generation.csv  (CampusKey, SiteKey, Timestamp, SolarGeneration; 15-min)
      Weather_Data_reordered_all.csv (CampusKey, Timestamp, weather…; hourly)
      Solar_Site_Details.csv, Monthly_Summary_Solar.csv (metadata; unused here)

    We select ONE (campus, site) PV series, resample to hourly mean, and join that
    campus's hourly weather as exogenous features. If campus/site are None we pick
    the (campus, site) with the highest non-missing generation fraction.

    Missing handling (documented assumption): PV target NaNs are treated as ~0
    generation (predominantly night/no-output); short weather gaps are interpolated.
    PV is the study's *exploratory* renewable target (Pre-Registration §10).
    """
    path = path or os.path.join(DATA_DIR, "unisolar")
    gen_p = os.path.join(path, "Solar_Energy_Generation.csv")
    wx_p = os.path.join(path, "Weather_Data_reordered_all.csv")
    if not os.path.exists(gen_p):
        raise FileNotFoundError(
            f"UNISOLAR generation CSV not found at {gen_p}. "
            "Point `path` at the extracted UNISOLAR directory.")

    gen = pd.read_csv(gen_p)
    gen["Timestamp"] = pd.to_datetime(gen["Timestamp"])
    if campus is None or site is None:
        cov = (gen.assign(nn=gen["SolarGeneration"].notna())
               .groupby(["CampusKey", "SiteKey"]).nn.mean().sort_values(ascending=False))
        campus, site = map(int, cov.index[0])
    g = gen[(gen.CampusKey == campus) & (gen.SiteKey == site)]
    pv = (g.set_index("Timestamp")["SolarGeneration"]
          .resample("h").mean().rename("pv").to_frame())
    pv["pv"] = pv["pv"].fillna(0.0)  # night/no-output convention

    exog_cols = []
    if os.path.exists(wx_p):
        wx = pd.read_csv(wx_p)
        wx["Timestamp"] = pd.to_datetime(wx["Timestamp"])
        wx = wx[wx.CampusKey == campus].set_index("Timestamp")
        wx = wx.drop(columns=[c for c in ("CampusKey", "SiteKey") if c in wx.columns])
        wx = wx.select_dtypes("number").resample("h").mean()
        exog_cols = list(wx.columns)
        df = pv.join(wx, how="left")
    else:
        df = pv
    df.attrs["campus"], df.attrs["site"] = campus, site
    return _finalize(df, target="pv", exog=exog_cols), None


LOADERS = {"opsd": load_opsd, "uci": load_uci_household, "unisolar": load_unisolar}


def load(name, **kw):
    if name not in LOADERS:
        raise KeyError(f"unknown dataset '{name}'; choose from {list(LOADERS)}")
    return LOADERS[name](**kw)
