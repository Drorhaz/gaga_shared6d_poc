#!/usr/bin/env python3
"""Lock common (tau, m), block length, and primary rate from T1-only evidence."""

from __future__ import annotations

import json
from itertools import product

import numpy as np
import pandas as pd

import _bootstrap  # noqa: F401
from rqa_pilot.io_readonly import build_segment_index
from rqa_pilot.paths import ensure_rqa_dirs, load_pilot, rqa_path
from rqa_pilot.rqa_core import auto_rqa
from rqa_pilot.signals import downsample, finite_clean, normalize_series, regional_speed_series
from rqa_pilot.surrogates import make_surrogate


def _series(rec, region, rate, pilot):
    s = regional_speed_series(
        rec.recording_id, int(rec.start_frame), int(rec.end_frame), region, pilot["native_fps"]
    )
    s = finite_clean(s)
    s = downsample(s, pilot["native_fps"], float(rate))
    return finite_clean(s)


def main() -> None:
    ensure_rqa_dirs()
    pilot = load_pilot()
    agg = json.loads(rqa_path("outputs", "t1_diagnostics", "ami_fnn_aggregate.json").read_text())

    # Common m: max of proposed commons across rates (upper end)
    m_common = int(max(v["m_common_proposed"] for v in agg.values()))
    m_common = int(np.clip(m_common, 3, 5))

    # Prefer tau band in seconds from 60 Hz aggregate if present else median across rates
    prefer_rate = "60" if "60" in agg else sorted(agg.keys())[0]
    tau_seconds = float(agg[prefer_rate]["tau_median_seconds"])
    block_s = float(np.median([v["block_shuffle_seconds_proposed"] for v in agg.values()]))

    segs = build_segment_index(pilot["stage1"]["exercises"])
    segs = segs[
        segs["participant"].isin(pilot["stage1"]["participants"])
        & segs["timepoint"].eq(1)
        & segs["repetition"].isin([1, 2])
    ]

    bake_rows = []
    regions = pilot["regions_primary"][:3]  # trunk + arms for rate bake-off speed
    for rate in pilot["rates_hz"]:
        tau = max(1, int(round(tau_seconds * rate)))
        theiler = tau
        block_len = max(2, int(round(block_s * rate)))
        mode = "fixed_mean_rescaled"
        for pid, ex, region in product(pilot["stage1"]["participants"], pilot["stage1"]["exercises"], regions):
            pair = segs[(segs.participant == pid) & (segs.exercise_id == ex)]
            if set(pair.repetition.tolist()) != {1, 2}:
                continue
            mets = {}
            for rep in (1, 2):
                rec = pair[pair.repetition == rep].iloc[0]
                s = normalize_series(_series(rec, region, rate, pilot), "amp_preserving")
                if s.size < 40:
                    continue
                for kind in ("identity", "full_shuffle"):
                    y = make_surrogate(s, kind, block_len, seed=1000 + rep)
                    # unique cache tags avoid collisions across surrogates
                    tag = f"{pid}_T1_R{rep}_ex{ex}_{region}_{rate}_{kind}"
                    q = auto_rqa(
                        y,
                        tau=tau,
                        m=m_common,
                        theiler=theiler,
                        lmin=pilot["lmin_default"],
                        mode=mode,
                        radius_frac=0.35,
                        cache_dir=rqa_path("cache"),
                        cache_tag=tag,
                    )
                    mets[(rep, kind)] = q
            if (1, "identity") not in mets or (2, "identity") not in mets:
                continue
            drep_det = abs(mets[(1, "identity")]["DET"] - mets[(2, "identity")]["DET"])
            drep_lam = abs(mets[(1, "identity")]["LAM"] - mets[(2, "identity")]["LAM"])
            # surrogate disruption: mean DET drop
            drops = []
            for rep in (1, 2):
                if (rep, "full_shuffle") in mets and np.isfinite(mets[(rep, "identity")]["DET"]):
                    drops.append(mets[(rep, "identity")]["DET"] - mets[(rep, "full_shuffle")]["DET"])
            bake_rows.append(
                {
                    "rate_hz": rate,
                    "participant": pid,
                    "exercise_id": ex,
                    "region": region,
                    "tau_frames": tau,
                    "m": m_common,
                    "drep_DET": drep_det,
                    "drep_LAM": drep_lam,
                    "mean_DET_drop_shuffle": float(np.nanmean(drops)) if drops else np.nan,
                    "RR_R1": mets[(1, "identity")]["RR"],
                    "DET_R1": mets[(1, "identity")]["DET"],
                    "n_samples": mets[(1, "identity")].get("n_samples", np.nan),
                }
            )

    bake = pd.DataFrame(bake_rows)
    bake_path = rqa_path("outputs", "t1_diagnostics", "rate_bakeoff_t1.csv")
    bake.to_csv(bake_path, index=False)

    # Score rates: prefer high surrogate DET drop, moderate RR, low Drep DET, and not diagnostic-only unless needed
    scores = {}
    for rate, sub in bake.groupby("rate_hz"):
        rr = sub["RR_R1"].median()
        rr_ok = float((rr >= pilot["threshold"]["rr_diagnostic_lo"]) and (rr <= pilot["threshold"]["rr_diagnostic_hi"]))
        # soft score if outside: still usable
        rr_pen = 0.0 if rr_ok else -0.5
        scores[int(rate)] = {
            "median_DET_drop_shuffle": float(sub["mean_DET_drop_shuffle"].median()),
            "median_drep_DET": float(sub["drep_DET"].median()),
            "median_RR": float(rr),
            "median_n_samples": float(sub["n_samples"].median()),
            "score": float(
                sub["mean_DET_drop_shuffle"].median()
                - 0.5 * sub["drep_DET"].median()
                + rr_pen
                - (0.25 if int(rate) == pilot["diagnostic_rate_hz"] else 0.0)
            ),
        }

    # Choose best non-diagnostic if competitive; else best overall
    primary = max(scores.keys(), key=lambda r: scores[r]["score"])
    if primary == pilot["diagnostic_rate_hz"]:
        alts = [r for r in scores if r != pilot["diagnostic_rate_hz"]]
        if alts:
            primary = max(alts, key=lambda r: scores[r]["score"])

    tau_frames = max(1, int(round(tau_seconds * primary)))
    tau_band = sorted(
        {
            max(1, tau_frames - 1),
            tau_frames,
            tau_frames + 1,
        }
    )

    lock = {
        "locked_from": "T1-only AMI/FNN + Stage1-T1 rate bake-off",
        "primary_rate_hz": int(primary),
        "diagnostic_rate_hz": int(pilot["diagnostic_rate_hz"]),
        "rates_compared_hz": list(pilot["rates_hz"]),
        "tau_seconds": tau_seconds,
        "tau_frames_at_primary": tau_frames,
        "tau_band_frames_at_primary": tau_band,
        "m": m_common,
        "theiler_default": tau_frames,
        "lmin_default": int(pilot["lmin_default"]),
        "block_shuffle_seconds": block_s,
        "block_shuffle_frames_at_primary": max(2, int(round(block_s * primary))),
        "threshold": {
            "amp_preserving_auto": "fixed_mean_rescaled",
            "fixed_radius_frac_mean_dist_default": 0.20,
            "trial_zscore_auto": "target_rr",
            "target_rr": float(pilot["threshold"]["target_rr"]),
        },
        "rate_scores": {str(k): v for k, v in scores.items()},
        "ami_fnn_aggregate_prefer_rate": prefer_rate,
        "interpretation": pilot["interpretation"],
    }
    lock_path = rqa_path("outputs", "locks", "parameter_lock_stage1.json")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_text(json.dumps(lock, indent=2))
    print(f"wrote {bake_path}")
    print(f"wrote {lock_path} primary_rate={primary} tau={tau_frames} m={m_common}")


if __name__ == "__main__":
    main()
