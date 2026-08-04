#!/usr/bin/env python3
"""Stage 2 secondary: compact MdRQA + optional trunk–arm CRQA (locked params)."""

from __future__ import annotations

import json

import numpy as np
import pandas as pd

import _bootstrap  # noqa: F401
from rqa_pilot.io_readonly import build_segment_index
from rqa_pilot.mdrqa import mdrqa_metrics
from rqa_pilot.paths import ensure_rqa_dirs, load_pilot, rqa_path
from rqa_pilot.rqa_core import auto_rqa, apply_theiler, pairwise_distance_matrix, quantify_rp, recurrence_matrix, threshold_for_target_rr
from rqa_pilot.signals import downsample, finite_clean, normalize_series, regional_speed_series
from rqa_pilot.surrogates import make_surrogate
from rqa_pilot.embedding import delay_embed


def _reg(rec, region, rate, pilot):
    s = regional_speed_series(rec.recording_id, int(rec.start_frame), int(rec.end_frame), region, pilot["native_fps"])
    return finite_clean(downsample(finite_clean(s), pilot["native_fps"], float(rate)))


def crqa_pair(x: np.ndarray, y: np.ndarray, tau: int, m: int, theiler: int, target_rr: float, lmin: int) -> dict:
    """CRQA between two scalar series with shared embedding params; target-RR."""
    xe = delay_embed(x, tau, m)
    ye = delay_embed(y, tau, m)
    n = min(len(xe), len(ye))
    if n < 20:
        return {k: np.nan for k in ("RR", "DET", "Lmean", "LAM", "ENTR", "epsilon")}
    xe, ye = xe[:n], ye[:n]
    # pairwise cross distances
    # ||xe_i - ye_j||
    d = np.sqrt(np.maximum(0.0, np.sum(xe**2, axis=1)[:, None] + np.sum(ye**2, axis=1)[None, :] - 2 * xe @ ye.T))
    # Theiler-like exclusion on |i-j|
    dist_th = apply_theiler(d, theiler)
    eps = threshold_for_target_rr(dist_th, target_rr)
    if not np.isfinite(eps):
        return {k: np.nan for k in ("RR", "DET", "Lmean", "LAM", "ENTR", "epsilon")}
    rp = recurrence_matrix(dist_th, eps)
    q = quantify_rp(rp, lmin=lmin, n_embed_total=n)
    q["epsilon"] = float(eps)
    return q


def main() -> None:
    ensure_rqa_dirs()
    pilot = load_pilot()
    lock = json.loads(rqa_path("outputs", "locks", "parameter_lock_stage1.json").read_text())
    rate = int(lock["primary_rate_hz"])
    tau = int(lock["tau_frames_at_primary"])
    m = int(lock["m"])
    theiler = int(lock["theiler_default"])
    lmin = int(lock["lmin_default"])
    target_rr = float(lock["threshold"]["target_rr"])
    block_len = int(lock["block_shuffle_frames_at_primary"])
    regions = ["trunk_spine", "left_arm", "right_arm", "left_leg", "right_leg"]

    segs = build_segment_index([11, 13])
    segs = segs[segs.participant.isin(["651", "790"]) & segs.timepoint.isin([1, 2, 3]) & segs.repetition.isin([1, 2])]

    md_rows = []
    cr_rows = []
    for rec in segs.itertuples(index=False):
        chans = []
        ok = True
        series_map = {}
        for region in regions:
            s = _reg(rec, region, rate, pilot)
            if s.size < 40:
                ok = False
                break
            series_map[region] = s
        if not ok:
            continue
        # align lengths
        n = min(len(series_map[r]) for r in regions)
        mat = np.column_stack([normalize_series(series_map[r][:n], "trial_zscore") for r in regions])
        q = mdrqa_metrics(mat, theiler=theiler, lmin=lmin, target_rr=target_rr)
        q_shuf = mdrqa_metrics(
            np.column_stack([make_surrogate(mat[:, i], "full_shuffle", block_len, seed=10 + i) for i in range(mat.shape[1])]),
            theiler=theiler,
            lmin=lmin,
            target_rr=target_rr,
        )
        md_rows.append(
            {
                "participant": str(rec.participant),
                "timepoint": int(rec.timepoint),
                "repetition": int(rec.repetition),
                "exercise_id": int(rec.exercise_id),
                "duration_s": float(rec.duration_s),
                "surrogate": "identity",
                **{k: q.get(k, np.nan) for k in ("RR", "DET", "Lmean", "Lmax_over_N", "ENTR", "LAM", "TT", "epsilon", "n_samples")},
                "DET_shuf": q_shuf.get("DET", np.nan),
                "LAM_shuf": q_shuf.get("LAM", np.nan),
            }
        )

        # CRQA trunk vs mean arms
        trunk = normalize_series(series_map["trunk_spine"][:n], "trial_zscore")
        arms = normalize_series(0.5 * (series_map["left_arm"][:n] + series_map["right_arm"][:n]), "trial_zscore")
        cq = crqa_pair(trunk, arms, tau, m, theiler, target_rr, lmin)
        cq_s = crqa_pair(make_surrogate(trunk, "full_shuffle", block_len, seed=99), arms, tau, m, theiler, target_rr, lmin)
        cr_rows.append(
            {
                "participant": str(rec.participant),
                "timepoint": int(rec.timepoint),
                "repetition": int(rec.repetition),
                "exercise_id": int(rec.exercise_id),
                "duration_s": float(rec.duration_s),
                **{k: cq.get(k, np.nan) for k in ("RR", "DET", "Lmean", "LAM", "ENTR", "epsilon")},
                "DET_shuf_one": cq_s.get("DET", np.nan),
                "LAM_shuf_one": cq_s.get("LAM", np.nan),
            }
        )

    pd.DataFrame(md_rows).to_csv(rqa_path("outputs", "stage2", "compact_mdrqa.csv"), index=False)
    pd.DataFrame(cr_rows).to_csv(rqa_path("outputs", "stage2", "crqa_trunk_arms.csv"), index=False)
    print(f"MdRQA rows={len(md_rows)} CRQA rows={len(cr_rows)}")


if __name__ == "__main__":
    main()
