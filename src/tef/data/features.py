"""Feature construction and leakage-safe supervised framing.

Leakage rules enforced here:
- Lag/rolling features use only PAST values (shift >= 1, trailing windows).
- The target for horizon h at time t is target[t+h] (predicted from info up to t).
- Scaling is fit on TRAIN only (see split.fit_scaler).
"""
from __future__ import annotations
import numpy as np
import pandas as pd


def build_features(df: pd.DataFrame, lags=(1, 24, 168), rolling=(24,),
                   calendar=True, target_col="target"):
    """Return X (features), y (target, same-time) as aligned DataFrame/Series.
    Horizon shifting is applied later in make_supervised so multiple horizons
    reuse one feature matrix.
    """
    out = pd.DataFrame(index=df.index)
    # Exogenous columns (contemporaneous — assumed known/forecast at predict time).
    for col in df.columns:
        if col != target_col:
            out[col] = df[col]
    # Lags of the target (strictly past).
    for L in lags:
        out[f"{target_col}_lag{L}"] = df[target_col].shift(L)
    # Trailing rolling stats of the target (shift(1) so the current value is excluded).
    for W in rolling:
        base = df[target_col].shift(1)
        out[f"{target_col}_rmean{W}"] = base.rolling(W).mean()
        out[f"{target_col}_rstd{W}"] = base.rolling(W).std()
    if calendar:
        idx = df.index
        out["hour_sin"] = np.sin(2 * np.pi * idx.hour / 24.0)
        out["hour_cos"] = np.cos(2 * np.pi * idx.hour / 24.0)
        out["dow"] = idx.dayofweek
        out["is_weekend"] = (idx.dayofweek >= 5).astype(int)
        out["month"] = idx.month
    y = df[target_col].copy()
    return out, y


def make_supervised(X: pd.DataFrame, y: pd.Series, horizon: int = 1):
    """Shift target by +horizon and drop rows with any NaN (from lags/rolling/shift).
    Returns X_s (np ok via .values), y_s, and the retained integer positions
    (so drift-onset indices can be re-mapped to the supervised frame).
    """
    y_h = y.shift(-horizon)
    frame = X.copy()
    frame["__y__"] = y_h
    valid = frame.dropna()
    kept_positions = np.searchsorted(np.arange(len(X)),
                                     [X.index.get_loc(ix) for ix in valid.index])
    y_s = valid["__y__"]
    X_s = valid.drop(columns="__y__")
    return X_s, y_s, kept_positions


def remap_index(original_idx: int, kept_positions: np.ndarray) -> int:
    """Map an index in the raw series to its position in the supervised frame
    (first kept position >= original_idx). Used to translate drift onset."""
    pos = np.searchsorted(kept_positions, original_idx)
    return int(min(pos, len(kept_positions) - 1))
