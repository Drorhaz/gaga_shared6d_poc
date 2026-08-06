#!/usr/bin/env python3
"""Synthetic (+ optional T1) parity vs Pose-Dynamics / rqa-analysis backend.

Read-only validation. Does not retune Stage 1 locks.
Writes JSON under rqa_guided_pilot/outputs/paper_reference/.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
POSE = ROOT / "Pose-Dynamics-main" / "src"
sys.path.insert(0, str(SRC))
sys.path.insert(0, str(POSE))

from rqa_pilot.ami_fnn import (  # noqa: E402
    average_mutual_information,
    false_nearest_neighbors,
    first_local_minimum,
    choose_m_from_fnn,
)
from rqa_pilot.rqa_core import auto_rqa  # noqa: E402
from rqa_pilot.surrogates import full_shuffle, block_shuffle  # noqa: E402

OUT = ROOT / "outputs" / "paper_reference"
OUT.mkdir(parents=True, exist_ok=True)

TAU = 18
M = 4
LMIN = 2
THEILER = 18
RADIUS_FRAC = 0.35
# Backend: diag_ignore=tw zeros d=0..tw-1 → |i-j| < tw. Match theiler=18 → tw=19.
BACKEND_TW = THEILER + 1


def _paper_ami_fnn():
    from pose_dynamics.nonlinear import state_space_recon as ssr

    # silence tqdm in AMI/FNN
    import tqdm as tqdm_mod

    class _Dummy:
        def __init__(self, *a, **k):
            pass

        def __iter__(self):
            return iter(())

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def _tqdm(it, *a, **k):
        return it

    tqdm_mod.tqdm = _tqdm
    return ssr


def make_signals(n: int = 1200, seed: int = 0) -> dict[str, np.ndarray]:
    rng = np.random.default_rng(seed)
    t = np.arange(n, dtype=np.float64)
    sine = np.sin(2 * np.pi * t / 40.0)
    noisy = sine + 0.15 * rng.standard_normal(n)
    white = rng.standard_normal(n)
    const = np.full(n, 1.234)
    # repeated structured motif
    motif = np.array([0, 1, 2, 1, 0, -1, -2, -1], dtype=np.float64)
    structured = np.tile(motif, n // len(motif) + 1)[:n]
    out = {
        "periodic_sine": sine,
        "noisy_sine": noisy,
        "white_noise": white,
        "constant": const,
        "structured_sequence": structured,
    }
    out["sine_full_shuffle"] = full_shuffle(sine, rng)
    out["sine_block_shuffle"] = block_shuffle(sine, block_len=36, rng=rng)
    out["structured_full_shuffle"] = full_shuffle(structured, rng)
    return out


def our_rqa(x: np.ndarray) -> dict:
    return auto_rqa(
        x,
        tau=TAU,
        m=M,
        theiler=THEILER,
        lmin=LMIN,
        mode="fixed_mean_rescaled",
        radius_frac=RADIUS_FRAC,
    )


def backend_available():
    try:
        from rqa_analysis.utils import rqa_utils_cpp  # noqa: F401
        from rqa_analysis.utils import norm_utils  # noqa: F401

        return True
    except Exception as e:
        return False, str(e)


def backend_rqa(x: np.ndarray, rescale: int = 1, radius: float = RADIUS_FRAC) -> dict:
    from rqa_analysis.utils import rqa_utils_cpp, norm_utils

    xn = norm_utils.normalize_data(np.asarray(x, dtype=np.float32), 0)  # no norm
    ds = rqa_utils_cpp.rqa_dist(xn, xn, dim=M, lag=TAU)
    D = np.asarray(ds["d"], dtype=np.float32)
    td, rs, mats, err = rqa_utils_cpp.rqa_stats(
        D, rescale, float(radius), BACKEND_TW, LMIN, "auto"
    )
    return {
        "err_code": int(err),
        "RR": float(rs["perc_recur"]) / 100.0,
        "DET": float(rs["perc_determ"]) / 100.0,
        "Lmean": float(rs["mean_line_length"]),
        "Lmax": float(rs["maxl_found"]),
        "ENTR": float(rs["entropy"]),
        "LAM": float(rs["laminarity"]),
        "TT": float(rs["trapping_time"]),
        "rescale": int(rs["rescale"]),
        "rad": float(rs["rad"]),
        "diag_ignore": int(rs["diag_ignore"]),
    }


def ami_compare(x: np.ndarray, max_tau: int = 60) -> dict:
    ssr = _paper_ami_fnn()
    ours = average_mutual_information(x, max_tau=max_tau, n_bins=16)
    paper = ssr.ami(x, min_lag=1, max_lag=max_tau)
    if paper is None:
        return {"ours_tau": first_local_minimum(ours), "paper_tau": None, "corr": None}
    paper_ami = paper[:, 1]
    # align lengths
    n = min(len(ours), len(paper_ami))
    a, b = ours[:n], paper_ami[:n]
    mask = np.isfinite(a) & np.isfinite(b)
    corr = float(np.corrcoef(a[mask], b[mask])[0, 1]) if mask.sum() > 5 else None
    # paper first local min
    paper_tau = None
    for i in range(1, n - 1):
        if b[i] <= b[i - 1] and b[i] <= b[i + 1]:
            paper_tau = i + 1
            break
    return {
        "ours_tau": first_local_minimum(ours),
        "paper_tau": paper_tau,
        "curve_corr": corr,
        "ours_ami1": float(ours[0]) if np.isfinite(ours[0]) else None,
        "paper_ami1": float(b[0]) if np.isfinite(b[0]) else None,
    }


def fnn_compare(x: np.ndarray, tau: int = TAU, max_m: int = 8) -> dict:
    ssr = _paper_ami_fnn()
    ours = false_nearest_neighbors(x, tau=tau, max_m=max_m)
    dims, pct = ssr.fnn(x, tlag=tau, min_dimension=1, max_dimension=max_m)
    paper = np.asarray(pct, dtype=np.float64) / 100.0  # paper returns percent
    n = min(len(ours), len(paper))
    a, b = ours[:n], paper[:n]
    mask = np.isfinite(a) & np.isfinite(b)
    corr = float(np.corrcoef(a[mask], b[mask])[0, 1]) if mask.sum() > 3 else None
    return {
        "ours_m": choose_m_from_fnn(ours),
        "paper_m": choose_m_from_fnn(paper),
        "curve_corr": corr,
        "ours_frac": [None if not np.isfinite(v) else float(v) for v in ours],
        "paper_frac": [None if not np.isfinite(v) else float(v) for v in paper],
    }


def qualitative_expectations(metrics: dict[str, dict]) -> dict:
    """Check ordering without tuning."""
    notes = []
    ok = True
    det = {k: metrics[k].get("DET") for k in metrics}
    # periodic / structured should have higher DET than white noise / shuffles
    if np.isfinite(det.get("periodic_sine", np.nan)) and np.isfinite(det.get("white_noise", np.nan)):
        if not (det["periodic_sine"] > det["white_noise"]):
            ok = False
            notes.append("FAIL: sine DET not > white noise DET")
        else:
            notes.append("PASS: sine DET > white noise DET")
    if np.isfinite(det.get("structured_sequence", np.nan)) and np.isfinite(
        det.get("structured_full_shuffle", np.nan)
    ):
        if not (det["structured_sequence"] > det["structured_full_shuffle"]):
            ok = False
            notes.append("FAIL: structured DET not disrupted by full shuffle")
        else:
            notes.append("PASS: full shuffle reduces structured DET")
    if np.isfinite(det.get("periodic_sine", np.nan)) and np.isfinite(
        det.get("sine_full_shuffle", np.nan)
    ):
        if not (det["periodic_sine"] > det["sine_full_shuffle"]):
            ok = False
            notes.append("FAIL: sine DET not disrupted by full shuffle")
        else:
            notes.append("PASS: full shuffle reduces sine DET")
    # constant should be NaN or degenerate
    c = metrics.get("constant", {})
    if c and (not np.isfinite(c.get("DET", np.nan)) or c.get("RR", 1) in (0, 1) or True):
        notes.append(
            f"constant signal: RR={c.get('RR')} DET={c.get('DET')} (expect NaN/degenerate)"
        )
    return {"passed": ok, "notes": notes}


def rel_diff(a, b):
    if a is None or b is None:
        return None
    if not (np.isfinite(a) and np.isfinite(b)):
        return None
    denom = max(abs(a), abs(b), 1e-12)
    return float(abs(a - b) / denom)


def run_synthetic():
    signals = make_signals()
    has_backend = backend_available()
    if isinstance(has_backend, tuple):
        backend_ok, backend_err = False, has_backend[1]
    else:
        backend_ok, backend_err = True, None

    ami_results = {}
    fnn_results = {}
    our_metrics = {}
    be_metrics = {}
    parity = {}

    for name, x in signals.items():
        ami_results[name] = ami_compare(x)
        if name != "constant":
            fnn_results[name] = fnn_compare(x)
        else:
            fnn_results[name] = {"ours_m": None, "paper_m": None, "note": "constant skipped"}

        our_metrics[name] = {k: (None if isinstance(v, float) and not np.isfinite(v) else v)
                             for k, v in our_rqa(x).items()
                             if k in ("RR", "DET", "Lmean", "Lmax", "ENTR", "LAM", "TT", "epsilon", "mean_distance")}
        # cast numpy floats
        our_metrics[name] = {
            k: (float(v) if isinstance(v, (float, np.floating)) and np.isfinite(v) else None)
            for k, v in our_metrics[name].items()
        }

        if backend_ok:
            try:
                be_metrics[name] = backend_rqa(x, rescale=1, radius=RADIUS_FRAC)
            except Exception as e:
                be_metrics[name] = {"error": str(e)}
            if "error" not in be_metrics[name]:
                parity[name] = {
                    k: rel_diff(our_metrics[name].get(k), be_metrics[name].get(k))
                    for k in ("RR", "DET", "Lmean", "Lmax", "ENTR", "LAM", "TT")
                }

    # target-RR aligned comparison on sine (removes residual mean-definition mismatch)
    target_rr_parity = None
    if backend_ok:
        from rqa_pilot.rqa_core import (
            delay_embed,
            pairwise_distance_matrix,
            apply_theiler,
            threshold_for_target_rr,
            recurrence_matrix,
            quantify_rp,
        )
        from rqa_analysis.utils import rqa_utils_cpp, norm_utils

        x = signals["periodic_sine"]
        emb = delay_embed(x, TAU, M)
        dist = pairwise_distance_matrix(emb)
        dist_th = apply_theiler(dist, THEILER)
        target = 0.05
        eps = threshold_for_target_rr(dist_th, target)
        rp = recurrence_matrix(dist_th, eps)
        q = quantify_rp(rp, lmin=LMIN)
        # backend absolute threshold: rescale=0, rad=eps
        xn = norm_utils.normalize_data(np.asarray(x, dtype=np.float32), 0)
        ds = rqa_utils_cpp.rqa_dist(xn, xn, dim=M, lag=TAU)
        D = np.asarray(ds["d"], dtype=np.float32)
        td, rs, mats, err = rqa_utils_cpp.rqa_stats(D, 0, float(eps), BACKEND_TW, LMIN, "auto")
        be = {
            "RR": float(rs["perc_recur"]) / 100.0,
            "DET": float(rs["perc_determ"]) / 100.0,
            "Lmean": float(rs["mean_line_length"]),
            "Lmax": float(rs["maxl_found"]),
            "ENTR": float(rs["entropy"]),
            "LAM": float(rs["laminarity"]),
            "TT": float(rs["trapping_time"]),
            "err_code": int(err),
        }
        target_rr_parity = {
            "target_rr": target,
            "epsilon_absolute": float(eps),
            "ours": {k: float(q[k]) if np.isfinite(q[k]) else None for k in ("RR", "DET", "Lmean", "Lmax", "ENTR", "LAM", "TT")},
            "backend": be,
            "rel_diff": {k: rel_diff(float(q[k]), be[k]) for k in ("RR", "DET", "Lmean", "Lmax", "ENTR", "LAM", "TT")},
        }

    qual = qualitative_expectations(our_metrics)
    return {
        "backend_executed": backend_ok,
        "backend_error": backend_err,
        "params": {
            "tau": TAU,
            "m": M,
            "theiler_ours": THEILER,
            "backend_tw": BACKEND_TW,
            "lmin": LMIN,
            "radius_frac_mean": RADIUS_FRAC,
            "backend_rescale": 1,
            "note_rescale": "backend rescale=1 divides distances by mean (incl. diagonal zeros); Pose-Dynamics bool True→int 1 (mean), not max",
        },
        "ami": ami_results,
        "fnn": fnn_results,
        "our_rqa": our_metrics,
        "backend_rqa_mean_rescale": be_metrics,
        "rel_diff_mean_rescale": parity,
        "target_rr_absolute_threshold_parity": target_rr_parity,
        "qualitative": qual,
    }


def run_t1_subset(n_cells: int = 6):
    """Compare a few Stage-1 T1 amp-preserving cells under absolute-eps alignment."""
    import pandas as pd
    from rqa_pilot.io_readonly import build_segment_index
    from rqa_pilot.signals import finite_clean, regional_speed_series
    from rqa_pilot.rqa_core import (
        delay_embed,
        pairwise_distance_matrix,
        apply_theiler,
        threshold_from_mean_distance,
        recurrence_matrix,
        quantify_rp,
    )

    if not backend_available() or isinstance(backend_available(), tuple):
        return {"executed": False, "reason": "backend unavailable"}

    from rqa_analysis.utils import rqa_utils_cpp, norm_utils

    segs = build_segment_index([11, 13])
    segs = segs[(segs["participant"].isin(["651", "790"])) & (segs["timepoint"] == 1)]
    rows = []
    regions = ["trunk_spine", "left_arm", "right_arm"]
    count = 0
    for rec in segs.itertuples(index=False):
        for region in regions:
            if count >= n_cells:
                break
            x = finite_clean(
                regional_speed_series(
                    rec.recording_id, int(rec.start_frame), int(rec.end_frame), region, 120.0
                )
            )
            if x.size < 200:
                continue
            # ours
            o = our_rqa(x)
            emb = delay_embed(x, TAU, M)
            dist = pairwise_distance_matrix(emb)
            dist_th = apply_theiler(dist, THEILER)
            eps = threshold_from_mean_distance(dist_th, RADIUS_FRAC)
            # backend with absolute eps (rescale=0) for fair metric compare
            xn = norm_utils.normalize_data(np.asarray(x, dtype=np.float32), 0)
            ds = rqa_utils_cpp.rqa_dist(xn, xn, dim=M, lag=TAU)
            D = np.asarray(ds["d"], dtype=np.float32)
            td, rs, mats, err = rqa_utils_cpp.rqa_stats(
                D, 0, float(eps), BACKEND_TW, LMIN, "auto"
            )
            be = {
                "RR": float(rs["perc_recur"]) / 100.0,
                "DET": float(rs["perc_determ"]) / 100.0,
                "Lmean": float(rs["mean_line_length"]),
                "Lmax": float(rs["maxl_found"]),
                "ENTR": float(rs["entropy"]),
                "LAM": float(rs["laminarity"]),
                "TT": float(rs["trapping_time"]),
                "err": int(err),
            }
            rows.append(
                {
                    "segment_id": rec.segment_id,
                    "region": region,
                    "n": int(x.size),
                    "epsilon": float(eps),
                    "ours": {k: float(o[k]) if np.isfinite(o[k]) else None for k in ("RR", "DET", "Lmean", "Lmax", "ENTR", "LAM", "TT")},
                    "backend_abs_eps": be,
                    "rel_diff": {
                        k: rel_diff(float(o[k]) if np.isfinite(o[k]) else None, be[k])
                        for k in ("RR", "DET", "Lmean", "Lmax", "ENTR", "LAM", "TT")
                    },
                    # also report mean-rescale backend at same numeric radius (NOT equivalent by default)
                    "backend_mean_rescale_r035": backend_rqa(x, rescale=1, radius=RADIUS_FRAC),
                }
            )
            count += 1
        if count >= n_cells:
            break
    return {"executed": True, "n_cells": len(rows), "cells": rows}


def main():
    syn = run_synthetic()
    (OUT / "synthetic_parity.json").write_text(json.dumps(syn, indent=2))
    try:
        t1 = run_t1_subset(6)
    except Exception as e:
        t1 = {"executed": False, "reason": str(e)}
    (OUT / "t1_parity.json").write_text(json.dumps(t1, indent=2))
    print(json.dumps({"synthetic_qualitative": syn["qualitative"], "backend": syn["backend_executed"], "t1": t1.get("executed"), "t1_n": t1.get("n_cells")}, indent=2))


if __name__ == "__main__":
    main()
