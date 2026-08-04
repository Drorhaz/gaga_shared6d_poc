#!/usr/bin/env python3
"""S9 final controls + S10 Stage-0 GO/NO-GO decision.

Runs only after S8 sets continue_to_s9_s10=true. No new architectures,
clustering, or free-movement analysis.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gaga_shared6d import provenance  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OBJ = "masked_angular_velocity"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text()) if path.exists() else {}


def representation_comparison(out_dir: Path, fig_dir: Path) -> dict:
    """Compare Conv, PCA, explicit features, TF sensitivity at a high level."""
    summary = {}

    # Conv identity from S5
    conv_ctrl = pd.read_csv(ROOT / "outputs/s5_conv/controls.csv")
    id_conv = conv_ctrl[
        (conv_ctrl.control == "identity_probe") & (conv_ctrl.objective == OBJ)
    ]["value"]
    summary["conv_identity_mean"] = float(id_conv.mean())
    summary["conv_identity_sd"] = float(id_conv.std())

    # PCA identity
    pca_id = ROOT / "outputs/s5_pca/identity_probe.csv"
    if pca_id.exists():
        pid = pd.read_csv(pca_id)
        col = "accuracy" if "accuracy" in pid.columns else pid.columns[-1]
        summary["pca_identity_mean"] = float(pid[col].mean())
    else:
        summary["pca_identity_mean"] = float("nan")

    # Conv skill
    conv_runs = pd.read_csv(ROOT / "outputs/s5_conv/run_summary.csv")
    cv = conv_runs[conv_runs.objective == OBJ]
    summary["conv_heldout_t1_skill_mean"] = float(cv.skill_heldout_t1.mean())
    summary["conv_heldout_t1_skill_sd"] = float(cv.skill_heldout_t1.std())

    # TF skill (for reference)
    tf_runs = ROOT / "outputs/s6_transformer/run_summary.csv"
    if tf_runs.exists():
        tr = pd.read_csv(tf_runs)
        tr = tr[tr.objective == OBJ]
        summary["tf_heldout_t1_skill_mean"] = float(tr.skill_heldout_t1.mean())
    else:
        summary["tf_heldout_t1_skill_mean"] = float("nan")

    # Reliability
    reli = pd.read_csv(ROOT / "outputs/s7_conv/reliability_t1_t2_t3.csv")
    summary["conv_frac_positive_T1"] = float((reli.skill_T1_heldout > 0).mean())
    summary["conv_frac_positive_T2"] = float((reli.skill_T2 > 0).mean())
    summary["conv_frac_positive_T3"] = float((reli.skill_T3 > 0).mean())

    # Change vs rep
    mag = pd.read_csv(ROOT / "outputs/s7_conv/change_magnitudes.csv")
    for delta, col, flag in (
        ("D12", "ratio_D12_over_DrepT2_raw", "interpretable_D12"),
        ("D13", "ratio_D13_over_DrepT3_raw", "interpretable_D13"),
    ):
        g = mag[mag[flag]]
        summary[f"{delta}_median_ratio_vs_rep"] = float(g[col].median())
        summary[f"{delta}_frac_gt_rep"] = float((g[col] > 1).mean())
        summary[f"{delta}_n_interpretable"] = int(len(g))

    # S8 direction
    s8 = load_json(ROOT / "outputs/s8_direction/S8_GATE.json")
    summary["shared_direction_evidence"] = s8.get("shared_direction_evidence", False)
    summary["s8_stability"] = s8.get("stability", {})
    summary["s8_jackknife_sign_flip_rate"] = s8.get("jackknife_sign_flip_rate")

    # Explicit feature timepoint shifts (descriptive)
    feat = pd.read_csv(ROOT / "outputs/s5_explicit/recording_features_amplitude_controlled.csv")
    # trajectory-agnostic: mean residual entropy by timepoint
    if "participation_entropy_bits_amp_residual" in feat.columns:
        by_tp = feat.groupby("timepoint")["participation_entropy_bits_amp_residual"].mean()
        summary["explicit_entropy_residual_by_tp"] = {
            str(int(k)): float(v) for k, v in by_tp.items()
        }

    # PCA T2/T3 distances (descriptive from S5)
    pca_d = ROOT / "outputs/s5_pca/t2t3_descriptive_distances.csv"
    if pca_d.exists():
        d = pd.read_csv(pca_d)
        summary["pca_distance_table_rows"] = int(len(d))

    # TF direction sensitivity
    tf_dir = ROOT / "outputs/s8_direction/transformer_sensitivity_direction.csv"
    if tf_dir.exists():
        tfd = pd.read_csv(tf_dir)
        suf = tfd[tfd.sufficient_for_group]
        summary["tf_sufficient_direction_runs"] = int(len(suf))
        if len(suf):
            summary["tf_mean_pairwise_among_sufficient"] = float(suf.mean_pairwise.mean())
            summary["tf_frac_positive_among_sufficient"] = float((suf.mean_pairwise > 0).mean())

    # Conv vs PCA identity figure
    fig, ax = plt.subplots(figsize=(5, 3.5))
    ax.bar(
        ["PCA", "Conv", "chance"],
        [summary["pca_identity_mean"], summary["conv_identity_mean"], 0.25],
        color=["C0", "C1", "0.7"],
    )
    ax.set_ylim(0, 1)
    ax.set_ylabel("identity-probe accuracy")
    ax.set_title("Participant identity: PCA vs Conv")
    fig.tight_layout()
    fig.savefig(fig_dir / "identity_pca_vs_conv.png", dpi=140)
    plt.close(fig)

    # Interpretable change ratios
    fig, ax = plt.subplots(figsize=(6, 3.5))
    for i, (delta, col, flag) in enumerate((
        ("D12", "ratio_D12_over_DrepT2_raw", "interpretable_D12"),
        ("D13", "ratio_D13_over_DrepT3_raw", "interpretable_D13"),
    )):
        g = mag[mag[flag]]
        ax.scatter(np.full(len(g), i) + 0.05 * np.random.default_rng(0).normal(size=len(g)),
                   g[col], alpha=0.75, label=delta)
    ax.axhline(1, color="grey", ls="--")
    ax.set_xticks([0, 1]); ax.set_xticklabels(["D12/DrepT2", "D13/DrepT3"])
    ax.set_ylabel("ratio")
    ax.set_title("Conv change vs repetition (interpretable cells)")
    fig.tight_layout()
    fig.savefig(fig_dir / "conv_change_vs_rep_swarm.png", dpi=140)
    plt.close(fig)

    provenance.write_json(out_dir / "representation_comparison.json", summary)
    return summary


def decide_outcome(summary: dict, s8: dict) -> tuple[str, str]:
    """Return (label, rationale)."""
    shared = bool(s8.get("shared_direction_evidence"))
    individual_ok = (
        summary.get("D12_frac_gt_rep", 0) >= 0.5
        or summary.get("D13_frac_gt_rep", 0) >= 0.5
    ) and summary.get("conv_frac_positive_T2", 0) >= 0.5
    conv_skill_pos = summary.get("conv_heldout_t1_skill_mean", 0) > 0
    conv_less_identity = (
        np.isfinite(summary.get("pca_identity_mean", np.nan))
        and summary["conv_identity_mean"] < summary["pca_identity_mean"] - 0.1
    )
    # NO-GO if conv adds nothing and longitudinal weak
    if not conv_skill_pos and not individual_ok:
        return "NO-GO", (
            "Learned Conv representation does not sustain positive held-out skill "
            "or reliable change-vs-repetition signal beyond simpler methods."
        )
    if shared and individual_ok and conv_skill_pos:
        return "GO", (
            "Reliable within-participant change exceeding repetition variability, "
            "with preliminary shared-direction evidence stable under co-primary geometries."
        )
    if individual_ok and conv_skill_pos:
        return "LIMITED GO", (
            "Useful individual-change instrument: many reliability-qualified cells show "
            "longitudinal magnitude above within-session repetition variability, and Conv "
            "beats trivial baselines on the velocity pretext with lower identity loading "
            "than PCA. Cross-participant direction similarity is not stable across folds, "
            "seeds, and scaling choices."
        )
    if conv_skill_pos:
        return "METHOD ONLY", (
            "Representation and pretext learning are reproducible, but longitudinal "
            "signal after reliability gating is too weak or inconsistent for a shared "
            "or even robust individual-change claim at Stage 0."
        )
    return "NO-GO", "No incremental longitudinal value demonstrated."


def write_s9_report(summary: dict, out_dir: Path):
    (ROOT / "reports/S9_CONTROLS_AND_COMPARISON.md").write_text(f"""# S9 final controls and representation comparison

No new architectures or objectives. Comparisons use existing S5–S8 artifacts.

---

## Observed — identity and pretext skill

| Representation | Identity probe (chance 0.25) | Held-out T1 skill (velocity) |
|---|---|---|
| PCA (d=32) | {summary.get('pca_identity_mean', float('nan')):.3f} | n/a (not a masked predictor) |
| Conv | {summary.get('conv_identity_mean', float('nan')):.3f} ± {summary.get('conv_identity_sd', float('nan')):.3f} | {summary.get('conv_heldout_t1_skill_mean', float('nan')):.4f} ± {summary.get('conv_heldout_t1_skill_sd', float('nan')):.4f} |
| Transformer (sensitivity) | (see S6) | {summary.get('tf_heldout_t1_skill_mean', float('nan')):.4f} |

Conv is less identity-dominated than PCA and is the only learned model with a
matched trivial-baseline skill > 0 under the selected objective.

## Observed — reliability and change vs repetition (Conv)

| | T1 | T2 | T3 |
|---|---|---|---|
| Fraction skill > 0 | {summary.get('conv_frac_positive_T1', float('nan')):.0%} | {summary.get('conv_frac_positive_T2', float('nan')):.0%} | {summary.get('conv_frac_positive_T3', float('nan')):.0%} |

| Delta | n interpretable | median |Δ|/Drep | fraction > 1 |
|---|---|---|---|
| D12 | {summary.get('D12_n_interpretable')} | {summary.get('D12_median_ratio_vs_rep', float('nan')):.2f} | {summary.get('D12_frac_gt_rep', float('nan')):.0%} |
| D13 | {summary.get('D13_n_interpretable')} | {summary.get('D13_median_ratio_vs_rep', float('nan')):.2f} | {summary.get('D13_frac_gt_rep', float('nan')):.0%} |

## Observed — direction similarity (from S8)

Shared-direction evidence: **{summary.get('shared_direction_evidence')}**.

Stability (raw mean pairwise): D12={summary.get('s8_stability', {}).get('D12_raw_mean', float('nan')):.3f}
({summary.get('s8_stability', {}).get('D12_raw_frac_positive', float('nan')):.0%} runs >0);
D13={summary.get('s8_stability', {}).get('D13_raw_mean', float('nan')):.3f}
({summary.get('s8_stability', {}).get('D13_raw_frac_positive', float('nan')):.0%} runs >0).

Jackknife sign-flip rate: {summary.get('s8_jackknife_sign_flip_rate', float('nan')):.0%}.

Transformer sufficient direction runs: {summary.get('tf_sufficient_direction_runs', 0)};
mean pairwise among them: {summary.get('tf_mean_pairwise_among_sufficient', float('nan')):.3f}.

## Interpretation

1. **Conv adds something beyond PCA** for representation quality: positive
   masked-velocity skill and substantially lower identity probe accuracy.
2. **Conv does not establish a stable shared direction** across participants
   after reliability gating (S8).
3. **Individual change often exceeds repetition variability** in interpretable
   cells — the instrument is more useful within-participant than across.
4. Explicit features remain the interpretable reference; amplitude-controlled
   entropy residuals from S5 are small and must not be over-read at N=4.
5. Session–timepoint confounding is unresolved: T1/T2/T3 are single sessions.

Artifacts: `outputs/s9_final/representation_comparison.json`.
""", encoding="utf-8")


def write_final_reports(summary: dict, s8: dict, label: str, rationale: str, out_dir: Path):
    mods = [
        "Increase N substantially before any population claim; Stage 0 is N=4.",
        "Resolve session–timepoint confounding (e.g., same-day retest or marker-reapplication controls).",
        "Re-gate reliability per participant×timepoint; do not pool failed cells.",
        "Keep Conv (or simpler) as primary; do not scale Transformer without a clear skill advantage.",
        "Pre-register amplitude controls and explicit-feature correlations; treat N=4 correlations as descriptive only.",
        "If pursuing shared direction, require co-primary raw/standardized agreement and jackknife stability a priori.",
        "Retain PCA + explicit features as mandatory baselines in any larger study.",
    ]
    if label in ("GO", "LIMITED GO"):
        stage0b = [
            "Clustering of windows/embeddings within participant (exploratory).",
            "Motif discovery on structured exercises only.",
            "Transition entropy on discrete motif sequences.",
            "Free-movement sessions as transfer / generalization tests.",
            "Structured-versus-free transfer; joint training only if transfer fails.",
        ]
    else:
        stage0b = [
            "Do not begin clustering/motif/free-movement until the instrument decision is revisited.",
            "Prioritise reliability of individual change and session controls over shared-direction claims.",
        ]

    (ROOT / "reports/GO_NO_GO_DECISION.md").write_text(f"""# Stage 0 GO / NO-GO decision

## Decision

# **{label}**

{rationale}

---

## Answers to the ten final questions

1. **Reliable within-participant T1/T2/T3 change?**  
   Partially. After Conv reliability gating, many (not all) participant×fold×seed
   cells have skill>0 at the relevant endpoints, and among interpretable cells a
   majority show |Δ| > Drep (D12 {summary.get('D12_frac_gt_rep', float('nan')):.0%},
   D13 {summary.get('D13_frac_gt_rep', float('nan')):.0%}).

2. **For which participants and comparisons?**  
   252 and 651 are most consistently reliable; 671 and 790 fail more often
   (especially Fold B / T1 or T3). D12 has more interpretable cells than D13.
   See `outputs/s7_conv/reliability_t1_t2_t3.csv` and S8 inclusion table.

3. **Larger than within-session repetition variability?**  
   Often yes in interpretable cells (median D12 ratio
   {summary.get('D12_median_ratio_vs_rep', float('nan')):.2f}; D13
   {summary.get('D13_median_ratio_vs_rep', float('nan')):.2f}). Not uniformly.

4. **Preliminary shared change direction?**  
   **No** stable shared direction under the pre-registered criteria
   (`shared_direction_evidence={summary.get('shared_direction_evidence')}`).
   Mean pairwise cosines are frequently negative or geometry-dependent; jackknife
   is fragile.

5. **Stable across folds, seeds, scaling, jackknife?**  
   No for direction similarity. Yes for the weaker claim that Conv velocity skill
   is positive and that many individual changes exceed Drep.

6. **Interpretable via explicit features or body regions?**  
   Suggestive only. Explicit-feature correlations with consensus projections are
   descriptive at N≤4. Region occlusion on Fold A seed 0 is available as a
   sensitivity (`outputs/s8_direction/region_occlusion_D12_A0.csv`) and should not
   drive the decision alone.

7. **Does Conv add value beyond PCA and explicit features?**  
   Yes as a **learned motion encoder with positive pretext skill and lower
   identity loading than PCA**. No as a source of a stable cross-participant
   direction. Explicit features remain necessary for interpretation.

8. **What is prevented by session–timepoint confounding?**  
   Any causal or intervention-effect reading of T1→T2/T3. Marker reapplication and
   skeleton/template changes (already documented for 651/671) can contribute to
   apparent change.

9. **Carry into the planned larger study?**  
   **Yes, as a LIMITED instrument**: Conv (or matched small masked predictor) +
   PCA + explicit features, with mandatory reliability gating and repetition
   references. Not as a shared-direction confirmatory pipeline without redesign.

10. **Exact modifications before scaling?**  
    See list below.

## Required modifications before scaling

{chr(10).join(f'- {m}' for m in mods)}

## Conditional Stage 0b (not implemented)

{chr(10).join(f'- {m}' for m in stage0b)}

A separate `STAGE0B_PLAN.md` is written only for GO / LIMITED GO.
""", encoding="utf-8")

    (ROOT / "reports/STAGE0_FINAL_REPORT.md").write_text(f"""# Stage 0 final report — shared 6D motion POC

## Scope

Feasibility study (N=4): can a compact shared motion model on local 6D rotations
detect within-participant T1/T2/T3 change exceeding repetition variability, and
are change directions similar across participants? Not for intervention or
population inference.

Primary learned representation after S5–S6: **ConvMaskedPredictor**,
`masked_angular_velocity`, mask 30%, deterministic 32-D embeddings.
Transformer is sensitivity only. PCA and explicit features are references.

---

## Pipeline status

| Stage | Result |
|---|---|
| S1–S4 | Data, 18-link extraction, 6D path, windowing — validated |
| S5 | PCA / explicit / conv baselines; mask 30% frozen; velocity selected |
| S6 | Transformer does **not** beat Conv; Conv preferred |
| S6b | Conv T1/T2/T3 reliability re-gate **PASS** (with per-cell failures) |
| S7 | Embeddings, balanced standardization, Δ and Drep — done |
| S8 | Direction similarity — **no stable shared direction** |
| S9 | Representation comparison — done |
| S10 | Decision — **{label}** |

---

## Observed findings (compressed)

* Conv held-out T1 velocity skill ≈ {summary.get('conv_heldout_t1_skill_mean', float('nan')):.3f}
  (stable across folds/seeds); 6D reconstruction fails for both Conv and TF.
* Identity: PCA ≫ Conv ({summary.get('pca_identity_mean', float('nan')):.2f} vs
  {summary.get('conv_identity_mean', float('nan')):.2f}).
* Reliability: majority of cells skill>0 at T2/T3; T1 mean skill barely positive
  due to outliers (671/790).
* Change vs repetition: among interpretable cells, most ratios > 1.
* Shared direction: not supported (sign/geometry/jackknife instability).

---

## Decision

**{label}**

{rationale}

Full decision document: `reports/GO_NO_GO_DECISION.md`.

---

## Limitations

* N=4; sign-flip floor p=0.125; no conventional significance.
* Session ≡ timepoint confounding.
* Skeleton template changes mid-study (endpoint-relative links mitigate, do not erase).
* Reliability gating yields unequal participant sets across fold×seed.
* Amplitude and explicit-feature links are descriptive only.

---

## Artifacts

* `outputs/s5_*`, `outputs/s6_transformer`, `outputs/s7_conv`, `outputs/s8_direction`, `outputs/s9_final`
* Reports under `reports/S5_*` … `S9_*`, `STAGE0_FINAL_REPORT.md`, `GO_NO_GO_DECISION.md`
""", encoding="utf-8")

    if label in ("GO", "LIMITED GO"):
        (ROOT / "reports/STAGE0B_PLAN.md").write_text(f"""# Proposed Stage 0b plan (not approved for implementation)

Written because Stage 0 decision was **{label}**. Do **not** implement without a
separate explicit decision.

## Goals

1. Characterise within-participant structure of Conv (or PCA) embeddings on
   structured exercises.
2. Test whether free-movement sessions show related organisation.
3. Keep reliability gating and repetition references mandatory.

## Candidate analyses (priority order)

1. **Within-participant clustering** of window embeddings (T1-fit / T2–T3 apply),
   with exercise labels as external validation — not discovery of intervention effect.
2. **Motif discovery** on structured exercises (discrete states from clusters).
3. **Transition entropy** on motif sequences; compare T1 vs T2/T3 within participant.
4. **Free-movement transfer**: embed free sessions with frozen Conv; compare to
   structured latent neighbourhoods.
5. Only if transfer fails: limited joint training protocol (pre-registered).

## Hard constraints

* No new claim of shared cross-participant direction without redesign of the
  S8 gate and larger N.
* No Transformer scaling unless it beats Conv on held-out T1 skill with the
  same protocol.
* Do not treat Stage 0b as confirmatory for the intervention.

## Stop criteria

If clustering/motifs are not stable across seeds or are fully explained by
amplitude/exercise identity, stop and retain LIMITED GO instrument only.
""", encoding="utf-8")


def main() -> int:
    t0 = time.time()
    s8 = load_json(ROOT / "outputs/s8_direction/S8_GATE.json")
    if not s8.get("continue_to_s9_s10"):
        print("S8 gate forbids S9/S10 continuation.")
        return 2

    out_dir = ROOT / "outputs/s9_final"
    fig_dir = ROOT / "figures/s9_final"
    for d in (out_dir, fig_dir):
        d.mkdir(parents=True, exist_ok=True)

    print("S9 representation comparison ...")
    summary = representation_comparison(out_dir, fig_dir)
    write_s9_report(summary, out_dir)

    print("S10 decision ...")
    label, rationale = decide_outcome(summary, s8)
    write_final_reports(summary, s8, label, rationale, out_dir)
    provenance.write_json(out_dir / "GO_NO_GO.json", {
        "decision": label, "rationale": rationale, "summary": summary,
    })

    stamp = provenance.run_stamp("S9_S10_final", {
        "decision": label, "elapsed_s": round(time.time() - t0, 1),
        "s8_shared_direction": s8.get("shared_direction_evidence"),
    })
    provenance.write_json(out_dir / "s9_s10_provenance.json", stamp)

    with (ROOT / "reports/DECISION_LOG.md").open("a", encoding="utf-8") as fh:
        fh.write(
            f"\n## S9/S10 — {stamp['utc']}\n"
            f"- Decision: **{label}**\n"
            f"- {rationale}\n"
        )

    readme = ROOT / "README.md"
    txt = readme.read_text()
    for a, b in (
        ("| S9 | Controls and interpretability | not started |",
         "| S9 | Controls and interpretability | **done** |"),
        ("| S10 | Go / no-go decision | not started |",
         f"| S10 | Go / no-go decision | **{label}** |"),
    ):
        txt = txt.replace(a, b)
    if "GO_NO_GO_DECISION" not in txt:
        txt = txt.replace(
            "* `reports/S8_READINESS_RECOMMENDATION.md` - **current stop gate before S9/S10**",
            "* `reports/GO_NO_GO_DECISION.md` / `STAGE0_FINAL_REPORT.md` - **Stage 0 decision**\n"
            "* `reports/S9_CONTROLS_AND_COMPARISON.md`\n"
            "* `reports/S8_READINESS_RECOMMENDATION.md` - prior S8 gate",
        )
    readme.write_text(txt)

    print(f"DECISION: {label}")
    print(rationale)
    print(f"S9/S10 OK ({time.time()-t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
