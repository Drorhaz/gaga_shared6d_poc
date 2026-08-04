"""Interpretable movement features for S5 (descriptive only)."""

from __future__ import annotations

import numpy as np
from scipy.stats import entropy


def _link_speed(rotvec_window: np.ndarray, fps: float) -> np.ndarray:
    """(T, L, 3) → (T-1, L) geodesic speed in deg/s between frames."""
    t, l, _ = rotvec_window.shape
    # Approximate geodesic step by rotvec finite-difference magnitude — accurate
    # for the small per-frame steps at 120 Hz and far cheaper than matrix geodesics
    # per link per frame.
    step = np.linalg.norm(np.diff(rotvec_window, axis=0), axis=2)  # (T-1, L) rad
    return np.degrees(step) * fps


def features_for_window(
    rotvec: np.ndarray,
    link_ids: list[str],
    regions: dict[str, str],
    mirror_pairs: list[list[str]],
    fps: float,
    active_quantile: float = 0.50,
) -> dict:
    """Compute one feature dict for a (T, L, 3) rotvec window."""
    speeds = _link_speed(rotvec, fps)  # (T-1, L)
    # energy per link: mean squared speed
    link_energy = np.nanmean(speeds ** 2, axis=0)
    link_energy = np.nan_to_num(link_energy, nan=0.0)
    total_energy = float(link_energy.sum())

    region_names = sorted(set(regions.values()))
    region_energy = {}
    for rname in region_names:
        idx = [i for i, lid in enumerate(link_ids) if regions[lid] == rname]
        region_energy[rname] = float(link_energy[idx].sum())

    # active links: above within-window median energy (or configured quantile)
    thr = float(np.quantile(link_energy, active_quantile)) if total_energy > 0 else 0.0
    active = link_energy >= thr
    if total_energy == 0:
        active = np.zeros_like(link_energy, dtype=bool)
    active_link_count = int(active.sum())
    active_regions = {
        r for r in region_names
        if any(active[i] for i, lid in enumerate(link_ids) if regions[lid] == r)
    }
    active_region_count = len(active_regions)

    # participation entropy over link energy shares
    shares = link_energy / total_energy if total_energy > 0 else np.ones(len(link_ids)) / len(link_ids)
    part_entropy = float(entropy(shares + 1e-12, base=2))

    # effective dimensionality (participation ratio)
    s2 = shares ** 2
    eff_dim = float(1.0 / s2.sum()) if s2.sum() > 0 else 0.0

    # L/R symmetry: 1 - mean relative energy difference over mirror pairs
    sym_terms = []
    for left, right in mirror_pairs:
        il, ir = link_ids.index(left), link_ids.index(right)
        a, b = link_energy[il], link_energy[ir]
        denom = a + b + 1e-12
        sym_terms.append(1.0 - abs(a - b) / denom)
    symmetry = float(np.mean(sym_terms)) if sym_terms else float("nan")

    # regional coupling: mean pairwise corr of regional speed time series
    reg_series = {}
    for rname in region_names:
        idx = [i for i, lid in enumerate(link_ids) if regions[lid] == rname]
        reg_series[rname] = np.nanmean(speeds[:, idx], axis=1)
    corrs = []
    rlist = list(region_names)
    for i in range(len(rlist)):
        for j in range(i + 1, len(rlist)):
            a, b = reg_series[rlist[i]], reg_series[rlist[j]]
            ok = np.isfinite(a) & np.isfinite(b)
            if ok.sum() > 5 and np.std(a[ok]) > 1e-12 and np.std(b[ok]) > 1e-12:
                corrs.append(float(np.corrcoef(a[ok], b[ok])[0, 1]))
    regional_coupling = float(np.mean(corrs)) if corrs else float("nan")

    # lagged coupling: max |corr| at lags ±1..5 frames between trunk and arms
    lagged = float("nan")
    if "trunk_spine" in reg_series and "left_arm" in reg_series:
        a = reg_series["trunk_spine"]
        b = 0.5 * (reg_series["left_arm"] + reg_series["right_arm"])
        best = 0.0
        for lag in range(-5, 6):
            if lag < 0:
                aa, bb = a[-lag:], b[:lag]
            elif lag > 0:
                aa, bb = a[:-lag], b[lag:]
            else:
                aa, bb = a, b
            ok = np.isfinite(aa) & np.isfinite(bb)
            if ok.sum() > 5 and np.std(aa[ok]) > 1e-12 and np.std(bb[ok]) > 1e-12:
                best = max(best, abs(float(np.corrcoef(aa[ok], bb[ok])[0, 1])))
        lagged = best

    out = {
        "total_energy_deg2_s2": total_energy,
        "active_link_count": active_link_count,
        "active_region_count": active_region_count,
        "participation_entropy_bits": part_entropy,
        "effective_dimensionality": eff_dim,
        "lr_symmetry": symmetry,
        "regional_coupling": regional_coupling,
        "trunk_arm_lagged_coupling": lagged,
    }
    for rname, val in region_energy.items():
        out[f"energy_{rname}"] = val
    # amplitude-controlled: energy shares and features residualised / normalised
    out["total_energy_log"] = float(np.log1p(total_energy))
    for rname, val in region_energy.items():
        out[f"energy_share_{rname}"] = val / total_energy if total_energy > 0 else 0.0
    return out
