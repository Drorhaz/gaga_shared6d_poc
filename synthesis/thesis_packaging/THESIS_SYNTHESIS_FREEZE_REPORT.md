# Thesis synthesis freeze report

**Date:** 2026-08-07  
**Phase:** Thesis result packaging (no new scientific computation)  
**Project B path:** `/Users/drorhazan/Desktop/gaga_psilo/projects/gaga_shared6d_poc`  
**Project A (READ-ONLY):** `/Users/drorhazan/Desktop/gaga_psilo/projects/gaga_jcvpca`

---

## Git state at freeze documentation

| Item | Value |
|---|---|
| Branch | `exploratory/guided-rqa-stage2` |
| HEAD (short) | `4c3f075` |
| Remote tracking | `origin/exploratory/guided-rqa-stage2` |
| `synthesis/` at freeze | **Untracked** in working tree (packaging docs created under it) |
| Freeze git commit/tag | **Not created in this packaging phase** — awaiting separate approval before commit/tag; do **not** merge to `main` |

---

## Authoritative evidence set

### JcvPCA (Project A — READ-ONLY)

- Claims: `gaga_jcvpca/results_committee_case/step00_claim_framework/CLAIMS.md`
- Marker-gap stack: `.../marker_gap_policy_ex09_13/`
- Headline A2/S3: `.../tables_to_show/09_headline_a2_summary.csv`
- NV tiers: `.../step08_nv_and_stability/NV_PROFILE.csv`
- Step-5 org/amp: `.../step05_amplitude_vs_organization/classification_summary.md`
- Persistence: `.../step09_persistence_t2_t3/persistence_summary.md`
- Hierarchy audit: `synthesis/JCVPCA_EVIDENCE_HIERARCHY_AUDIT.md`

**Locked:** A2 = S2; A3 not formally supported; `51 organization ≠ A3`; D12 primary / D13 supplemental.

### Conv / explicit / Transformer / PCA (Project B — frozen guided analyses)

- Conv: `outputs/s7_conv/`, `outputs/stage0b_guided_closeout/exercise_level_change.csv`
- Profiles: `outputs/stage0b_individual_profiles/individual_profiles.csv`
- Explicit: `outputs/s5_explicit/window_features.csv`, `recording_features*.csv`
- Freeze package: `outputs/guided_analysis_finalization/`, `reports/GUIDED_ANALYSIS_*.md`
- Transformer: `outputs/s6_transformer/ARCHITECTURE_RECOMMENDATION.json`
- PCA reference: `outputs/s5_pca/`, `reports/S5_PCA_BASELINE_REPORT.md`

### RQA (isolated pilot — gate closed)

- `rqa_guided_pilot/outputs/stage2/STAGE2_GATE.json` → `LIMITED_PASS_STOP`
- Complementary cells: 651–ex13–D12; 790–ex11–D12 (amp-preserving)

### Coupling audit (aggregation of already-computed features only)

- `synthesis/EXISTING_COUPLING_R1_R2_AUDIT.md`
- `synthesis/EXISTING_COUPLING_LONGITUDINAL_RESULTS.csv`
- `synthesis/JCVPCA_COUPLING_CONCORDANCE.md`
- `synthesis/COUPLING_INTERPRETATION_SUMMARY.md`
- `synthesis/XCORR_FINAL_RECOMMENDATION.md` → `EXISTING_COUPLING_INFORMATIVE_BUT_LIMITED`

### Cross-method synthesis

- `synthesis/CROSS_METHOD_PARTICIPANT_MATRIX.md` + `.csv`
- `synthesis/SCIENTIFIC_CLAIM_LADDER.md`
- `synthesis/CROSS_METHOD_CONSTRUCT_MAP.md`
- `synthesis/R1_R2_COMMON_FRAMEWORK.md`
- `synthesis/CHANG_PAPER_IMPACT_REVIEW.md` (`ROADMAP_MINOR_UPDATE`)
- `synthesis/PRESENTATION_RECOMMENDATION.md`
- `synthesis/SYNTHESIS_IMPLEMENTATION_ROADMAP.md`

---

## Analyses included in the packaging narrative

1. Marker-gap JcvPCA A1/A2/S0–S3, coverage, persistence, Step-5 descriptive organization/amplitude  
2. Conv reliability + D12/D13 change vs Drep + exercise localization  
3. Explicit features (incl. amp residuals) as interpretation  
4. RQA Stage 2 limited complementary cells (not primary)  
5. Existing regional coupling R1/R2 longitudinal audit (window-mean aggregation only)  
6. Transformer sensitivity; PCA identity reference (secondary/reference only)  
7. Literature guardrails (Chang / Newell / Verrel) without reshaping claims  

---

## Analyses explicitly excluded

- New Chang-style joint-angle cross-correlation  
- Anatomical Cardan/Euler reconstruction from rotvecs  
- JcvPCA / Conv / Transformer / RQA / explicit / coupling recompute from raw motion  
- RQA Stage 3  
- Free-movement analysis  
- Clustering / motifs / new models  
- Causal Gaga or psilocybin inference  
- Group-level statistics across the four participants  
- Merge to `main`  

**Confirmation:** This packaging phase performs **documentation and narrative drafting only**. No new scientific computation was run.

---

## Known limitations (carry into thesis)

- N=4 participant-specific case studies; no cohort inference  
- Session–timepoint confounding  
- JcvPCA NV floor = single T1 R1–R2 pair  
- 651 anatomical incompleteness (A2 = 4/10 under marker-gap)  
- Coupling = regional speed-magnitude metrics, not Chang joint phase  
- A3 supervisor-gated  
- D13 often coverage-limited for JcvPCA  

---

## Packaging outputs in this folder

1. `THESIS_FINAL_FIGURE_SPECIFICATIONS.md`  
2. `THESIS_RESULTS_DRAFT.md`  
3. `THESIS_DISCUSSION_DRAFT.md`  
4. `SUPERVISOR_REVIEW_QUESTIONS.md`  
5. `THESIS_RESULT_PACKAGING_SUMMARY.md`  
6. This freeze report  
