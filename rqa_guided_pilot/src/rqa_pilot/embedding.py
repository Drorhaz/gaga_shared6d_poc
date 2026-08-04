"""Delay embedding utilities."""

from __future__ import annotations

import numpy as np


def delay_embed(x: np.ndarray, tau: int, m: int) -> np.ndarray:
    """Return embedded trajectory of shape (N_embed, m)."""
    x = np.asarray(x, dtype=np.float64).ravel()
    n = x.size
    n_embed = n - (m - 1) * tau
    if n_embed < 5:
        return np.zeros((0, m), dtype=np.float64)
    idx = np.arange(n_embed)[:, None] + tau * np.arange(m)[None, :]
    return x[idx]


def n_embed(n_samples: int, tau: int, m: int) -> int:
    return max(0, int(n_samples) - (m - 1) * tau)
