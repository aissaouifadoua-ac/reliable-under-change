"""Naive/statistical baselines. Each exposes fit(X, y) and predict(X).

Persistence and SeasonalNaive operate on the target's own lag columns, so they
need the lag feature names; they are given the raw target history at predict time
via a column convention (target_lag1, target_lag{season}).
"""
from __future__ import annotations
import numpy as np
from sklearn.linear_model import Ridge as _Ridge


class Persistence:
    """Predict y_hat = last observed target (target_lag1 feature)."""

    def __init__(self, lag_col="target_lag1"):
        self.lag_col = lag_col

    def fit(self, X, y=None):
        return self

    def predict(self, X):
        return np.asarray(X[self.lag_col].values, float)


class SeasonalNaive:
    """Predict y_hat = target value one season ago (e.g. target_lag24 or _lag168)."""

    def __init__(self, season_col="target_lag24"):
        self.season_col = season_col

    def fit(self, X, y=None):
        return self

    def predict(self, X):
        return np.asarray(X[self.season_col].values, float)


class Ridge:
    def __init__(self, alpha=1.0):
        self.m = _Ridge(alpha=alpha)

    def fit(self, X, y):
        self.m.fit(np.asarray(X), np.asarray(y))
        return self

    def predict(self, X):
        return self.m.predict(np.asarray(X))
