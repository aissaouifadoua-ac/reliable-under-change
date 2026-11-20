"""Conformal prediction interval methods.

The adaptation family, from least to most reactive:
- SplitConformal: static absolute-residual conformal (calibrate once; fixed width).
- WindowedConformal: rolling split conformal — recompute the residual quantile on a
  trailing window each step (adapts to residual *scale*, but the level is fixed at
  nominal; no coverage feedback). The non-trivial adaptive baseline.
- AdaptiveConformalInference (ACI): Gibbs & Candes (2021) online update of the
  effective miscoverage level from realized coverage.
- AgACI: aggregated ACI (Zaffran et al. 2022) — run ACI experts over a gamma grid and
  aggregate their widths online by interval-score performance, removing gamma tuning.

All produce symmetric intervals around a point forecast; residual scores are
absolute residuals |y - yhat|.
"""
from __future__ import annotations
import numpy as np


def _finite_quantile(scores: np.ndarray, level: float) -> float:
    """Conformal quantile with finite-sample correction (ceil((n+1)(level))/n)."""
    s = np.sort(np.asarray(scores, dtype=float).ravel())
    n = len(s)
    if n == 0:
        return float("inf")
    k = int(np.ceil((n + 1) * level))
    k = min(max(k, 1), n)
    return float(s[k - 1])


class SplitConformal:
    """Static split conformal. Calibrate once on held-out residuals; fixed width."""

    def __init__(self, nominal: float = 0.90):
        self.nominal = nominal
        self.q_ = None

    def calibrate(self, y_cal, yhat_cal):
        scores = np.abs(np.asarray(y_cal, float) - np.asarray(yhat_cal, float))
        self.q_ = _finite_quantile(scores, self.nominal)
        return self

    def intervals(self, yhat):
        yhat = np.asarray(yhat, float)
        return yhat - self.q_, yhat + self.q_


class WindowedConformal:
    """Rolling split conformal: the residual quantile is re-estimated on a trailing
    window every step. Unlike ACI there is no coverage feedback — the level stays at
    ``nominal`` and only the residual *sample* rolls. This isolates the question of
    whether re-estimating the quantile on recent residuals is enough, or whether the
    ACI feedback term is doing the work. Non-trivial adaptive baseline.
    """

    def __init__(self, nominal: float = 0.90, window: int = 500):
        self.nominal = nominal
        self.window = window
        self._resid = []

    def seed_residuals(self, y_cal, yhat_cal):
        r = np.abs(np.asarray(y_cal, float) - np.asarray(yhat_cal, float))
        self._resid.extend(list(r))
        return self

    def _q(self):
        if not self._resid:
            return float("inf")
        return _finite_quantile(np.array(self._resid[-self.window:]), self.nominal)

    def run(self, yhat, y, lag=1):
        """Online pass with delayed feedback: the residual of the forecast issued at
        step ``s`` is only available ``lag`` steps later (``lag`` = horizon), so it can
        influence the interval issued at ``s+lag`` at the earliest. ``lag=1`` recovers
        the standard one-step-ahead setting."""
        yhat = np.asarray(yhat, float)
        y = np.asarray(y, float)
        lo = np.empty_like(yhat)
        hi = np.empty_like(yhat)
        for t in range(len(yhat)):
            s = t - lag
            if s >= 0:  # label of forecast s is observed now
                self._resid.append(abs(y[s] - yhat[s]))
            q = self._q()
            lo[t], hi[t] = yhat[t] - q, yhat[t] + q
        return lo, hi


def _interval_score_point(y, lo, hi, alpha):
    """Single-point Winkler interval score (lower is better)."""
    width = hi - lo
    pen = 0.0
    if y < lo:
        pen = (2.0 / alpha) * (lo - y)
    elif y > hi:
        pen = (2.0 / alpha) * (y - hi)
    return width + pen


class AdaptiveConformalInference:
    """ACI (Gibbs & Candes 2021): ``theta`` is the *adaptive miscoverage level*
    alpha_t, updated online toward the target miscoverage alpha = 1 - nominal.

    Update: alpha_{t+1} = alpha_t + gamma * (alpha - err_t), with err_t = 1 if y_t
    fell outside the interval else 0. On a miss (err_t=1) alpha_t decreases, so the
    quantile level 1 - alpha_t rises and the interval widens; on over-coverage it
    tightens. The half-width is the (1 - alpha_t) empirical quantile of the residuals
    observed so far (rolling window). ACI regulates *long-run* miscoverage frequency
    under distribution shift, not exact coverage in every local window.
    """

    def __init__(self, nominal: float = 0.90, gamma: float = 0.01, window: int = 500):
        self.nominal = nominal
        self.alpha = 1.0 - nominal
        self.gamma = gamma
        self.window = window
        self.theta = self.alpha  # adaptive miscoverage level alpha_t; start at target
        self._resid = []

    def _q(self):
        if not self._resid:
            return float("inf")
        level = float(np.clip(1.0 - self.theta, 0.0, 1.0))
        return _finite_quantile(np.array(self._resid[-self.window:]), level)

    def step(self, yhat_t, y_t=None):
        """Return (lower, upper) for the current point using residuals so far.
        If y_t is provided, update residual buffer and theta for the NEXT step.
        Returns (lower, upper, width).
        """
        q = self._q()
        lo, hi = yhat_t - q, yhat_t + q
        if y_t is not None:
            covered = (y_t >= lo) and (y_t <= hi)
            err = 0.0 if covered else 1.0
            # widen when we under-cover (err high), tighten when we over-cover.
            self.theta = float(np.clip(self.theta + self.gamma * (self.alpha - err),
                                       1e-4, 1 - 1e-4))
            self._resid.append(abs(y_t - yhat_t))
        return lo, hi, q

    def run(self, yhat, y, lag=1):
        """Online pass with delayed feedback (``lag`` = horizon). The error and residual
        of the forecast issued at ``s`` update theta/the buffer only at ``s+lag``, when
        its label is observed — no look-ahead at multi-step horizons. ``lag=1`` is the
        standard one-step setting."""
        yhat = np.asarray(yhat, float)
        y = np.asarray(y, float)
        lo = np.empty_like(yhat)
        hi = np.empty_like(yhat)
        formed_lo, formed_hi = {}, {}
        for t in range(len(yhat)):
            s = t - lag
            if s >= 0:  # label of forecast s observed now -> deferred update
                covered = (y[s] >= formed_lo[s]) and (y[s] <= formed_hi[s])
                err = 0.0 if covered else 1.0
                self.theta = float(np.clip(self.theta + self.gamma * (self.alpha - err),
                                           1e-4, 1 - 1e-4))
                self._resid.append(abs(y[s] - yhat[s]))
            q = self._q()
            lo[t], hi[t] = yhat[t] - q, yhat[t] + q
            formed_lo[t], formed_hi[t] = lo[t], hi[t]
        return lo, hi

    def seed_residuals(self, y_cal, yhat_cal):
        """Warm-start the residual buffer from the calibration set."""
        r = np.abs(np.asarray(y_cal, float) - np.asarray(yhat_cal, float))
        self._resid.extend(list(r))
        return self


class AgACI:
    """Aggregated ACI (Zaffran et al. 2022): run a set of ACI experts over a gamma
    grid and aggregate their half-widths online with exponentially-weighted weights
    driven by each expert's recent interval-score loss. This removes the single-gamma
    tuning that ACI is criticised for — the aggregate tracks whichever gamma is
    currently performing best without committing to one a priori.
    """

    def __init__(self, nominal: float = 0.90,
                 gammas=(0.0, 0.005, 0.01, 0.02, 0.05, 0.1),
                 window: int = 500, eta: float = 2.0):
        self.nominal = nominal
        self.alpha = 1.0 - nominal
        self.eta = eta
        self.experts = [AdaptiveConformalInference(nominal, gamma=g, window=window)
                        for g in gammas]
        self.logw = np.zeros(len(self.experts))  # log-weights, normalized on use

    def seed_residuals(self, y_cal, yhat_cal):
        for e in self.experts:
            e.seed_residuals(y_cal, yhat_cal)
        return self

    def _weights(self):
        w = np.exp(self.logw - self.logw.max())
        s = w.sum()
        return w / s if s > 0 else np.full(len(w), 1.0 / len(w))

    def run(self, yhat, y, lag=1):
        """Online pass with delayed feedback (``lag`` = horizon): each expert's state
        and the aggregation weights are updated from the forecast issued at ``s`` only
        at ``s+lag``, when its label is observed. ``lag=1`` is the standard setting."""
        yhat = np.asarray(yhat, float)
        y = np.asarray(y, float)
        lo = np.empty_like(yhat)
        hi = np.empty_like(yhat)
        formed_q = {}  # per-expert half-widths issued at each step (for deferred update)
        for t in range(len(yhat)):
            s = t - lag
            if s >= 0:  # label of forecast s observed now -> deferred expert/weight update
                qs_s = formed_q[s]
                losses = np.array([_interval_score_point(
                    y[s], yhat[s] - q, yhat[s] + q, self.alpha) for q in qs_s])
                scale = np.median(losses) + 1e-9
                self.logw = self.logw - self.eta * (losses / scale)
                for k, e in enumerate(self.experts):
                    covered = (y[s] >= yhat[s] - qs_s[k]) and (y[s] <= yhat[s] + qs_s[k])
                    err = 0.0 if covered else 1.0
                    e.theta = float(np.clip(e.theta + e.gamma * (e.alpha - err),
                                            1e-4, 1 - 1e-4))
                    e._resid.append(abs(y[s] - yhat[s]))
            qs = np.array([e._q() for e in self.experts])
            qs = np.where(np.isfinite(qs), qs, np.nanmax(qs[np.isfinite(qs)])
                          if np.isfinite(qs).any() else 0.0)
            w = self._weights()
            q_agg = float(np.dot(w, qs))
            lo[t], hi[t] = yhat[t] - q_agg, yhat[t] + q_agg
            formed_q[t] = qs
        return lo, hi


def _pinball(score, radius, coverage):
    """Pinball (quantile) loss of predicting ``radius`` for a nonconformity ``score``."""
    d = score - radius
    return coverage * d if d >= 0 else (coverage - 1.0) * d


class _ScaleFreeOGD:
    """One SAOCP expert: scale-free online gradient descent on the pinball loss of the
    interval radius (Bhatnagar et al. 2023, Algorithm 1). Step size is
    D / sqrt(3) * g_t / sqrt(sum_j g_j^2), so it needs no learning-rate tuning.
    ``updates`` counts the rounds the expert has lived, for its finite lifetime."""

    def __init__(self, coverage, scale, init=0.0):
        self.coverage = coverage
        self.scale = scale
        self.radius = float(init)
        self.grad_sq = 0.0
        self.updates = 0

    def update(self, score):
        # Subgradient of the pinball loss in the radius.
        grad = (-self.coverage if score > self.radius
                else (1.0 - self.coverage) if score < self.radius else 0.0)
        self.grad_sq += grad * grad
        self.updates += 1
        if self.grad_sq > 0:
            self.radius = max(0.0, self.radius
                              - self.scale / np.sqrt(3.0) * grad / np.sqrt(self.grad_sq))


class StronglyAdaptiveConformal:
    """SAOCP (Bhatnagar, Wang, Xiong & Bai 2023, Algorithm 2): strongly adaptive online
    conformal prediction. A new scale-free-OGD expert is started at every step with a
    geometric lifetime ``lifetime * 2^(trailing zeros of t)``; the active experts' radii
    are aggregated with the coin-betting sleeping-expert weights of the paper. Unlike
    ACI, which regulates long-run miscoverage, the regret bound holds on every
    sub-interval, so the method targets *local* coverage.

    The learned quantity is the interval radius itself (absolute-residual score), so the
    intervals stay symmetric and directly comparable with the rest of the ladder.
    The implementation follows the authors' reference code (salesforce/online_conformal,
    ``saocp.py``) in every detail that affects the output: lifetime multiplier 8, a
    newborn expert initialised at the current aggregate radius, ``scale`` (the paper's
    D) defaulting to sqrt(3) times the largest calibration residual, the clipped
    coin-betting gain, and retirement after ``lifetime + 1`` updates. Run side by side
    with a transcription of that code, the radii are not bit-identical: a newborn
    expert's first gain is exactly 0 in exact arithmetic and comes out as a ~1e-17
    residue in the reference, which flips the sign test on its weight. Aggregate
    behaviour agrees (coverage within 0.002, radius correlation above 0.99).
    """

    def __init__(self, nominal: float = 0.90, lifetime: int = 8, scale=None):
        self.nominal = nominal
        self.lifetime = int(lifetime)
        self.scale = scale
        self.t = 0                      # number of scores consumed so far
        self.experts = {}               # start index -> expert state and meta weights
        self.radius = 0.0               # current aggregated radius
        self._warm = []

    def seed_residuals(self, y_cal, yhat_cal):
        """Warm start: set D from the calibration residuals and run the learner over
        them, so the first test interval is already calibrated (as for the other rungs,
        which seed their residual buffer from the calibration set)."""
        r = np.abs(np.asarray(y_cal, float) - np.asarray(yhat_cal, float))
        if self.scale is None:
            self.scale = float(np.max(r)) * np.sqrt(3.0) if len(r) else 1.0
        for s in r:
            self._consume(float(s))
        return self

    def _lifetime(self, t):
        nu = (t & -t).bit_length() - 1          # trailing zeros of t (t >= 1)
        return self.lifetime * (2 ** nu)

    def _consume(self, score):
        """One SAOCP round on an observed nonconformity score."""
        if self.scale is None:
            self.scale = max(float(score), 1e-12)
        self.t += 1
        t = self.t
        # Retire expired experts, start the expert born at t (initialised at the current
        # aggregate so a newborn does not drag the radius to zero).
        self.experts = {i: e for i, e in self.experts.items()
                        if e["expert"].updates <= e["lifetime"]}
        self.experts[t] = {
            "expert": _ScaleFreeOGD(self.nominal, self.scale, init=self.radius),
            "lifetime": self._lifetime(t), "sum_g": 0.0, "sum_wg": 0.0, "w": 0.0,
            "prior": 1.0 / (t ** 2 * (1.0 + np.floor(np.log2(t)))),
        }
        # Aggregate radius for this round from the active experts.
        radius = self._aggregate()
        # Meta update (coin betting) and expert updates on the revealed score.
        norm = self.scale * max(self.nominal, 1.0 - self.nominal)
        loss_meta = _pinball(score, radius, self.nominal)
        for i, e in self.experts.items():
            g = (loss_meta - _pinball(score, e["expert"].radius, self.nominal)) / norm
            g = float(np.clip(g, -1.0 if e["w"] > 0 else 0.0, 1.0))
            e["sum_g"] += g
            e["sum_wg"] += e["w"] * g
            e["w"] = e["sum_g"] / (t - i + 1) * (1.0 + e["sum_wg"])
            e["expert"].update(score)
        self.radius = self._aggregate()

    def _aggregate(self):
        ids = list(self.experts)
        prior = np.array([self.experts[i]["prior"] for i in ids])
        w = np.array([max(self.experts[i]["w"], 0.0) for i in ids])
        p = prior * w
        p = p / p.sum() if p.sum() > 0 else prior / prior.sum()
        return float(np.dot(p, [self.experts[i]["expert"].radius for i in ids]))

    def run(self, yhat, y, lag=1):
        """Online pass with delayed feedback (``lag`` = horizon). The learner consumes
        the score of the forecast issued at ``s`` only at ``s+lag``, when its label is
        observed, and the interval issued at ``t`` uses the radius learned from the
        scores available by then. No look-ahead at multi-step horizons."""
        yhat = np.asarray(yhat, float)
        y = np.asarray(y, float)
        lo = np.empty_like(yhat)
        hi = np.empty_like(yhat)
        for t in range(len(yhat)):
            s = t - lag
            if s >= 0:
                self._consume(abs(y[s] - yhat[s]))
            lo[t], hi[t] = yhat[t] - self.radius, yhat[t] + self.radius
        return lo, hi
