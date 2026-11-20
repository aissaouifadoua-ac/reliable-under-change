"""Chronological train/calibrate/test split + train-only scaling. No shuffling."""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler


@dataclass
class Split:
    X_train: pd.DataFrame
    y_train: pd.Series
    X_cal: pd.DataFrame
    y_cal: pd.Series
    X_test: pd.DataFrame
    y_test: pd.Series
    scaler: StandardScaler
    train_end: int
    cal_end: int
    # Unscaled feature partitions. Naive baselines (persistence, seasonal-naive) read
    # a target-lag column *as a raw-unit forecast*, so they must use these, not the
    # standardized frames — otherwise they predict standardized (~0) values against a
    # raw-unit target and their error inflates to the scale of the target itself.
    X_test_raw: pd.DataFrame = None
    X_cal_raw: pd.DataFrame = None


def chronological_split(X: pd.DataFrame, y: pd.Series,
                        train=0.6, calibrate=0.2) -> Split:
    """Split by time order into train / calibrate / test. Fit scaler on train only."""
    n = len(X)
    train_end = int(n * train)
    cal_end = int(n * (train + calibrate))
    scaler = StandardScaler().fit(X.iloc[:train_end].values)

    def _scale(df):
        return pd.DataFrame(scaler.transform(df.values), index=df.index,
                            columns=df.columns)

    return Split(
        X_train=_scale(X.iloc[:train_end]), y_train=y.iloc[:train_end],
        X_cal=_scale(X.iloc[train_end:cal_end]), y_cal=y.iloc[train_end:cal_end],
        X_test=_scale(X.iloc[cal_end:]), y_test=y.iloc[cal_end:],
        scaler=scaler, train_end=train_end, cal_end=cal_end,
        X_test_raw=X.iloc[cal_end:], X_cal_raw=X.iloc[train_end:cal_end],
    )


def assert_no_leakage(split: Split):
    """Sanity checks that the split respects time order and is disjoint."""
    assert split.X_train.index.max() < split.X_cal.index.min(), "train/cal overlap"
    assert split.X_cal.index.max() < split.X_test.index.min(), "cal/test overlap"
    return True
