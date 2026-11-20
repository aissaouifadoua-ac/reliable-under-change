"""Synthetic non-stationary energy-like series with a *controlled* concept drift,
so the harness runs end-to-end (and RQ4/RQ5/RQ6 have ground-truth drift onset)
without downloading data. Real loaders (OPSD/UCI/UNISOLAR) share the same schema.

Schema: a DataFrame indexed by an hourly DatetimeIndex with columns:
  target, temp, irradiance  (plus calendar/lag features added later by features.py)
The returned `drift_onset` is the integer row index where the input->target
relationship changes (concept drift), used as ground truth.
"""
from __future__ import annotations
import numpy as np
import pandas as pd


def make_synthetic(n=6000, seed=0, drift_onset_frac=0.75, drift_magnitude=1.5,
                   start="2021-01-01"):
    rng = np.random.default_rng(seed)
    idx = pd.date_range(start=start, periods=n, freq="h")
    hour = idx.hour.to_numpy()
    dow = idx.dayofweek.to_numpy()
    doy = idx.dayofyear.to_numpy()

    # Exogenous drivers.
    temp = 15 + 10 * np.sin(2 * np.pi * (doy / 365.0)) \
        + 4 * np.sin(2 * np.pi * (hour / 24.0)) + rng.normal(0, 1.5, n)
    irradiance = np.clip(np.sin(np.pi * (hour - 6) / 12.0), 0, None) \
        * (0.6 + 0.4 * np.sin(2 * np.pi * doy / 365.0)) + rng.normal(0, 0.05, n)
    irradiance = np.clip(irradiance, 0, None)

    # Base load: daily + weekly seasonality + temperature effect.
    daily = 8 * np.sin(2 * np.pi * (hour - 8) / 24.0)
    weekly = -3.0 * (dow >= 5)
    beta_temp = 1.2  # coefficient of temp -> load (this is what drifts)

    onset = int(n * drift_onset_frac)
    beta_series = np.full(n, beta_temp)
    # Concept drift: the temperature->load relationship strengthens after onset
    # (e.g. AC/heat-pump adoption). Input distributions stay similar; the *map* changes.
    beta_series[onset:] = beta_temp * drift_magnitude

    load = 100 + daily + weekly + beta_series * (temp - 15) + rng.normal(0, 2.0, n)

    df = pd.DataFrame({"target": load, "temp": temp, "irradiance": irradiance},
                      index=idx)
    return df, onset
