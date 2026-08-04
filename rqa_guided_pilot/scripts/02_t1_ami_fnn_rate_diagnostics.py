#!/usr/bin/env python3
"""T1-only AMI / ACF / FNN diagnostics across all participants and rates."""

from __future__ import annotations

import json

import numpy as np
import pandas as pd

import _bootstrap  # noqa: F401
from rqa_pilot.ami_fnn import (
    autocorrelation,
    average_mutual_information,
    choose_m_from_fnn,
    classify_ami_curve,
    false_nearest_neighbors,
    first_acf_zero,
    first_local_minimum,
)
from rqa_pilot.io_readonly import build_segment_index
from rqa_pilot.paths import ensure_rqa_dirs, load_pilot, rqa_path
from rqa_pilot.signals import downsample, finite_clean, regional_speed_series


def main() -> None:
    ensure_rqa_dirs()
    pilot = load_pilot()
    cfg = pilot["ami_fnn"]
    segs = build_segment_index(cfg["exercises"])
    segs = segs[
        segs["participant"].isin(cfg["participants"])
        & segs["timepoint"].isin(cfg["timepoints"])
        & segs["repetition"].isin(cfg["repetitions"])
    ].reset_index(drop=True)

    rows = []
    for rate in pilot["rates_hz"]:
        max_tau = max(2, int(round(cfg["max_tau_seconds"] * rate)))
        for rec in segs.itertuples(index=False):
            for region in pilot["regions_primary"]:
                series = regional_speed_series(
                    rec.recording_id, int(rec.start_frame), int(rec.end_frame), region, pilot["native_fps"]
                )
                series = finite_clean(series)
                if series.size < 40:
                    continue
                series = downsample(series, pilot["native_fps"], float(rate))
                series = finite_clean(series)
                if series.size < 40:
                    continue
                ami = average_mutual_information(series, max_tau=max_tau)
                tau_star = first_local_minimum(ami)
                acf = autocorrelation(series, max_lag=max_tau)
                acf0 = first_acf_zero(acf)
                # provisional tau for FNN: AMI min or ACF zero or 0.15s
                tau_fnn = tau_star or acf0 or max(1, int(round(0.15 * rate)))
                tau_fnn = int(min(max(1, tau_fnn), max_tau))
                fnn = false_nearest_neighbors(
                    series,
                    tau=tau_fnn,
                    max_m=int(cfg["fnn_max_m"]),
                    rtol=float(cfg["fnn_rtol"]),
                    atol=float(cfg["fnn_atol"]),
                )
                m_star = choose_m_from_fnn(fnn)
                rows.append(
                    {
                        "participant": rec.participant,
                        "timepoint": rec.timepoint,
                        "repetition": rec.repetition,
                        "exercise_id": rec.exercise_id,
                        "region": region,
                        "rate_hz": rate,
                        "n_samples": series.size,
                        "duration_s": rec.duration_s,
                        "ami_class": classify_ami_curve(ami),
                        "tau_ami": tau_star,
                        "tau_acf0": acf0,
                        "tau_fnn_used": tau_fnn,
                        "m_fnn": m_star,
                        "ami_1": ami[0] if ami.size else np.nan,
                        "ami_at_tau": ami[tau_fnn - 1] if ami.size >= tau_fnn else np.nan,
                        "fnn_at_m": fnn[m_star - 1] if m_star and fnn.size >= m_star else np.nan,
                        "acf_lag1": acf[1] if acf.size > 1 else np.nan,
                    }
                )

    df = pd.DataFrame(rows)
    out = rqa_path("outputs", "t1_diagnostics", "ami_fnn_summary.csv")
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)

    # Aggregate proposed common band (seconds and frames per rate)
    summary = {}
    for rate, sub in df.groupby("rate_hz"):
        taus = sub["tau_ami"].dropna().astype(int)
        ms = sub["m_fnn"].dropna().astype(int)
        if len(taus) == 0:
            continue
        tau_med = int(np.median(taus))
        tau_q25, tau_q75 = int(np.quantile(taus, 0.25)), int(np.quantile(taus, 0.75))
        m_med = int(np.median(ms)) if len(ms) else 4
        m_p75 = int(np.quantile(ms, 0.75)) if len(ms) else m_med
        m_common = max(m_med, m_p75)  # prefer upper plausible
        m_common = int(np.clip(m_common, 3, 5))
        # band of 3 tau values around median
        band = sorted({max(1, tau_med - max(1, (tau_q75 - tau_q25) // 2)), tau_med, tau_med + max(1, (tau_q75 - tau_q25) // 2 + 1)})
        # ACF-informed block length: ~max(0.25s, 2*median tau)
        block_s = max(0.25, 2.0 * tau_med / float(rate))
        summary[str(int(rate))] = {
            "n_rows": int(len(sub)),
            "tau_median_frames": tau_med,
            "tau_q25_frames": tau_q25,
            "tau_q75_frames": tau_q75,
            "tau_band_frames": band,
            "tau_median_seconds": tau_med / float(rate),
            "m_median": m_med,
            "m_p75": m_p75,
            "m_common_proposed": m_common,
            "ami_class_counts": sub["ami_class"].value_counts().to_dict(),
            "mean_acf_lag1": float(sub["acf_lag1"].mean()),
            "block_shuffle_seconds_proposed": float(block_s),
        }

    summ_path = rqa_path("outputs", "t1_diagnostics", "ami_fnn_aggregate.json")
    summ_path.write_text(json.dumps(summary, indent=2))
    print(f"wrote {out} rows={len(df)}")
    print(f"wrote {summ_path}")


if __name__ == "__main__":
    main()
