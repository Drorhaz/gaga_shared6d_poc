#!/usr/bin/env python3
"""Write Stage 2 markdown reports from computed tables."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

import _bootstrap  # noqa: F401
from rqa_pilot.paths import ensure_rqa_dirs, rqa_path


def _md_table(df: pd.DataFrame, cols=None, max_rows=30) -> str:
    if df is None or df.empty:
        return "_No rows._\n"
    d = df if cols is None else df[cols]
    d = d.head(max_rows).copy()
    # format floats
    for c in d.columns:
        if pd.api.types.is_float_dtype(d[c]):
            d[c] = d[c].map(lambda x: f"{x:.4f}" if pd.notna(x) else "")
    header = "| " + " | ".join(map(str, d.columns)) + " |"
    sep = "| " + " | ".join(["---"] * len(d.columns)) + " |"
    rows = ["| " + " | ".join(map(str, row)) + " |" for row in d.to_numpy()]
    return "\n".join([header, sep, *rows]) + "\n"


def main() -> None:
    ensure_rqa_dirs()
    out = rqa_path("outputs", "stage2")
    fig = rqa_path("figures", "stage2")
    fig.mkdir(parents=True, exist_ok=True)
    rep = rqa_path("reports")

    lock = json.loads(rqa_path("outputs", "locks", "parameter_lock_stage1.json").read_text())
    gate = json.loads((out / "STAGE2_GATE.json").read_text())
    longi = pd.read_csv(out / "longitudinal_deltas.csv")
    drep = pd.read_csv(out / "r1r2_drep.csv")
    surr = pd.read_csv(out / "surrogate_drops.csv")
    trunc = pd.read_csv(out / "truncation_sensitivity.csv")
    amp = pd.read_csv(out / "amplitude_control_pairs.csv")
    cmp_ = pd.read_csv(out / "exercise_level_comparison.csv")
    sens = pd.read_csv(out / "sensitivity_summary.csv")
    mdrqa = pd.read_csv(out / "compact_mdrqa.csv") if (out / "compact_mdrqa.csv").exists() else pd.DataFrame()
    crqa = pd.read_csv(out / "crqa_trunk_arms.csv") if (out / "crqa_trunk_arms.csv").exists() else pd.DataFrame()

    # Simple diagnostic figure: DET ratios by pid/ex/delta for zscore
    try:
        import matplotlib.pyplot as plt

        z = cmp_[(cmp_.normalization == "trial_zscore") & (cmp_.delta.isin(["D12", "D13"]))]
        if len(z):
            fig1, ax = plt.subplots(figsize=(7, 4))
            labels = [f"{r.participant}-ex{int(r.exercise_id)}-{r.delta}" for r in z.itertuples()]
            ax.bar(range(len(z)), z.median_ratio_DET.values)
            ax.axhline(1.0, color="k", ls="--", lw=1)
            ax.set_xticks(range(len(z)))
            ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=8)
            ax.set_ylabel("median |ΔDET| / Drep")
            ax.set_title("Stage 2 DET change vs R1/R2 (trial z-score)")
            fig1.tight_layout()
            fig1.savefig(fig / "det_ratio_zscore.png", dpi=120)
            plt.close(fig1)
    except Exception as e:
        (fig / "figure_error.txt").write_text(str(e))

    # --- reports ---
    (rep / "STAGE2_METHOD_REPORT.md").write_text(
        f"""# Stage 2 Method Report

**Branch:** `exploratory/guided-rqa-stage2`  
**Stage 1 freeze:** `rqa-stage1-feasibility-pass-v1` @ `{lock.get('primary_rate_hz')} Hz lock`  
**Scientific freeze untouched:** `guided-analysis-freeze-v1` @ `5062e22`

## Scope

- Participants: 651, 790
- Exercises: ex11, ex13
- Timepoints: T1, T2, T3
- Repetitions: R1, R2
- Primary method: regional Auto-RQA on angular-velocity-magnitude dynamics
- Views: amplitude-preserving (fixed radius); trial z-score (target RR)

## Locked parameters (not retuned on T2/T3)

| Parameter | Value |
|---|---|
| Rate | {lock['primary_rate_hz']} Hz |
| τ | {lock['tau_frames_at_primary']} frames ({lock['tau_seconds']} s) |
| m | {lock['m']} |
| Embed span | 0.45 s |
| Radius (amp-preserving) | {lock['threshold']['fixed_radius_frac_mean_dist_default']} × mean distance |
| Target RR (z-score) | {lock['threshold']['target_rr']} |
| Theiler | {lock['theiler_default']} |
| Lmin | {lock['lmin_default']} (+ sensitivity 3) |
| Block shuffle | {lock['block_shuffle_seconds']} s |

## Metrics

Primary: RR (fixed-radius only), DET, Lmean, LAM, ENTR.  
Secondary: Lmax/N_embed, ε (target-RR), Lmean in seconds.

## Language

Analyses concern **regional angular-velocity-magnitude dynamics** and **multiregional angular-velocity states** (MdRQA). Not posture/pose/motif recurrence.
"""
    )

    # Longitudinal
    focus = longi[longi.delta.isin(["D12", "D13"])]
    summary = (
        focus.groupby(["participant", "exercise_id", "delta", "normalization"])
        .agg(med_ratio_DET=("ratio_DET", "median"), frac_DET=("ratio_DET", lambda s: float((s > 1).mean())), med_ratio_LAM=("ratio_LAM", "median"))
        .reset_index()
    )
    (rep / "STAGE2_LONGITUDINAL_RESULTS.md").write_text(
        f"""# Stage 2 Longitudinal Results

## Empirical summary (median |Δ|/Drep)

{_md_table(summary)}

## Notes

- Comparisons are within the same exercise.
- `|Δ|/Drep > 1` is descriptive continuity with Conv, not a sole success criterion.
- See novelty and amplitude-control reports for interpretation.
"""
    )

    (rep / "STAGE2_R1_R2_RELIABILITY.md").write_text(
        f"""# Stage 2 R1/R2 Reliability

Multi-indicator framework (no 15%/70% hard gates).

## Median Drep (primary settings)

{_md_table(drep.groupby(['normalization','timepoint']).agg(DET=('Drep_DET','median'), LAM=('Drep_LAM','median'), Lmean=('Drep_Lmean','median'), ENTR=('Drep_ENTR','median')).reset_index())}

Scale-normalized summaries use Drep relative to within-metric IQR on T1 cells in Stage 1; Stage 2 reports absolute Drep alongside longitudinal ratios.
"""
    )

    (rep / "STAGE2_DURATION_AND_SURROGATE_CHECKS.md").write_text(
        f"""# Stage 2 Duration and Surrogate Checks

## Surrogates (amp-preserving Auto-RQA)

| Control | median DET drop | median LAM drop | median Lmean drop |
|---|---|---|---|
| Full shuffle | {surr.drop_DET_shuf.median():.3f} | {surr.drop_LAM_shuf.median():.3f} | {surr.drop_Lmean_shuf.median():.3f} |
| Block shuffle | {surr.drop_DET_blk.median():.3f} | {surr.drop_LAM_blk.median():.3f} | {surr.drop_Lmean_blk.median():.3f} |

Full shuffle remains the primary negative control. Block shuffle is graded (weaker DET effect under near-ceiling DET).

## Duration truncation

Median |ΔDET| (trunc − primary): **{trunc.delta_trunc_DET.abs().median():.4f}**

Raw Lmax is diagnostic only; Lmean / Lmax·N⁻¹ used for claims.
"""
    )

    z_persist = float(((amp.ratio_DET_amp > 1) & (amp.ratio_DET_z > 1)).mean()) if len(amp) else 0
    (rep / "STAGE2_AMPLITUDE_CONTROL.md").write_text(
        f"""# Stage 2 Amplitude Control

Parallel views: amplitude-preserving (RR interpretable) and trial-level z-score (target-RR; RR not a DV).

## Persistence of DET ratios

Fraction of matched cells with ratio_DET > 1 in **both** amp-preserving and z-score views: **{z_persist:.3f}**

{_md_table(amp.assign(both_DET=lambda d: (d.ratio_DET_amp>1)&(d.ratio_DET_z>1)).groupby(['participant','exercise_id','delta']).both_DET.mean().reset_index(), max_rows=40)}

A finding that vanishes entirely under z-score and tracks energy is not treated as novel temporal organization.
"""
    )

    (rep / "STAGE2_COMPARISON_WITH_EXISTING_METHODS.md").write_text(
        f"""# Stage 2 Comparison with Existing Methods

Read-only inputs: Conv exercise-level `|Δ|/Drep` and explicit recording-feature changes.

## Exercise-level table

{_md_table(cmp_[cmp_.delta.isin(['D12','D13'])].sort_values(['participant','exercise_id','delta','normalization']), cols=['participant','exercise_id','delta','normalization','median_ratio_DET','frac_ratio_DET_gt1','conv_ratio','conv_exceed_frac','feat_exceed_total_energy_deg2_s2','feat_exceed_participation_entropy_bits_amp_residual','novelty_class'])}

Transformer remains secondary sensitivity only. PCA is not used as RQA input.
"""
    )

    counts = cmp_.novelty_class.value_counts().to_dict()
    (rep / "STAGE2_NOVELTY_ASSESSMENT.md").write_text(
        f"""# Stage 2 Novelty Assessment

## Class counts (exercise-level rows)

{json.dumps(counts, indent=2)}

## Criteria

A finding is `NOVEL_TEMPORAL_INFORMATION` only if structure-metric change is stable vs R1/R2, persists under trial z-score, is not fully explained by energy, and remains interpretable as intensity-dynamics reorganization.

`COMPLEMENTARY_INTERPRETATION`: useful temporal description alongside Conv/explicit changes.  
`REDUNDANT_WITH_EXISTING_FEATURES`: mirrors energy/explicit features without z-score persistence.  
`UNSTABLE` / `NOT_INTERPRETABLE`: fails reliability or lacks coherent structure-metric support.

## Strongest novelty support

{_md_table(cmp_[(cmp_.novelty_class=='NOVEL_TEMPORAL_INFORMATION') & (cmp_.delta.isin(['D12','D13']))])}

## Strongest evidence against novelty

{_md_table(cmp_[cmp_.novelty_class.isin(['REDUNDANT_WITH_EXISTING_FEATURES','UNSTABLE']) & (cmp_.delta.isin(['D12','D13']))])}
"""
    )

    # MdRQA / CRQA brief in gate extras
    md_note = "MdRQA not computed." if mdrqa.empty else f"Compact MdRQA median DET drop vs shuffle: {(mdrqa.DET - mdrqa.DET_shuf).median():.3f}"
    cr_note = "CRQA not computed." if crqa.empty else f"CRQA trunk–arms median DET drop (shuffle-one): {(crqa.DET - crqa.DET_shuf_one).median():.3f}"

    decision = gate["decision"]
    (rep / "STAGE2_GATE_REPORT.md").write_text(
        f"""# Stage 2 Gate Report

# Decision: `{decision}`

## Gate inputs

| Check | Value |
|---|---|
| Qualified pid×ex×delta (z-score novel/complementary) | {gate.get('n_qualified_pid_ex_delta_zscore', gate.get('n_qualified_pid_ex_delta', 0))} |
| Amp-preserving complementary pid×ex×delta | {gate.get('n_amp_preserving_complementary_pid_ex_delta', 0)} |
| Novel z-score rows | {gate['n_novel_zscore_rows']} |
| Full-shuffle DET drop median | {gate['surrogate_DET_drop_median']:.3f} |
| Surrogate OK | {gate['surrogate_ok']} |
| Truncation OK | {gate['truncation_ok']} |
| Sensitivity OK | {gate['sensitivity_ok']} |

## Secondary analyses

- {md_note}
- {cr_note}
- CRQA run as a limited trunk–arm coordination check; interpret relative to existing `trunk_arm_lagged_coupling`.

## Sensitivity summary

{_md_table(sens)}

## Stop

Stage 3 is **not** started. Even if `{decision}` is `PASS_TO_STAGE3`, Stage 3 requires separate approval.

## Limitations

- N=2 participants in Stage 2; session–timepoint confounding remains.
- DET near ceiling under amp-preserving view; z-score/target-RR and Lmin=3 sensitivity mitigate over-reading.
- R1/R2 is within-session variability, not a full noise floor.
"""
    )

    manifest = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "stage": "stage2",
        "branch": "exploratory/guided-rqa-stage2",
        "stage1_tag": "rqa-stage1-feasibility-pass-v1",
        "decision": decision,
        "locked_params": {
            "rate_hz": lock["primary_rate_hz"],
            "tau_frames": lock["tau_frames_at_primary"],
            "m": lock["m"],
            "radius": lock["threshold"]["fixed_radius_frac_mean_dist_default"],
        },
        "outputs": sorted(p.name for p in out.glob("*")),
        "reports": [
            "STAGE2_METHOD_REPORT.md",
            "STAGE2_LONGITUDINAL_RESULTS.md",
            "STAGE2_R1_R2_RELIABILITY.md",
            "STAGE2_DURATION_AND_SURROGATE_CHECKS.md",
            "STAGE2_AMPLITUDE_CONTROL.md",
            "STAGE2_COMPARISON_WITH_EXISTING_METHODS.md",
            "STAGE2_NOVELTY_ASSESSMENT.md",
            "STAGE2_GATE_REPORT.md",
        ],
    }
    rqa_path("manifests", "stage2_run_manifest.json").write_text(json.dumps(manifest, indent=2))
    print("reports written; decision=", decision)


if __name__ == "__main__":
    main()
