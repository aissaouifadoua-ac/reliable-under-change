import numpy as np
import pytest

torch = pytest.importorskip("torch")
from tef.models.patchtst import PatchTSTForecaster, build_sequences


def test_build_sequences_alignment():
    t = np.arange(10.0)
    seq = build_sequences(t, lookback=3)
    assert seq.shape == (10, 3)
    # last window ends at the current value
    assert seq[5, -1] == 5.0 and seq[5, 0] == 3.0
    # left-padding for early rows
    assert seq[0, 0] == 0.0 and seq[0, -1] == 0.0


def test_patchtst_learns_and_ig_shapes():
    rng = np.random.default_rng(0)
    t = np.sin(np.arange(1500) / 8.0) + rng.normal(0, 0.05, 1500)
    seq = build_sequences(t, lookback=48)
    y = np.roll(t, -1)[: len(seq)]
    m = PatchTSTForecaster(lookback=48, patch_len=8, stride=4, epochs=5,
                           random_state=0).fit(seq[:1000], y[:1000])
    pred = m.predict(seq[1000:])
    # beats predict-the-mean baseline
    mae = np.mean(np.abs(pred - y[1000:]))
    mae_mean = np.mean(np.abs(y[1000:] - y[:1000].mean()))
    assert mae < mae_mean
    ig = m.integrated_gradients(seq[1000:1010])
    assert ig.shape == (10, 48)
