#!/usr/bin/env python3
"""Stage 2 regional Auto-RQA: 651/790 × ex11/ex13 × T1/T2/T3 × R1/R2 (locked params)."""

from __future__ import annotations

import json
from itertools import product

import numpy as np
import pandas as pd

import _bootstrap  # noqa: F401
from rqa_pilot.duration import truncate_to_length
from rqa_pilot.io_readonly import build_segment_index
from rqa_pilot.paths import ensure_rqa_dirs, load_pilot, rqa_path
from rqa_pilot.rqa_core import auto_rqa
from rqa_pilot.signals import downsample, finite_clean, normalize_series, regional_speed_series
from rqa_pilot.surrogates import make_surrogate


def _series(rec, region, rate, pilot, norm, n_trunc=None):
    s = regional_speed_series(
        rec.recording_id, int(rec.start_frame), int(rec.end_frame), region, pilot["native_fps"]
    )
    s = finite_clean(downsample(finite_clean(s), pilot["native_fps"], float(rate)))
    if n_trunc is not None:
        s = truncate_to_length(s, n_trunc)
    return normalize_series(s, norm)


def main() -> None:
    ensure_rqa_dirs()
    pilot = load_pilot()
    lock = json.loads(rqa_path("outputs", "locks", "parameter_lock_stage1.json").read_text())
    rate = int(lock["primary_rate_hz"])
    tau = int(lock["tau_frames_at_primary"])
    m = int(lock["m"])
    theiler = int(lock["theiler_default"])
    lmin = int(lock["lmin_default"])
    block_len = int(lock["block_shuffle_frames_at_primary"])
    radius = float(lock["threshold"]["fixed_radius_frac_mean_dist_default"])
    target_rr = float(lock["threshold"]["target_rr"])
    tau_band = [int(x) for x in lock["tau_band_frames_at_primary"]]

    segs = build_segment_index([11, 13])
    segs = segs[
        segs["participant"].isin(["651", "790"])
        & segs["timepoint"].isin([1, 2, 3])
        & segs["repetition"].isin([1, 2])
    ].reset_index(drop=True)

    trunc_map = {}
    for pid, ex in product(["651", "790"], [11, 13]):
        lengths = []
        for rec in segs[(segs.participant == pid) & (segs.exercise_id == ex)].itertuples(index=False):
            lengths.append(len(_series(rec, "trunk_spine", rate, pilot, "amp_preserving")))
        trunc_map[(pid, ex)] = int(min(lengths)) if lengths else 0

    settings = []
    for norm in ("amp_preserving", "trial_zscore"):
        mode = "fixed_mean_rescaled" if norm == "amp_preserving" else "target_rr"
        settings.append(dict(label=f"primary_{norm}", norm=norm, mode=mode, tau=tau, theiler=theiler, lmin=lmin, trunc=False, surr="identity", radius=radius))
    for kind in ("full_shuffle", "block_shuffle"):
        settings.append(dict(label=f"surr_{kind}", norm="amp_preserving", mode="fixed_mean_rescaled", tau=tau, theiler=theiler, lmin=lmin, trunc=False, surr=kind, radius=radius))
    settings.append(dict(label="trunc_amp_preserving", norm="amp_preserving", mode="fixed_mean_rescaled", tau=tau, theiler=theiler, lmin=lmin, trunc=True, surr="identity", radius=radius))
    settings.append(dict(label="lmin3_amp_preserving", norm="amp_preserving", mode="fixed_mean_rescaled", tau=tau, theiler=theiler, lmin=3, trunc=False, surr="identity", radius=radius))
    for t in tau_band:
        if t == tau:
            continue
        settings.append(dict(label=f"tau_{t}", norm="amp_preserving", mode="fixed_mean_rescaled", tau=t, theiler=t, lmin=lmin, trunc=False, surr="identity", radius=radius))
    for rf in (0.30, 0.40):
        settings.append(dict(label=f"radius_{rf}", norm="amp_preserving", mode="fixed_mean_rescaled", tau=tau, theiler=theiler, lmin=lmin, trunc=False, surr="identity", radius=rf))

    rows = []
    for setting in settings:
        for rec in segs.itertuples(index=False):
            n_trunc = trunc_map[(str(rec.participant), int(rec.exercise_id))] if setting["trunc"] else None
            for region in pilot["regions_primary"]:
                s = _series(rec, region, rate, pilot, setting["norm"], n_trunc)
                if s.size < 30:
                    continue
                seed = (
                    int(rec.participant) * 100000
                    + int(rec.timepoint) * 10000
                    + int(rec.repetition) * 1000
                    + int(rec.exercise_id) * 100
                    + abs(hash(region)) % 97
                )
                y = make_surrogate(s, setting["surr"], block_len, seed)
                q = auto_rqa(
                    y,
                    tau=int(setting["tau"]),
                    m=m,
                    theiler=int(setting["theiler"]),
                    lmin=int(setting["lmin"]),
                    mode=setting["mode"],
                    radius_frac=float(setting["radius"]),
                    target_rr=target_rr,
                )
                rows.append(
                    {
                        "setting": setting["label"],
                        "participant": str(rec.participant),
                        "timepoint": int(rec.timepoint),
                        "repetition": int(rec.repetition),
                        "exercise_id": int(rec.exercise_id),
                        "recording_id": rec.recording_id,
                        "segment_id": rec.segment_id,
                        "region": region,
                        "rate_hz": rate,
                        "normalization": setting["norm"],
                        "threshold_mode": setting["mode"],
                        "surrogate": setting["surr"],
                        "truncated": bool(setting["trunc"]),
                        "duration_s": float(rec.duration_s),
                        "n_trunc": n_trunc if n_trunc is not None else -1,
                        **{
                            k: q.get(k, np.nan)
                            for k in (
                                "RR", "DET", "Lmean", "Lmax", "Lmax_over_N", "ENTR", "LAM", "TT",
                                "epsilon", "mean_distance", "n_samples", "N_embed", "tau", "m", "theiler", "lmin",
                            )
                        },
                        "Lmean_s": (q["Lmean"] / rate) if np.isfinite(q.get("Lmean", np.nan)) else np.nan,
                    }
                )

    out = rqa_path("outputs", "stage2", "auto_rqa_metrics.csv")
    out.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(out, index=False)
    print(f"wrote {out} rows={len(rows)}")


if __name__ == "__main__":
    main()
