import numpy as np
import pandas as pd
from tef.data.loaders import load_uci_household, load_opsd
from tef.scenarios.perturb import inject_concept_drift


def _write_uci(tmp_path):
    idx = pd.date_range("2007-01-01", periods=600, freq="min")
    df = pd.DataFrame({
        "Date": idx.strftime("%d/%m/%Y"),
        "Time": idx.strftime("%H:%M:%S"),
        "Global_active_power": np.abs(np.random.RandomState(0).normal(2, 0.5, len(idx))),
        "Voltage": np.random.RandomState(1).normal(240, 2, len(idx)),
        "Global_intensity": np.random.RandomState(2).normal(10, 1, len(idx)),
        "Sub_metering_1": np.random.RandomState(3).uniform(0, 5, len(idx)),
        "Sub_metering_2": np.random.RandomState(4).uniform(0, 5, len(idx)),
        "Sub_metering_3": np.random.RandomState(5).uniform(0, 5, len(idx)),
    })
    p = tmp_path / "household_power_consumption.txt"
    df.to_csv(p, sep=";", index=False)
    return str(p)


def test_uci_loader_schema(tmp_path):
    path = _write_uci(tmp_path)
    df, onset = load_uci_household(path=path)
    assert "target" in df.columns and onset is None
    assert isinstance(df.index, pd.DatetimeIndex)
    assert df.index.freqstr == "h"          # resampled to hourly
    assert not df["target"].isna().any()


def test_opsd_loader_schema(tmp_path):
    idx = pd.date_range("2018-01-01", periods=200, freq="h")
    df = pd.DataFrame({
        "DE_load_actual_entsoe_transparency": np.random.RandomState(0).normal(50000, 3000, 200),
        "DE_solar_generation_actual": np.random.RandomState(1).uniform(0, 20000, 200),
    }, index=idx)
    p = tmp_path / "opsd_time_series_60min.csv"
    df.to_csv(p)
    out, onset = load_opsd(path=str(p), country="DE")
    assert "target" in out.columns and "solar_generation_actual" in out.columns
    assert onset is None


def test_inject_drift_returns_onset():
    idx = pd.date_range("2020-01-01", periods=1000, freq="h")
    base = np.sin(np.arange(1000) / 24.0)
    df = pd.DataFrame({"target": 100 + 5 * base, "temp": base}, index=idx)
    drifted, onset = inject_concept_drift(df, onset_frac=0.8, magnitude=2.0,
                                          driver="temp")
    assert 0 < onset < 1000
    # pre-onset unchanged, post-onset altered
    assert np.allclose(drifted["target"].values[:onset], df["target"].values[:onset])
    assert not np.allclose(drifted["target"].values[onset:], df["target"].values[onset:])
