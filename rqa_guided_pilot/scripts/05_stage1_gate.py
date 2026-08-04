#!/usr/bin/env python3
"""Evaluate Stage 1 stop gate and write decision report."""

from __future__ import annotations

import json

import numpy as np
import pandas as pd

import _bootstrap  # noqa: F401
from rqa_pilot.paths import ensure_rqa_dirs, rqa_path


CORE = ["DET", "LAM", "Lmean", "ENTR"]


def _drep_table(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    keys = ["participant", "timepoint", "exercise_id", "region", "normalization", "setting"]
    for key, sub in df.groupby(keys):
        if set(sub.repetition.tolist()) != {1, 2}:
            continue
        a = sub[sub.repetition == 1].iloc[0]
        b = sub[sub.repetition == 2].iloc[0]
        row = dict(zip(keys, key))
        for m in CORE + ["RR"]:
            row[f"Drep_{m}"] = abs(a[m] - b[m])
            row[f"mean_{m}"] = 0.5 * (a[m] + b[m])
            row[m + "_R1"] = a[m]
            row[m + "_R2"] = b[m]
        rows.append(row)
    return pd.DataFrame(rows)


def _longitudinal(df: pd.DataFrame) -> pd.DataFrame:
    """Matched-rep longitudinal |Δ| and ratio to max endpoint Drep."""
    prim = df[df.setting.isin(["primary_amp_preserving", "primary_trial_zscore"])]
    drep = _drep_table(prim)
    rows = []
    for (pid, ex, region, norm, setting), sub in prim.groupby(
        ["participant", "exercise_id", "region", "normalization", "setting"]
    ):
        for rep in (1, 2):
            s = sub[sub.repetition == rep]
            if set(s.timepoint.tolist()) != {1, 3}:
                continue
            t1 = s[s.timepoint == 1].iloc[0]
            t3 = s[s.timepoint == 3].iloc[0]
            # Drep at endpoints
            d1 = drep[
                (drep.participant == pid)
                & (drep.exercise_id == ex)
                & (drep.region == region)
                & (drep.normalization == norm)
                & (drep.setting == setting)
                & (drep.timepoint == 1)
            ]
            d3 = drep[
                (drep.participant == pid)
                & (drep.exercise_id == ex)
                & (drep.region == region)
                & (drep.normalization == norm)
                & (drep.setting == setting)
                & (drep.timepoint == 3)
            ]
            if d1.empty or d3.empty:
                continue
            row = {
                "participant": pid,
                "exercise_id": ex,
                "region": region,
                "normalization": norm,
                "setting": setting,
                "repetition": rep,
                "duration_s_T1": t1["duration_s"],
                "duration_s_T3": t3["duration_s"],
                "N_embed_T1": t1["N_embed"],
                "N_embed_T3": t3["N_embed"],
            }
            for m in CORE + ["RR"]:
                delta = abs(t3[m] - t1[m])
                drep_m = max(d1.iloc[0][f"Drep_{m}"], d3.iloc[0][f"Drep_{m}"])
                row[f"abs_delta_{m}"] = delta
                row[f"Drep_max_{m}"] = drep_m
                row[f"ratio_{m}"] = delta / drep_m if drep_m > 1e-12 else np.nan
            rows.append(row)
    return pd.DataFrame(rows)


def main() -> None:
    ensure_rqa_dirs()
    lock = json.loads(rqa_path("outputs", "locks", "parameter_lock_stage1.json").read_text())
    df = pd.read_csv(rqa_path("outputs", "stage1", "auto_rqa_metrics.csv"))

    prim = df[df.setting.isin(["primary_amp_preserving", "primary_trial_zscore"])].copy()
    drep = _drep_table(prim)
    drep.to_csv(rqa_path("outputs", "stage1", "r1r2_drep.csv"), index=False)
    longi = _longitudinal(df)
    longi.to_csv(rqa_path("outputs", "stage1", "longitudinal_d13.csv"), index=False)

    # Surrogate disruption on amp-preserving identity vs shuffle
    id_df = df[(df.setting == "primary_amp_preserving") & (df.surrogate == "identity")]
    sh_df = df[(df.setting == "surr_full_shuffle")]
    blk_df = df[(df.setting == "surr_block_shuffle")]
    merge_keys = ["participant", "timepoint", "repetition", "exercise_id", "region"]
    surr = id_df.merge(sh_df[merge_keys + CORE], on=merge_keys, suffixes=("", "_shuf"))
    surr = surr.merge(blk_df[merge_keys + CORE], on=merge_keys, suffixes=("", "_blk"))
    for m in CORE:
        surr[f"drop_{m}_shuf"] = surr[m] - surr[f"{m}_shuf"]
        surr[f"drop_{m}_blk"] = surr[m] - surr[f"{m}_blk"]
    surr.to_csv(rqa_path("outputs", "stage1", "surrogate_drops.csv"), index=False)

    # Truncation sensitivity: compare primary vs trunc on DET/Lmean
    trunc = df[df.setting == "trunc_amp_preserving"]
    tr = id_df.merge(trunc[merge_keys + CORE], on=merge_keys, suffixes=("", "_trunc"))
    for m in CORE:
        tr[f"delta_trunc_{m}"] = tr[f"{m}_trunc"] - tr[m]
    tr.to_csv(rqa_path("outputs", "stage1", "truncation_sensitivity.csv"), index=False)

    # Gate assessments (distributional; no 15%/70% hard cut)
    # 1) R1/R2: median relative Drep for DET
    rel = []
    for m in CORE:
        med = drep[f"Drep_{m}"].median()
        iqr = np.nanpercentile(drep[f"mean_{m}"], 75) - np.nanpercentile(drep[f"mean_{m}"], 25)
        rel.append({"metric": m, "median_Drep": float(med), "mean_IQR": float(iqr), "median_Drep_over_IQR": float(med / iqr) if iqr > 1e-12 else np.nan})
    rel_df = pd.DataFrame(rel)

    median_det_drop = float(surr["drop_DET_shuf"].median())
    median_lam_drop = float(surr["drop_LAM_shuf"].median())
    frac_det_drop_pos = float((surr["drop_DET_shuf"] > 0).mean())
    rr_med = float(prim[prim.normalization == "amp_preserving"]["RR"].median())
    rr_ok = 0.01 <= rr_med <= 0.10

    # Longitudinal descriptive: fraction of cells with ratio_DET > 1 on amp-preserving
    long_amp = longi[longi.normalization == "amp_preserving"]
    frac_ratio_det = float((long_amp["ratio_DET"] > 1).mean()) if len(long_amp) else 0.0
    frac_ratio_det_z = float((longi[longi.normalization == "trial_zscore"]["ratio_DET"] > 1).mean()) if len(longi) else 0.0

    # Truncation: median |delta DET|
    trunc_med = float(tr["delta_trunc_DET"].abs().median()) if len(tr) else np.nan

    # Tau sensitivity: rank correlation of DET across tau settings for same cells
    tau_settings = [s for s in df.setting.unique() if s.startswith("tau_") or s == "primary_amp_preserving"]
    # Simple: median abs DET difference between primary and each tau_*
    tau_diffs = []
    for s in df.setting.unique():
        if not str(s).startswith("tau_"):
            continue
        alt = df[df.setting == s]
        mrg = id_df.merge(alt[merge_keys + ["DET"]], on=merge_keys, suffixes=("", "_alt"))
        if len(mrg):
            tau_diffs.append(float((mrg["DET"] - mrg["DET_alt"]).abs().median()))
    tau_med_diff = float(np.nanmedian(tau_diffs)) if tau_diffs else np.nan

    checks = {
        "parameter_lock_exists": True,
        "primary_rate_hz": lock["primary_rate_hz"],
        "tau_frames": lock["tau_frames_at_primary"],
        "m": lock["m"],
        "rr_median_amp_preserving": rr_med,
        "rr_in_diagnostic_band_0.01_0.10": rr_ok,
        "median_DET_drop_full_shuffle": median_det_drop,
        "median_LAM_drop_full_shuffle": median_lam_drop,
        "fraction_cells_DET_drop_shuffle_gt0": frac_det_drop_pos,
        "surrogate_disrupts_DET": bool(median_det_drop > 0.02 and frac_det_drop_pos >= 0.6),
        "r1r2_summary": rel_df.to_dict(orient="records"),
        "r1r2_not_pathological": bool(rel_df.set_index("metric").loc["DET", "median_Drep_over_IQR"] < 1.5)
        if "DET" in set(rel_df.metric) else False,
        "frac_longitudinal_ratio_DET_gt1_amp": frac_ratio_det,
        "frac_longitudinal_ratio_DET_gt1_zscore": frac_ratio_det_z,
        "median_abs_delta_DET_truncation": trunc_med,
        "duration_truncation_not_abolishing": bool(np.isnan(trunc_med) or trunc_med < 0.5),
        "median_abs_DET_diff_across_tau_band": tau_med_diff,
        "tau_band_moderately_stable": bool(np.isnan(tau_med_diff) or tau_med_diff < 0.25),
    }

    # Stage-1 gate decision
    pass_tech = all(
        [
            checks["rr_in_diagnostic_band_0.01_0.10"] or rr_med < 0.15,  # allow mild overshoot with note
            checks["surrogate_disrupts_DET"],
            checks["r1r2_not_pathological"],
            checks["duration_truncation_not_abolishing"],
            checks["tau_band_moderately_stable"],
        ]
    )
    # Soft RR note
    if not checks["rr_in_diagnostic_band_0.01_0.10"]:
        checks["rr_note"] = "RR median outside 1–10% diagnostic band; review radius before Stage 2"

    decision = "PASS_TO_STAGE2" if pass_tech else "FAIL_OR_REVISE"
    checks["stage1_decision"] = decision
    checks["n_metric_rows"] = int(len(df))
    checks["n_longitudinal_rows"] = int(len(longi))

    gate_path = rqa_path("outputs", "stage1", "STAGE1_GATE.json")
    gate_path.write_text(json.dumps(checks, indent=2))

    # Markdown report
    report = f"""# Stage 1 Gate Report

**Decision:** `{decision}`  
**Primary rate (locked):** {lock['primary_rate_hz']} Hz  
**tau / m:** {lock['tau_frames_at_primary']} / {lock['m']}  
**Block shuffle:** {lock['block_shuffle_seconds']:.3f} s

## Technical checks

| Check | Value |
|---|---|
| RR median (amp-preserving) | {rr_med:.4f} |
| RR in 1–10% band | {checks['rr_in_diagnostic_band_0.01_0.10']} |
| Median DET drop (full shuffle) | {median_det_drop:.4f} |
| Fraction DET drop > 0 | {frac_det_drop_pos:.3f} |
| Surrogate disrupts DET | {checks['surrogate_disrupts_DET']} |
| R1/R2 not pathological (DET) | {checks['r1r2_not_pathological']} |
| Truncation median \\|ΔDET\\| | {trunc_med:.4f} |
| Tau-band median \\|ΔDET\\| | {tau_med_diff:.4f} |

## Descriptive longitudinal (not sufficient alone)

- Fraction cells with \\|ΔDET\\|/Drep > 1 (amp-preserving): **{frac_ratio_det:.3f}**
- Fraction cells with \\|ΔDET\\|/Drep > 1 (trial z-score): **{frac_ratio_det_z:.3f}**

## Interpretation language

Regional Auto-RQA here measures recurrence of **regional angular-velocity-magnitude dynamics**, not posture or anatomical pose recurrence.

## Next step

{"Proceed to Stage 2 (T2 + novelty vs Conv/explicit + optional CRQA) upon approval." if decision == "PASS_TO_STAGE2" else "Do not expand to Stage 2 until technical issues are resolved."}

Artifacts: `outputs/stage1/*.csv`, `outputs/locks/parameter_lock_stage1.json`.
"""
    rqa_path("reports", "STAGE1_GATE_REPORT.md").write_text(report)
    print(f"wrote {gate_path}")
    print(f"decision={decision}")


if __name__ == "__main__":
    main()
