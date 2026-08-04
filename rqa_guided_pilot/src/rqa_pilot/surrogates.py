"""Temporal surrogate controls for RQA structure metrics."""

from __future__ import annotations

import numpy as np


def full_shuffle(x: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    y = np.asarray(x, dtype=np.float64).copy()
    rng.shuffle(y)
    return y


def block_shuffle(x: np.ndarray, block_len: int, rng: np.random.Generator) -> np.ndarray:
    """Shuffle contiguous blocks; preserves short local behavior."""
    y = np.asarray(x, dtype=np.float64).ravel()
    n = y.size
    if block_len <= 1 or block_len >= n:
        return full_shuffle(y, rng)
    n_blocks = int(np.ceil(n / block_len))
    pads = n_blocks * block_len - n
    if pads:
        y = np.concatenate([y, np.full(pads, np.nan)])
    blocks = y.reshape(n_blocks, block_len)
    rng.shuffle(blocks, axis=0)
    out = blocks.ravel()[:n]
    return out


def make_surrogate(x: np.ndarray, kind: str, block_len: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    if kind == "identity":
        return np.asarray(x, dtype=np.float64).copy()
    if kind == "full_shuffle":
        return full_shuffle(x, rng)
    if kind == "block_shuffle":
        return block_shuffle(x, block_len, rng)
    raise ValueError(kind)
