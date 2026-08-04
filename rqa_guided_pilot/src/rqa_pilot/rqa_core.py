"""Auto-RQA metrics with distance-matrix reuse."""

from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
from scipy.stats import entropy as scipy_entropy

from .embedding import delay_embed, n_embed


def _cache_key(tag: str, tau: int, m: int, n: int) -> str:
    h = hashlib.sha1(tag.encode()).hexdigest()[:16]
    return f"dist_{h}_tau{tau}_m{m}_n{n}.npy"


def pairwise_distance_matrix(
    emb: np.ndarray,
    cache_dir: Path | None = None,
    cache_tag: str | None = None,
    tau: int = 1,
    m: int = 1,
) -> np.ndarray:
    """Float Euclidean pairwise distances; optionally cached under rqa cache/."""
    if emb.ndim != 2 or emb.shape[0] < 5:
        return np.zeros((0, 0), dtype=np.float64)
    path = None
    if cache_dir is not None and cache_tag is not None:
        cache_dir.mkdir(parents=True, exist_ok=True)
        path = cache_dir / _cache_key(cache_tag, tau, m, emb.shape[0])
        if path.exists():
            return np.load(path)
    # (N,N) distances
    # using squared then sqrt for stability
    g = emb @ emb.T
    sq = np.maximum(0.0, np.diag(g)[:, None] + np.diag(g)[None, :] - 2.0 * g)
    dist = np.sqrt(sq, dtype=np.float64)
    np.fill_diagonal(dist, 0.0)
    if path is not None:
        # Persist float32 to limit cache size; compute in float64.
        np.save(path, dist.astype(np.float32))
    return dist


def apply_theiler(dist: np.ndarray, theiler: int) -> np.ndarray:
    """Return a copy with |i-j| <= theiler set to +inf (excluded)."""
    out = dist.copy()
    n = out.shape[0]
    if theiler <= 0:
        np.fill_diagonal(out, np.inf)
        return out
    for k in range(-theiler, theiler + 1):
        i = np.arange(max(0, -k), min(n, n - k))
        out[i, i + k] = np.inf
    return out


def threshold_from_mean_distance(dist_th: np.ndarray, frac: float) -> float:
    finite = dist_th[np.isfinite(dist_th)]
    if finite.size == 0:
        return np.nan
    return float(frac * np.mean(finite))


def threshold_for_target_rr(dist_th: np.ndarray, target_rr: float) -> float:
    finite = dist_th[np.isfinite(dist_th)]
    if finite.size < 10:
        return np.nan
    # off-diagonal only already via theiler
    return float(np.quantile(finite, target_rr))


def recurrence_matrix(dist_th: np.ndarray, eps: float) -> np.ndarray:
    rp = np.zeros(dist_th.shape, dtype=bool)
    finite = np.isfinite(dist_th)
    rp[finite] = dist_th[finite] <= eps
    return rp


def _line_lengths(rp: np.ndarray, axis: str, lmin: int) -> np.ndarray:
    """Extract diagonal (axis='diag') or vertical (axis='vert') line lengths >= lmin."""
    n = rp.shape[0]
    lengths: list[int] = []
    if axis == "diag":
        # diagonals with offset k = j-i, k>0 (upper) and skip main
        for k in range(1, n):
            diag = np.diag(rp, k=k)
            lengths.extend(_run_lengths(diag, lmin))
        # lower triangle mirrors for Auto-RQA; count once only (upper)
    elif axis == "vert":
        for j in range(n):
            lengths.extend(_run_lengths(rp[:, j], lmin))
    else:
        raise ValueError(axis)
    return np.asarray(lengths, dtype=np.int32) if lengths else np.asarray([], dtype=np.int32)


def _run_lengths(mask: np.ndarray, lmin: int) -> list[int]:
    out: list[int] = []
    run = 0
    for v in mask:
        if v:
            run += 1
        elif run:
            if run >= lmin:
                out.append(run)
            run = 0
    if run >= lmin:
        out.append(run)
    return out


def quantify_rp(
    rp: np.ndarray,
    lmin: int = 2,
    n_embed_total: int | None = None,
) -> dict[str, float]:
    n = rp.shape[0]
    # exclude impossible theiler-masked already False
    # number of possible points: all off those already false — use all pairs except we count True
    # For RR use fraction of True among finite-eligible pairs. Here RP already has Theiler as False.
    # Count all off-diagonal cells as denominator (standard Auto-RQA with Theiler zeros).
    denom = n * n - n  # exclude main diagonal cells (also false)
    # but Theiler band wider than 1 already zeroed — still count those zeros in denom (standard)
    n_rec = int(rp.sum())
    # subtract diagonal if any True slipped
    n_rec -= int(np.diag(rp).sum())
    rr = n_rec / denom if denom > 0 else np.nan

    diag_lens = _line_lengths(rp, "diag", lmin)
    # Auto-RQA is symmetric; upper triangle diagonals counted once; recurrent points on both triangles
    # Standard DET uses all recurrent points on diagonals / all recurrent points.
    # Because we only scanned upper diagonals, double diag point count for symmetry:
    diag_points = int(diag_lens.sum()) * 2 if diag_lens.size else 0
    # vertical lines: full matrix
    vert_lens = _line_lengths(rp, "vert", lmin)
    vert_points = int(vert_lens.sum()) if vert_lens.size else 0

    # Clamp diag_points to n_rec
    diag_points = min(diag_points, n_rec) if n_rec else 0
    det = diag_points / n_rec if n_rec > 0 else np.nan
    lam = vert_points / n_rec if n_rec > 0 else np.nan
    lmean = float(diag_lens.mean()) if diag_lens.size else np.nan
    lmax = float(diag_lens.max()) if diag_lens.size else np.nan
    tt = float(vert_lens.mean()) if vert_lens.size else np.nan
    if diag_lens.size:
        # Shannon entropy of diagonal line length histogram
        counts = np.bincount(diag_lens)
        probs = counts[counts > 0] / counts[counts > 0].sum()
        entr = float(scipy_entropy(probs, base=2))
    else:
        entr = np.nan
    n_emb = n_embed_total if n_embed_total is not None else n
    return {
        "RR": float(rr),
        "DET": float(det),
        "Lmean": float(lmean),
        "Lmax": float(lmax),
        "Lmax_over_N": float(lmax / n_emb) if n_emb and np.isfinite(lmax) else np.nan,
        "ENTR": float(entr),
        "LAM": float(lam),
        "TT": float(tt),
        "n_rec": float(n_rec),
        "N_embed": float(n),
    }


def auto_rqa(
    series: np.ndarray,
    tau: int,
    m: int,
    *,
    theiler: int | None = None,
    lmin: int = 2,
    mode: str = "fixed_mean_rescaled",
    radius_frac: float = 0.20,
    target_rr: float = 0.03,
    cache_dir: Path | None = None,
    cache_tag: str | None = None,
) -> dict[str, float]:
    """Compute Auto-RQA metrics for one scalar series."""
    x = np.asarray(series, dtype=np.float64).ravel()
    emb = delay_embed(x, tau, m)
    if emb.shape[0] < 10:
        return {k: np.nan for k in ("RR", "DET", "Lmean", "Lmax", "Lmax_over_N", "ENTR", "LAM", "TT", "epsilon", "mean_distance")}
    dist = pairwise_distance_matrix(emb, cache_dir=cache_dir, cache_tag=cache_tag, tau=tau, m=m)
    th = theiler if theiler is not None else tau
    dist_th = apply_theiler(dist, th)
    finite = dist_th[np.isfinite(dist_th)]
    mean_d = float(np.mean(finite)) if finite.size else np.nan
    if mode == "fixed_mean_rescaled":
        eps = threshold_from_mean_distance(dist_th, radius_frac)
    elif mode == "target_rr":
        eps = threshold_for_target_rr(dist_th, target_rr)
    else:
        raise ValueError(mode)
    if not np.isfinite(eps):
        out = {k: np.nan for k in ("RR", "DET", "Lmean", "Lmax", "Lmax_over_N", "ENTR", "LAM", "TT")}
        out.update({"epsilon": np.nan, "mean_distance": mean_d, "n_samples": float(x.size)})
        return out
    rp = recurrence_matrix(dist_th, eps)
    q = quantify_rp(rp, lmin=lmin, n_embed_total=emb.shape[0])
    q["epsilon"] = float(eps)
    q["mean_distance"] = mean_d
    q["n_samples"] = float(x.size)
    q["tau"] = float(tau)
    q["m"] = float(m)
    q["theiler"] = float(th)
    q["lmin"] = float(lmin)
    q["threshold_mode"] = 0.0 if mode == "fixed_mean_rescaled" else 1.0
    return q


def expected_n_embed(n_samples: int, tau: int, m: int) -> int:
    return n_embed(n_samples, tau, m)
