"""Candidate A: regional angular-velocity magnitude series."""

from __future__ import annotations

import numpy as np

from .io_readonly import load_link_config, load_rotvec


def link_speed_deg_s(rotvec: np.ndarray, fps: float) -> np.ndarray:
    """(T, L, 3) → (T-1, L) speed in deg/s (matches explicit_features definition)."""
    step = np.linalg.norm(np.diff(rotvec, axis=0), axis=2)
    return np.degrees(step) * fps


def regional_speed_series(
    recording_id: str,
    start_frame: int,
    end_frame: int,
    region: str,
    native_fps: float = 120.0,
) -> np.ndarray:
    """Full-exercise regional mean angular-velocity magnitude at native fps."""
    link_ids, regions = load_link_config()
    idx = [i for i, lid in enumerate(link_ids) if regions[lid] == region]
    if not idx:
        raise KeyError(f"unknown region {region}")
    rv = load_rotvec(recording_id)[start_frame:end_frame]
    if rv.shape[0] < 3:
        return np.asarray([], dtype=np.float64)
    speeds = link_speed_deg_s(rv, native_fps)  # (T-1, L)
    series = np.nanmean(speeds[:, idx], axis=1)
    return series.astype(np.float64)


def downsample(series: np.ndarray, native_fps: float, target_fps: float) -> np.ndarray:
    """Integer-factor downsample by stride (no re-filtering)."""
    if target_fps > native_fps:
        raise ValueError("target_fps cannot exceed native_fps")
    factor = int(round(native_fps / target_fps))
    if abs(native_fps / factor - target_fps) > 1e-6:
        raise ValueError(f"non-integer downsample {native_fps}->{target_fps}")
    return series[::factor].copy()


def normalize_series(series: np.ndarray, mode: str) -> np.ndarray:
    x = np.asarray(series, dtype=np.float64)
    if mode == "amp_preserving":
        return x.copy()
    if mode == "trial_zscore":
        mu = np.nanmean(x)
        sd = np.nanstd(x)
        if not np.isfinite(sd) or sd < 1e-12:
            return np.zeros_like(x)
        return (x - mu) / sd
    raise ValueError(mode)


def finite_clean(series: np.ndarray) -> np.ndarray:
    """Drop leading/trailing NaNs; require contiguous finite interior."""
    x = np.asarray(series, dtype=np.float64)
    ok = np.isfinite(x)
    if ok.sum() < 10:
        return np.asarray([], dtype=np.float64)
    # If interior gaps exist, keep only longest finite run
    if not ok.all():
        # mark runs
        padded = np.concatenate([[False], ok, [False]])
        edges = np.diff(padded.astype(int))
        starts = np.where(edges == 1)[0]
        ends = np.where(edges == -1)[0]
        lengths = ends - starts
        i = int(np.argmax(lengths))
        x = x[starts[i]:ends[i]]
    return x[np.isfinite(x)]
