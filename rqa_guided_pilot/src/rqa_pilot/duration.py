"""Duration matching helpers."""

from __future__ import annotations

import numpy as np


def truncate_to_length(series: np.ndarray, n: int) -> np.ndarray:
    x = np.asarray(series, dtype=np.float64).ravel()
    if n <= 0 or x.size < n:
        return x.copy()
    return x[:n].copy()


def min_length(series_list: list[np.ndarray]) -> int:
    return int(min(len(s) for s in series_list))
