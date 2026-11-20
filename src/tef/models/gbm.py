"""Gradient-boosting backbone with graceful fallback.

Prefers LightGBM (primary backbone in the pre-registration); if unavailable,
falls back to sklearn HistGradientBoostingRegressor so the harness still runs.
Supports quantile training for direct quantile intervals.
"""
from __future__ import annotations
import numpy as np

try:  # optional
    import lightgbm as lgb
    _HAS_LGB = True
except Exception:  # pragma: no cover
    _HAS_LGB = False

from sklearn.ensemble import HistGradientBoostingRegressor


class GBMRegressor:
    """Point regressor. backend attr records which library was used."""

    def __init__(self, n_estimators=300, learning_rate=0.05, max_depth=-1,
                 random_state=0, **kw):
        self.params = dict(n_estimators=n_estimators, learning_rate=learning_rate,
                           max_depth=max_depth, random_state=random_state, **kw)
        if _HAS_LGB:
            self.backend = "lightgbm"
            self.model = lgb.LGBMRegressor(
                n_estimators=n_estimators, learning_rate=learning_rate,
                max_depth=max_depth, random_state=random_state, verbose=-1)
        else:
            self.backend = "hist_gbr"
            md = None if max_depth in (-1, None) else max_depth
            self.model = HistGradientBoostingRegressor(
                max_iter=n_estimators, learning_rate=learning_rate,
                max_depth=md, random_state=random_state)

    def fit(self, X, y):
        self.model.fit(np.asarray(X), np.asarray(y))
        return self

    def predict(self, X):
        return self.model.predict(np.asarray(X))


class GBMQuantile:
    """Quantile regressor for direct interval endpoints (pinball loss)."""

    def __init__(self, quantiles=(0.05, 0.5, 0.95), n_estimators=300,
                 learning_rate=0.05, random_state=0):
        self.quantiles = tuple(quantiles)
        self.models = {}
        self._cfg = dict(n_estimators=n_estimators, learning_rate=learning_rate,
                         random_state=random_state)

    def fit(self, X, y):
        X, y = np.asarray(X), np.asarray(y)
        for q in self.quantiles:
            if _HAS_LGB:
                m = lgb.LGBMRegressor(objective="quantile", alpha=q, verbose=-1,
                                      **self._cfg)
            else:
                m = HistGradientBoostingRegressor(
                    loss="quantile", quantile=q,
                    max_iter=self._cfg["n_estimators"],
                    learning_rate=self._cfg["learning_rate"],
                    random_state=self._cfg["random_state"])
            self.models[q] = m.fit(X, y)
        return self

    def predict(self, X):
        X = np.asarray(X)
        return {q: m.predict(X) for q, m in self.models.items()}
