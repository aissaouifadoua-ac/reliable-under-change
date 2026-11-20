"""PatchTST deep backbone (channel-independent patch Transformer) + Integrated
Gradients, in PyTorch. Point forecasts plug into the same conformal/drift layers.

Design (Nie et al. 2023, simplified univariate/direct-horizon):
- Input: a lookback window of the (feature-time) target, shape (B, L).
- Patch the window into overlapping patches (patch_len, stride) -> tokens.
- Linear patch embedding + learned positional encoding -> Transformer encoder.
- Flatten tokens -> linear head -> single horizon-ahead value (direct forecast).

Sequences are built from the contiguous hourly target aligned to the supervised
frame, so predictions align 1:1 with the tabular pipeline's test rows.
"""
from __future__ import annotations
import os
import numpy as np

# Avoid the macOS duplicate-libomp segfault (torch + lightgbm in one process).
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

try:
    import torch
    import torch.nn as nn
    _HAS_TORCH = True
except Exception:  # pragma: no cover
    _HAS_TORCH = False


def build_sequences(target_at_feature_time, lookback: int) -> np.ndarray:
    """(N,) contiguous target -> (N, lookback) windows ending at each step.
    Early rows are left-padded with the first value so row alignment is preserved.
    """
    t = np.asarray(target_at_feature_time, dtype=float).ravel()
    n = len(t)
    out = np.empty((n, lookback), dtype=float)
    for i in range(n):
        lo = i - lookback + 1
        if lo < 0:
            pad = np.full(-lo, t[0])
            out[i] = np.concatenate([pad, t[:i + 1]])
        else:
            out[i] = t[lo:i + 1]
    return out


if _HAS_TORCH:
    class _PatchTSTNet(nn.Module):
        def __init__(self, lookback, patch_len=16, stride=8, d_model=64,
                     n_heads=4, n_layers=2, dropout=0.1):
            super().__init__()
            self.patch_len, self.stride = patch_len, stride
            self.n_patches = 1 + (lookback - patch_len) // stride
            self.embed = nn.Linear(patch_len, d_model)
            self.pos = nn.Parameter(torch.randn(1, self.n_patches, d_model) * 0.02)
            layer = nn.TransformerEncoderLayer(
                d_model=d_model, nhead=n_heads, dim_feedforward=d_model * 2,
                dropout=dropout, batch_first=True, activation="gelu")
            self.encoder = nn.TransformerEncoder(layer, num_layers=n_layers)
            self.head = nn.Sequential(nn.Flatten(),
                                      nn.Linear(self.n_patches * d_model, 1))

        def _patch(self, x):  # x: (B, L) -> (B, n_patches, patch_len)
            patches = x.unfold(dimension=1, size=self.patch_len, step=self.stride)
            return patches

        def forward(self, x):
            p = self._patch(x)
            z = self.embed(p) + self.pos
            z = self.encoder(z)
            return self.head(z).squeeze(-1)


class PatchTSTForecaster:
    """sklearn-like wrapper. fit(seq, y) / predict(seq)->yhat. CPU-friendly."""

    def __init__(self, lookback=96, patch_len=16, stride=8, d_model=64, n_heads=4,
                 n_layers=2, epochs=40, lr=1e-3, batch_size=256, random_state=0):
        if not _HAS_TORCH:
            raise ImportError("PatchTST requires torch. `pip install torch`.")
        self.lookback = lookback
        self.cfg = dict(patch_len=patch_len, stride=stride, d_model=d_model,
                        n_heads=n_heads, n_layers=n_layers)
        self.epochs, self.lr, self.batch_size = epochs, lr, batch_size
        self.random_state = random_state
        self.backend = "patchtst"
        self._mu = self._sd = self._ymu = self._ysd = None
        self.net = None

    def _scale_x(self, X):
        return (X - self._mu) / self._sd

    def fit(self, seq, y):
        torch.manual_seed(self.random_state)
        np.random.seed(self.random_state)
        X = np.asarray(seq, float)
        y = np.asarray(y, float)
        self._mu, self._sd = X.mean(), X.std() + 1e-8
        self._ymu, self._ysd = y.mean(), y.std() + 1e-8
        Xs = self._scale_x(X)
        ys = (y - self._ymu) / self._ysd
        self.net = _PatchTSTNet(self.lookback, **self.cfg)
        opt = torch.optim.Adam(self.net.parameters(), lr=self.lr)
        loss_fn = nn.L1Loss()
        Xt = torch.tensor(Xs, dtype=torch.float32)
        yt = torch.tensor(ys, dtype=torch.float32)
        n = len(Xt)
        self.net.train()
        for _ in range(self.epochs):
            perm = torch.randperm(n)
            for s in range(0, n, self.batch_size):
                idx = perm[s:s + self.batch_size]
                opt.zero_grad()
                pred = self.net(Xt[idx])
                loss = loss_fn(pred, yt[idx])
                loss.backward()
                opt.step()
        self.net.eval()
        return self

    def predict(self, seq):
        X = self._scale_x(np.asarray(seq, float))
        with torch.no_grad():
            out = self.net(torch.tensor(X, dtype=torch.float32)).numpy()
        return out * self._ysd + self._ymu

    def integrated_gradients(self, seq, baseline=None, steps=32):
        """IG attributions over lookback positions; returns (N, L) signed array."""
        X = self._scale_x(np.asarray(seq, float))
        Xt = torch.tensor(X, dtype=torch.float32)
        base = (torch.zeros_like(Xt) if baseline is None
                else torch.tensor(self._scale_x(baseline), dtype=torch.float32))
        total = torch.zeros_like(Xt)
        for a in np.linspace(1.0 / steps, 1.0, steps):
            xi = (base + a * (Xt - base)).clone().requires_grad_(True)
            out = self.net(xi).sum()
            grad, = torch.autograd.grad(out, xi)
            total += grad
        ig = (Xt - base) * total / steps
        return ig.detach().numpy()
