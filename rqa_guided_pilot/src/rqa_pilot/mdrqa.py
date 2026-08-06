"""Compact MdRQA on regional angular-velocity channels."""

from __future__ import annotations

import numpy as np

from .rqa_core import apply_theiler, quantify_rp, recurrence_matrix, threshold_for_target_rr


def mdrqa_metrics(
    channels: np.ndarray,
    *,
    theiler: int,
    lmin: int = 2,
    target_rr: float = 0.03,
) -> dict[str, float]:
    """channels: (T, C) already normalized. No additional delay embedding (state = multiregion vector)."""
    x = np.asarray(channels, dtype=np.float64)
    if x.ndim != 2 or x.shape[0] < 20:
        return {k: np.nan for k in ("RR", "DET", "Lmean", "Lmax", "Lmax_over_N", "ENTR", "LAM", "TT", "epsilon")}
    # pairwise distances in C-dimensional space
    g = x @ x.T
    sq = np.maximum(0.0, np.diag(g)[:, None] + np.diag(g)[None, :] - 2 * g)
    dist = np.sqrt(sq)
    dist_th = apply_theiler(dist, theiler)
    eps = threshold_for_target_rr(dist_th, target_rr)
    if not np.isfinite(eps):
        return {k: np.nan for k in ("RR", "DET", "Lmean", "Lmax", "Lmax_over_N", "ENTR", "LAM", "TT", "epsilon")}
    rp = recurrence_matrix(dist_th, eps)
    q = quantify_rp(rp, lmin=lmin, n_embed_total=x.shape[0])
    q["epsilon"] = float(eps)
    q["n_samples"] = float(x.shape[0])
    q["n_channels"] = float(x.shape[1])
    return q
