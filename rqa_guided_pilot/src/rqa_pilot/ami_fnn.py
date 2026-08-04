"""Average Mutual Information and False Nearest Neighbors (T1 diagnostics)."""

from __future__ import annotations

import numpy as np

from .embedding import delay_embed


def average_mutual_information(x: np.ndarray, max_tau: int, n_bins: int = 16) -> np.ndarray:
    """AMI(τ) for τ=1..max_tau using equal-width histogram bins."""
    x = np.asarray(x, dtype=np.float64).ravel()
    x = x[np.isfinite(x)]
    if x.size < max_tau + 20:
        return np.full(max_tau, np.nan)
    # rank-ish robust binning via percentiles
    edges = np.unique(np.quantile(x, np.linspace(0, 1, n_bins + 1)))
    if edges.size < 3:
        return np.full(max_tau, np.nan)
    ami = np.empty(max_tau, dtype=np.float64)
    nb = edges.size - 1
    for tau in range(1, max_tau + 1):
        a = x[:-tau]
        b = x[tau:]
        joint, _, _ = np.histogram2d(a, b, bins=edges)
        joint = joint / joint.sum()
        pa = joint.sum(axis=1, keepdims=True)
        pb = joint.sum(axis=0, keepdims=True)
        with np.errstate(divide="ignore", invalid="ignore"):
            ratio = np.where((joint > 0) & (pa > 0) & (pb > 0), joint / (pa * pb), 1.0)
            ami[tau - 1] = float(np.nansum(joint * np.log2(ratio)))
    return ami


def first_local_minimum(ami: np.ndarray) -> int | None:
    """Return τ (1-based) of first local minimum, or None."""
    if ami.size < 3 or not np.isfinite(ami).any():
        return None
    for i in range(1, ami.size - 1):
        if not np.isfinite(ami[i]):
            continue
        if ami[i] <= ami[i - 1] and ami[i] <= ami[i + 1]:
            return i + 1
    # plateau / slow decay: first τ where AMI drops below 1/e of AMI(1)
    a1 = ami[0]
    if np.isfinite(a1) and a1 > 0:
        thr = a1 / np.e
        for i, v in enumerate(ami):
            if np.isfinite(v) and v <= thr:
                return i + 1
    return None


def autocorrelation(x: np.ndarray, max_lag: int) -> np.ndarray:
    x = np.asarray(x, dtype=np.float64).ravel()
    x = x - np.nanmean(x)
    if x.size < max_lag + 5:
        return np.full(max_lag + 1, np.nan)
    denom = np.dot(x, x)
    if denom < 1e-18:
        return np.full(max_lag + 1, np.nan)
    out = np.empty(max_lag + 1, dtype=np.float64)
    out[0] = 1.0
    for lag in range(1, max_lag + 1):
        out[lag] = np.dot(x[:-lag], x[lag:]) / denom
    return out


def first_acf_zero(acf: np.ndarray) -> int | None:
    for i in range(1, acf.size):
        if np.isfinite(acf[i]) and acf[i] <= 0:
            return i
    return None


def false_nearest_neighbors(
    x: np.ndarray,
    tau: int,
    max_m: int = 8,
    rtol: float = 15.0,
    atol: float = 2.0,
) -> np.ndarray:
    """Fraction of false nearest neighbors for m=1..max_m (Kennel-style)."""
    x = np.asarray(x, dtype=np.float64).ravel()
    x = x[np.isfinite(x)]
    frac = np.full(max_m, np.nan)
    if x.size < (max_m + 1) * tau + 30:
        return frac
    ra = np.std(x)
    if ra < 1e-12:
        return frac
    for m in range(1, max_m + 1):
        emb = delay_embed(x, tau, m)
        if emb.shape[0] < 20:
            continue
        # nearest neighbor excluding trivial temporal neighbors within tau
        # brute force OK for short series
        d2 = np.sum((emb[:, None, :] - emb[None, :, :]) ** 2, axis=2)
        np.fill_diagonal(d2, np.inf)
        for i in range(emb.shape[0]):
            lo = max(0, i - tau)
            hi = min(emb.shape[0], i + tau + 1)
            d2[i, lo:hi] = np.inf
        nn = np.argmin(d2, axis=1)
        dist = np.sqrt(d2[np.arange(emb.shape[0]), nn])
        # next coordinate
        n_next = x.size - m * tau
        if n_next < emb.shape[0]:
            emb = emb[:n_next]
            nn = nn[:n_next]
            dist = dist[:n_next]
        if emb.shape[0] < 10:
            continue
        next_i = np.arange(emb.shape[0]) + m * tau
        next_nn = nn + m * tau
        valid = (next_nn < x.size) & (next_i < x.size) & np.isfinite(dist) & (dist > 1e-12)
        if valid.sum() < 10:
            continue
        R = np.abs(x[next_i[valid]] - x[next_nn[valid]]) / dist[valid]
        false = (R > rtol) | ((np.sqrt(dist[valid] ** 2 + (x[next_i[valid]] - x[next_nn[valid]]) ** 2) / ra) > atol)
        frac[m - 1] = float(false.mean())
    return frac


def choose_m_from_fnn(frac: np.ndarray, thresh: float = 0.1) -> int | None:
    """Smallest m with FNN fraction below thresh; else argmin."""
    if not np.isfinite(frac).any():
        return None
    for i, v in enumerate(frac):
        if np.isfinite(v) and v <= thresh:
            return i + 1
    return int(np.nanargmin(frac) + 1)


def classify_ami_curve(ami: np.ndarray) -> str:
    if not np.isfinite(ami).any():
        return "invalid"
    a = ami[np.isfinite(ami)]
    if a.size < 4:
        return "short"
    diffs = np.diff(a)
    sign_changes = np.sum(diffs[:-1] * diffs[1:] < 0)
    drop = a[0] - a[-1] if a[0] > 0 else 0
    if sign_changes >= 3 and drop < 0.3 * max(a[0], 1e-9):
        return "oscillatory"
    if first_local_minimum(ami) is not None and drop > 0.2 * max(a[0], 1e-9):
        # check if minimum is sharp
        return "clear_minimum_or_plateau"
    if drop < 0.15 * max(a[0], 1e-9):
        return "slow_decay"
    return "plateau_or_shallow"
