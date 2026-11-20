"""Robustness scenarios applied to a feature frame (pre-specified in §5).
Injected drift is produced by the data generator (ground-truth onset); these
helpers add missingness and noise for the robustness experiments.
"""
from __future__ import annotations
import numpy as np
import pandas as pd


def inject_missing(X: pd.DataFrame, frac=0.1, seed=0, fill="ffill"):
    """Randomly blank `frac` of cells then fill (simulating sensor dropout)."""
    rng = np.random.default_rng(seed)
    Xm = X.copy()
    mask = rng.random(Xm.shape) < frac
    Xm = Xm.mask(mask)
    if fill == "ffill":
        Xm = Xm.ffill().bfill()
    elif fill == "interp":
        Xm = Xm.interpolate().ffill().bfill()
    return Xm


def _pick_driver(df, target_col):
    """Exogenous column most correlated with the target (None if none exist)."""
    exog = [c for c in df.columns if c != target_col]
    if not exog:
        return None
    corrs = {c: abs(np.corrcoef(df[c].values, df[target_col].values)[0, 1])
             for c in exog}
    return max(corrs, key=corrs.get)


def inject_drift(df: pd.DataFrame, onset_frac=0.9, magnitude=1.5,
                 drift_type="conditional", transition=0, driver=None,
                 target_col="target"):
    """Overlay a CONTROLLED drift on a real series with a ground-truth onset, along
    three experimental axes so drift is a first-class variable (not just on/off):

    * ``drift_type`` — the *kind* of distribution change:
        - ``"conditional"``: amplify the target's dependence on the driver by
          ``magnitude`` (the model's learned map is now wrong). The *exogenous* driver
          is untouched, but because the feature set is autoregressive (target lags),
          the change propagates into the inputs at later steps — it carries an input
          signature rather than being a pure P(Y|X) change with P(X) frozen.
        - ``"covariate"``: shift the driver's distribution by ``(magnitude-1)`` pre-
          onset std, and move the target by the pre-onset regression slope so the
          *map* P(Y|X) is approximately preserved (only P(X) changes). The model sees the shifted
          driver, so a well-specified model should stay calibrated.
    * ``magnitude`` — severity. ``magnitude=1`` is no drift for either type.
    * ``transition`` — speed. ``0`` = abrupt step at onset; ``>0`` = linear ramp over
      that many steps (slower drift), so recovery dynamics can be measured vs speed.

    Returns ``(df_drifted, onset_int)``.
    """
    df = df.copy()
    n = len(df)
    onset = int(n * onset_frac)
    if driver is None:
        # Select the driver using ONLY the pre-onset segment, so the choice of which
        # exogenous variable to perturb does not peek at the (scored) post-onset region.
        assert 0 < onset < n, "drift onset must lie strictly inside the series"
        driver = _pick_driver(df.iloc[:onset], target_col)
    if driver is None:  # no exogenous driver: fall back to a target level shift.
        df.iloc[onset:, df.columns.get_loc(target_col)] *= magnitude
        return df, onset

    # Ramp weight w(t) in [0,1]: step (transition=0) or linear over `transition`.
    idx = np.arange(n)
    if transition and transition > 0:
        w = np.clip((idx - onset) / float(transition), 0.0, 1.0)
    else:
        w = (idx >= onset).astype(float)

    d = df[driver].values.astype(float)
    tvals = df[target_col].values.astype(float)

    if drift_type == "covariate":
        # Preserve P(Y|X): shift driver by k*sigma, move target by slope*shift.
        sigma = np.nanstd(d[:onset]) + 1e-12
        dc = d[:onset] - np.nanmean(d[:onset])
        tc = tvals[:onset] - np.nanmean(tvals[:onset])
        slope = float(np.dot(dc, tc) / (np.dot(dc, dc) + 1e-12))
        shift = (magnitude - 1.0) * sigma * w
        df[driver] = d + shift          # P(X) changes (model observes it)
        tvals = tvals + slope * shift    # map preserved => residuals ~ unchanged
    else:  # "conditional" (concept shift): change the map, leave P(X) intact.
        d_center = d - np.nanmean(d[:onset])
        tvals = tvals + (magnitude - 1.0) * d_center * w

    df[target_col] = tvals
    return df, onset


def inject_concept_drift(df: pd.DataFrame, onset_frac=0.9, magnitude=1.5,
                         driver=None, target_col="target"):
    """Backward-compatible alias: abrupt conditional (concept) drift."""
    return inject_drift(df, onset_frac=onset_frac, magnitude=magnitude,
                        drift_type="conditional", transition=0, driver=driver,
                        target_col=target_col)


def add_noise(X: pd.DataFrame, snr_db=20.0, seed=0):
    """Add Gaussian noise at a target signal-to-noise ratio (dB) per column."""
    rng = np.random.default_rng(seed)
    Xn = X.copy()
    for c in Xn.columns:
        sig_p = np.var(Xn[c].values) + 1e-12
        noise_p = sig_p / (10 ** (snr_db / 10.0))
        Xn[c] = Xn[c].values + rng.normal(0, np.sqrt(noise_p), len(Xn))
    return Xn
