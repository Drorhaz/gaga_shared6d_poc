#!/usr/bin/env python3
"""Stage 1 regional Auto-RQA for 651/790 × ex11/ex13 × T1/T3 × R1/R2."""

from __future__ import annotations

import json
from itertools import product

import numpy as np
import pandas as pd

import _bootstrap  # noqa: F401
from rqa_pilot.duration import min_length, truncate_to_length
from rqa_pilot.io_readonly import build_segment_index
from rqa_pilot.paths import ensure_rqa_dirs, load_pilot, rqa_path
from rqa_pilot.rqa_core import auto_rqa
from rqa_pilot.signals import downsample, finite_clean, normalize_series, regional_speed_series
from rqa_pilot.surrogates import make_surrogate


def _get_series(rec, region, rate, pilot, norm, n_trunc=None):
    s = regional_speed_series(
        rec.recording_id, int(rec.start_frame), int(rec.end_frame), region, pilot["native_fps"]
    )
    s = finite_clean(s)
    s = downsample(s, pilot["native_fps"], float(rate))
    s = finite_clean(s)
    if n_trunc is not None:
        s = truncate_to_length(s, n_trunc)
    s = normalize_series(s, norm)
    return s


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
    tau_band = [int(t) for t in lock["tau_band_frames_at_primary"]]
    target_rr = float(lock["threshold"]["target_rr"])
    radius_frac = float(lock["threshold"]["fixed_radius_frac_mean_dist_default"])

    segs = build_segment_index(pilot["stage1"]["exercises"])
    segs = segs[
        segs["participant"].isin(pilot["stage1"]["participants"])
        & segs["timepoint"].isin(pilot["stage1"]["timepoints"])
        & segs["repetition"].isin(pilot["stage1"]["repetitions"])
    ].reset_index(drop=True)

    rows = []
    # Precompute truncation lengths per pid×exercise (min across TP/reps at primary rate)
    trunc_map = {}
    for pid, ex in product(pilot["stage1"]["participants"], pilot["stage1"]["exercises"]):
        subset = segs[(segs.participant == pid) & (segs.exercise_id == ex)]
        lengths = []
        for rec in subset.itertuples(index=False):
            s = _get_series(rec, pilot["regions_primary"][0], rate, pilot, "amp_preserving")
            lengths.append(len(s))
        trunc_map[(pid, ex)] = int(min(lengths)) if lengths else 0

    settings = []
    # Primary settings
    for norm in pilot["normalization"]:
        mode = "fixed_mean_rescaled" if norm == "amp_preserving" else "target_rr"
        settings.append({"label": f"primary_{norm}", "norm": norm, "mode": mode, "tau": tau, "theiler": theiler, "trunc": False, "surrogate": "identity", "radius_frac": radius_frac})
    # Surrogates on amp-preserving primary
    for kind in ("full_shuffle", "block_shuffle"):
        settings.append({"label": f"surr_{kind}", "norm": "amp_preserving", "mode": "fixed_mean_rescaled", "tau": tau, "theiler": theiler, "trunc": False, "surrogate": kind, "radius_frac": radius_frac})
    # Duration truncation sensitivity
    settings.append({"label": "trunc_amp_preserving", "norm": "amp_preserving", "mode": "fixed_mean_rescaled", "tau": tau, "theiler": theiler, "trunc": True, "surrogate": "identity", "radius_frac": radius_frac})
    # Tau band / theiler sensitivity (amp-preserving)
    for t in tau_band:
        if t == tau:
            continue
        settings.append({"label": f"tau_{t}", "norm": "amp_preserving", "mode": "fixed_mean_rescaled", "tau": t, "theiler": t, "trunc": False, "surrogate": "identity", "radius_frac": radius_frac})
    settings.append({"label": "theiler_2tau", "norm": "amp_preserving", "mode": "fixed_mean_rescaled", "tau": tau, "theiler": 2 * tau, "trunc": False, "surrogate": "identity", "radius_frac": radius_frac})
    # Rate neighbor diagnostic (not primary): include 120 and 60 if different
    for alt_rate in pilot["rates_hz"]:
        if int(alt_rate) == rate:
            continue
        if int(alt_rate) == pilot["diagnostic_rate_hz"]:
            # limited diagnostic: only trunk on T1
            continue
        settings.append({
            "label": f"rate_{alt_rate}",
            "norm": "amp_preserving",
            "mode": "fixed_mean_rescaled",
            "tau": max(1, int(round(lock["tau_seconds"] * alt_rate))),
            "theiler": max(1, int(round(lock["tau_seconds"] * alt_rate))),
            "trunc": False,
            "surrogate": "identity",
            "radius_frac": radius_frac,
            "rate_hz": int(alt_rate),
        })

    for setting in settings:
        use_rate = int(setting.get("rate_hz", rate))
        for rec in segs.itertuples(index=False):
            # For non-primary rate settings, restrict to T1 to limit cost
            if "rate_hz" in setting and int(rec.timepoint) != 1:
                continue
            n_trunc = trunc_map[(str(rec.participant), int(rec.exercise_id))] if setting["trunc"] else None
            for region in pilot["regions_primary"]:
                s = _get_series(rec, region, use_rate, pilot, setting["norm"], n_trunc=n_trunc)
                if s.size < 30:
                    continue
                seed = (
                    int(rec.participant) * 100000
                    + int(rec.timepoint) * 10000
                    + int(rec.repetition) * 1000
                    + int(rec.exercise_id) * 100
                    + abs(hash(region)) % 97
                )
                y = make_surrogate(s, setting["surrogate"], block_len if use_rate == rate else max(2, int(round(lock["block_shuffle_seconds"] * use_rate))), seed)
                tag = (
                    f"{rec.segment_id}_{region}_{use_rate}_{setting['label']}_"
                    f"t{setting['tau']}_m{m}_{setting['norm']}_{setting['surrogate']}"
                )
                # Cache only identity primary embeddings to avoid multi-GB surrogate caches.
                use_cache = setting["surrogate"] == "identity" and "rate_" not in setting["label"]
                q = auto_rqa(
                    y,
                    tau=int(setting["tau"]),
                    m=m,
                    theiler=int(setting["theiler"]),
                    lmin=lmin,
                    mode=setting["mode"],
                    radius_frac=float(setting["radius_frac"]),
                    target_rr=target_rr,
                    cache_dir=rqa_path("cache") if use_cache else None,
                    cache_tag=tag if use_cache else None,
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
                        "rate_hz": use_rate,
                        "normalization": setting["norm"],
                        "threshold_mode": setting["mode"],
                        "surrogate": setting["surrogate"],
                        "truncated": bool(setting["trunc"]),
                        "duration_s": float(rec.duration_s),
                        "n_trunc": n_trunc if n_trunc is not None else -1,
                        **{k: q.get(k, np.nan) for k in (
                            "RR", "DET", "Lmean", "Lmax", "Lmax_over_N", "ENTR", "LAM", "TT",
                            "epsilon", "mean_distance", "n_samples", "N_embed", "tau", "m", "theiler", "lmin",
                        )},
                    }
                )

    df = pd.DataFrame(rows)
    out = rqa_path("outputs", "stage1", "auto_rqa_metrics.csv")
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    print(f"wrote {out} rows={len(df)}")


if __name__ == "__main__":
    main()
