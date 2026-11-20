# Data Cards

One card per dataset used in *Reliable Under Change*. Raw files are downloaded by
`scripts/download_data.py` into `data_raw/` (git-ignored) and loaded by
`src/tef/data/loaders.py`, which resamples to a contiguous hourly grid and applies
the leakage-safe framing in `src/tef/data/features.py`. Stats below are after the
loader's hourly resampling + gap handling.

---

## 1. Open Power System Data — DE country load (primary confirmatory)

| Field | Value |
|---|---|
| Source | Open Power System Data, *Time series* package (`opsd2020`) |
| URL | https://data.open-power-system-data.org/time_series/ |
| License | Data: mostly public/CC-BY per source TSO; verify per-column terms before redistribution |
| Target | `DE_load_actual_entsoe_transparency` → `target` (MW) |
| Exogenous kept | `DE_solar_generation_actual`, `DE_wind_generation_actual` (top-level only; per-TSO breakdowns dropped) |
| Resolution | 60 min (native) |
| Span (loaded) | 2015-01-01 → 2020-09-30 |
| Rows (hourly) | 50,400 |
| Missing handling | short gaps interpolated (≤6 h), residual ffill/bfill on a full hourly grid |
| Role | primary confirmatory (load) |
| Citation key | `opsd2020` |

## 2. UCI Individual Household Electric Power Consumption (secondary confirmatory)

| Field | Value |
|---|---|
| Source | UCI Machine Learning Repository (`hebrail2012uci`) |
| URL | https://archive.ics.uci.edu/dataset/235 |
| License | Open (UCI); DOI 10.24432/C58K54 |
| Target | `Global_active_power` (hourly mean, kW) → `target` |
| Exogenous kept | Voltage, Global_intensity, Sub_metering_1/2/3 |
| Resolution | 1 min (native) → resampled to hourly mean |
| Span (loaded) | 2006-12-16 → 2010-11-26 |
| Rows (hourly) | 34,589 |
| Missing handling | `?` → NaN; short gaps interpolated on a full hourly grid |
| Role | secondary confirmatory (household load); different scale/volatility |
| Citation key | `hebrail2012uci` |

## 3. UNISOLAR — multi-campus PV generation (exploratory renewable target)

| Field | Value |
|---|---|
| Source | Wimalaratne et al., HSI 2022 (`wimalaratne2022unisolar`) |
| Files | `Solar_Energy_Generation.csv` (15-min), `Weather_Data_reordered_all.csv` (hourly), `Solar_Site_Details.csv` |
| License | Open research dataset; cite the authors |
| Target | `SolarGeneration` for one auto-selected (campus, site) with best coverage → `pv` → `target` |
| Exogenous kept | ApparentTemperature, AirTemperature, DewPointTemperature, RelativeHumidity, WindSpeed, WindDirection (that campus) |
| Resolution | 15 min (generation) + hourly (weather) → hourly mean |
| Span (loaded) | 2021-02-03 → 2022-04-23 |
| Rows (hourly) | 10,680 |
| Missing handling | PV NaN treated as ~0 (night/no-output convention); weather short gaps interpolated |
| Role | **exploratory** (renewable/PV target; not part of confirmatory claims) |
| Caveats | zero-inflated target ⇒ intervals over-cover under the injected-drift design (reported, §3.2) |
| Citation key | `wimalaratne2022unisolar` |

---

### Common preprocessing (all datasets)
- Contiguous hourly `DatetimeIndex`; duplicates dropped; trimmed to the span with real target data.
- Features: target lags {1, 24, 168}, trailing rolling mean/std {24, 168}, calendar (hour sin/cos, day-of-week, weekend, month). Lags/rolling use only past values (`shift ≥ 1`).
- Split: chronological train 60% / calibrate 20% / test 20%; scaler fit on train only; leakage assertion (`data/split.assert_no_leakage`).
- Controlled drift injected into the test window for the `injected_drift` scenario (`scenarios/perturb.inject_concept_drift`).
