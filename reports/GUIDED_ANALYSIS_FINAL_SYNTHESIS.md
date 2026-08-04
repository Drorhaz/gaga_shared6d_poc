# Guided Analysis — Final Synthesis (Thesis Freeze Package)

**Freeze date:** 2026-08-04  
**Closeout antecedent:** `GUIDED ANALYSIS COMPLETE WITH EXPLORATORY EXTENSIONS`  
**Freeze outcome:** **GUIDED RESULTS FROZEN WITH DOCUMENTATION GAPS**  
**Shared-direction status:** closed (`shared_direction_evidence=False`)  
**Next scientific question (not started):** Does the structured-trained Conv representation transfer reliably to free movement?

This document freezes the guided-improvisation (Group4 / ex09–ex13) analysis for thesis packaging.
It synthesizes completed Stage 0 → Stage 0B-A2 reports. **No new scientific results were computed
for narrative gaps.**

---

## 1. What was tested?

Within N=4 participants (252, 651, 671, 790) and timepoints T1/T2/T3, using a frozen canonical
18-link 6D representation and a reliability-gated `ConvMaskedPredictor`
(`masked_angular_velocity`, mask 30%, 2 folds × 3 seeds):

1. Can Conv embeddings detect within-participant longitudinal change larger than within-session
   R1/R2 repetition variability (Drep)?
2. Can change be localized to supported exercise blocks ex09–ex13?
3. Do explicit coordination features (and amplitude residuals) support interpretable descriptions?
4. Is there a stable shared cross-participant change direction?
5. Do Transformer, masked-6D, PCA, clustering/motifs, or P1–P5 stages improve or justify
   alternative confirmatory frameworks?

Unit of inference: **within-participant**, not group-level learning.

---

## 2. Which analyses passed?

| Analysis | Status | Evidence |
|---|---|---|
| Representation / preprocessing validation | Pass | Stage S3 / S3b / S4 reports |
| Mask ratio freeze at 30% | Pass | S5 mask sweep |
| Angular-velocity objective selection | Pass | S5/S6 objective reports |
| Conv reliability gate (framework) | Pass | `outputs/s7_conv/RELIABILITY_GATE.json` |
| Conv change magnitude vs Drep (many gated cells) | Pass (partial) | S7; Stage 0B-A profiles |
| Explicit features + amp residuals vs R1/R2 | Pass (descriptive) | Stage 0B-A |
| Exercise localization ex09–ex13 | Pass (participant-specific) | Stage 0B-A / A2 |
| Guided closeout under LIMITED GO | Pass | Stage 0B-A2 final |

---

## 3. Which analyses failed or were not supported?

| Analysis | Status |
|---|---|
| Masked 6D reconstruction as selected objective | Failed |
| Transformer outperforming matched Conv | Failed |
| Stable shared cross-participant direction | Failed (`S8_GATE`) |
| Stable clustering / motif repertoire | Not justified |
| P1–P5 progressive cue segmentation | Unsupported by annotations |
| Uniform reliability across all participant×fold×seed cells | Failed (esp. 671; some 790/651) |
| Group-level / population learning claims | Not supported (N=4) |

---

## 4–7. Result hierarchy

### Primary findings
1. Reliability-gated explicit coordination features and amplitude-residual measures, compared with R1/R2.
2. Participant-level longitudinal profiles with exercise localization on ex09–ex13.
3. Conv change magnitude as a **reliability-gated detector/localizer** of individual change
   (recording and exercise levels), not as a biomechanical explanation by itself.

### Supporting findings
- Conv vs PCA identity/loading comparisons (PCA = reference only).
- Conv–explicit agreement/disagreement patterns.
- Method selection: velocity Conv preferred over Transformer / 6D.

### Exploratory findings
- Early/middle/late temporal thirds.
- Latent path length / spread / mean-position shift.
- Inference-time region occlusion (OOD risk).

### Not supported (must retain)
- Shared direction; clustering/motifs; P1–P5 stages; Transformer primacy; amplitude-only explanations
  for all changes; group-level Gaga strategy claims.

---

## 8. Participant-level reliability (summary)

Full table: `reports/GUIDED_ANALYSIS_PARTICIPANT_SUMMARY.md` and
`outputs/guided_analysis_finalization/participant_synthesis_table.csv`.

| Participant | Strongest reliable claim | Caution |
|---|---|---|
| **651** | Reliable T1→T2 and T1→T3 change >Drep with amp-residual entropy/dimensionality support | 5/6 cells; not universal folds/seeds |
| **790** | Reliable T1→T2 and T1→T3 change >Drep; strong D13 latent ratio; amp-residual entropy/dimensionality | 4/6 typical; endpoint failures exist |
| **252** | Reliable endpoints; **T1→T3** change >Drep with symmetry/coupling residuals | **T1→T2 ≤Drep** — do not overclaim D12 |
| **671** | Sparse reliable cells; limited endpoint skill (T1 3/6, T3 2/6) | Treat as limited reliability overall |

---

## 9–10. Thesis figures / tables

See:
- `reports/GUIDED_ANALYSIS_THESIS_FIGURE_PLAN.md`
- `reports/GUIDED_ANALYSIS_THESIS_RESULTS_OUTLINE.md`
- Selected copies: `figures/guided_analysis_thesis_selected/` (originals untouched)

Minimal tables: reliability/inclusion; participant change summary; exercise localization;
explicit-feature summary; method/negative findings. Fold×seed matrices → supplement.

---

## Evidence inventory

Machine-readable: `outputs/guided_analysis_finalization/evidence_inventory.csv`

| result | source_report | source_output | reliability | role | thesis |
| --- | --- | --- | --- | --- | --- |
| Conv reliability gate PASS (means>0; ≥50% positive cells T1/T2/T3) | reports/S6B_CONV_RELIABILITY_GATE.md | outputs/s7_conv/RELIABILITY_GATE.json | framework-level PASS; per-cell failures retained | primary | True |
| Many reliability-qualified Conv \|Δ\| exceed Drep (within-session R1/R2) | reports/S7_EMBEDDING_CHANGE_REPORT.md | outputs/s7_conv/change_magnitudes.csv | cell-gated | primary | True |
| Explicit coordination features vs R1/R2 with amp residuals | reports/STAGE0B_A_FEATURE_INTERPRETATION.md | outputs/stage0b_individual_profiles/recording_feature_changes.csv | descriptive at N=4; majority-fold exceedances | primary | True |
| Participant-level profiles (651/790 strongest; 252 mainly D13; 671 limited) | reports/STAGE0B_A_INDIVIDUAL_PROFILES.md | outputs/stage0b_individual_profiles/individual_profiles.csv | per-comparison status tags | primary | True |
| Exercise localization ex09–ex13 (participant-specific; no shared pattern) | reports/STAGE0B_A_EXERCISE_CONTRIBUTIONS.md | outputs/stage0b_guided_closeout/exercise_level_change.csv | reliable cells only | primary | True |
| Conv recording/exercise \|Δ\|/Drep localization | reports/STAGE0B_A2_EXERCISE_TEMPORAL_LOCALIZATION.md | outputs/stage0b_guided_closeout/exercise_level_change.csv | gated | supporting | True |
| PCA identity-dominant; reference only | reports/S9_CONTROLS_AND_COMPARISON.md | outputs/s9_final/ | n/a method comparison | supporting | True |
| Conv vs Transformer: Conv preferred (velocity objective) | reports/S6_TRANSFORMER_VS_CONV.md | outputs/s6_transformer/ | matched runs | supporting | True |
| Early/middle/late thirds within exercises | reports/STAGE0B_A2_EXERCISE_TEMPORAL_LOCALIZATION.md | outputs/stage0b_guided_closeout/tertiary_block_change.csv | exploratory | exploratory | False |
| Latent path/spread/mean-shift temporal dynamics | reports/STAGE0B_A2_TEMPORAL_DYNAMICS.md | outputs/stage0b_guided_closeout/temporal_dynamics.csv | exploratory | exploratory | False |
| Inference-time region occlusion | reports/STAGE0B_A2_REGION_ATTRIBUTION.md | outputs/stage0b_guided_closeout/region_occlusion_A0.csv | OOD risk; Fold A seed0 sensitivity | exploratory | False |
| No stable shared cross-participant direction | reports/S8_DIRECTION_SIMILARITY_REPORT.md | outputs/s8_direction/S8_GATE.json | negative retained | negative | True |
| Masked 6D objective failed vs angular velocity | reports/S6_OBJECTIVE_SELECTION.md | outputs/s5_conv/ | negative retained | negative | True |
| Transformer did not outperform matched Conv | reports/S6_TRANSFORMER_VS_CONV.md | outputs/s6_transformer/ | negative retained | negative | True |
| Clustering/motifs not justified | reports/STAGE0B_A2_REPERTOIRE_CLUSTERING.md | outputs/stage0b_guided_closeout/repertoire_summary.json | negative retained | negative | True |
| P1–P5 progressive cue stages unsupported | reports/STAGE0B_A2_GUIDED_SEGMENTATION.md | outputs/stage0b_guided_closeout/guided_segmentation.csv | annotation fact | negative | True |
| Some participant×fold×seed cells fail reliability gate | reports/S6B_CONV_RELIABILITY_GATE.md | outputs/s7_conv/reliability_t1_t2_t3.csv | excluded from interpretable claims | negative | True |
| Stage 0 LIMITED GO; guided closeout COMPLETE WITH EXPLORATORY EXTENSIONS | reports/GO_NO_GO_DECISION.md / STAGE0B_A2_FINAL_RECOMMENDATION.md | outputs/s9_final/GO_NO_GO.json | decision | supporting | True |

---

## Freeze notes

- Historical reports are preserved unchanged.
- Consistency issues are documented in `GUIDED_ANALYSIS_CONSISTENCY_AUDIT.md` (amendment notes only).
- Reproducibility uses content hashes because this project directory is **not** a git repository
  (documentation gap; see manifest).
