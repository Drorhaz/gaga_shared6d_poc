# Existing-analysis inventory (cross-project)

Read-only inventory of what was actually computed. Project files are source of truth.

| Method | Construct | Input representation | Unit of analysis | Timepoint comparison | Exercise resolution | Anatomical resolution | Participant resolution | R1/R2 reference | Reliability criteria | Amplitude control | Main positive findings | Main negative / failed findings | Known limitations | Scientific status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **JcvPCA** | Link relative contribution redistribution in T1 retained subspace | Relative link rotvecs → JcvPCA | Link × comparison (pooled ex09–13 primary) | T1→T2, T1→T3 | Layer-2 per-exercise NV (firewalled); primary = pooled | Link-level (Setup A/B maps) | 252,651,671,790 N-of-1 | Signed NV: T1 R1↔R2 | S2 = exceed + sign stable; coverage; rep_pass for S3 | Step-5 ROM flat band + org/amp/mixed | A2 present in all 4 pids at D12; S3=4 in 671 T2; persistence strongest in 671 | A3 not supervisor-approved; 651 pre-policy S3 stale; many org labels ≠ S3 | Reference-basis asymmetry; single-rep NV floor; marker-gap exclusions (esp. 651) | **Primary narrative method** |
| **Conv** | Learned detector of longitudinal movement-dynamics change | Masked angular-velocity objective on 6D/rotvec windows | Embedding \|Δ\| at recording / exercise | D12, D13, D23 | Yes (`exercise_level_change.csv`) | Regional exploratory (Stage0B), not link-level | Same 4 | Embedding Drep from R1 vs R2 | Reliability gate PASS; per-cell skill>0 required | Amp residuals on features; energy correlation flags | Gate pass; 651/790/671 D12 >Drep in reliable cells; exercise localization | masked_6D failed; 252 D12 ≤Drep; 671 sparse cells | Session–timepoint confounding; fold/seed failures | **Primary complementary detector** |
| **Explicit features** | Interpretable biomechanical / coordination descriptors | Link angular speed → regional aggregates | Window / recording / exercise × feature | D12, D13 | Yes | Regional (6 regions), not joint-pair anatomical | Same 4 | Feature \|Δ\| vs Drep_max | `reliable_fold_any_seed` | `*_amp_residual` columns | Entropy/dim/active-region (651/790); symmetry/coupling (252); coupling (671 sparse) | Regional speed coupling ≠ Chang joint phase | Descriptive only; Newell: dim direction not universal | **Interpretation aid** |
| **RQA** | Temporal recurrence / predictability of intensity dynamics | A1: regional angular-velocity magnitude; B2 secondary hand speed | Region × exercise × metric | D12 (Stage2 focus), D13 Stage1 | Yes (Stage2) | Regional | Stage2 focus N=2 (651,790) for novelty cells; Stage1 broader | Metric Drep R1/R2 | Surrogate, truncation, sensitivity OK | Amp-preserving view; z-score novelty bar | Tech valid; 2 amp-preserving complementary cells | 0 z-score novel; Stage3 not recommended | DET ceiling; not amplitude-independent novelty | **`LIMITED_PASS_STOP`; not primary longitudinal** |
| **Transformer** | Architecture sensitivity vs Conv | Same masked_angular_velocity | Same as Conv | Same | Limited vs Conv | Same latent | Same 4 | Same Drep family | Skill comparison | — | Only velocity objective positive | masked_6D fail; Conv preferred (skill 0.036 vs 0.029) | No clear advantage | **Sensitivity only** |
| **PCA** | Linear identity reference | Link features → PCA space | Identity probe | — | — | — | Cohort | — | Identity accuracy | — | Identity ~0.79–0.89 (chance 0.25) | Not longitudinal outcome | Different construct from JcvPCA redistribution | **Reference, not primary outcome** |

## Authoritative path cheat sheet

### Project A — JcvPCA
- Claims: `gaga_jcvpca/results_committee_case/step00_claim_framework/CLAIMS.md`
- Stack: `.../marker_gap_policy_ex09_13/`
- NV: `.../step08_nv_and_stability/NV_PROFILE.csv`
- Headline: `.../tables_to_show/09_headline_a2_summary.csv`
- Step 5: `.../step05_amplitude_vs_organization/classification_summary.md`
- Persistence: `.../step09_persistence_t2_t3/persistence_summary.md`

### Project B — Conv / features / RQA
- Conv change: `gaga_shared6d_poc/outputs/s7_conv/change_magnitudes.csv`
- Reliability: `.../outputs/s7_conv/reliability_t1_t2_t3.csv`, `RELIABILITY_GATE.json`
- Exercise localization: `.../outputs/stage0b_guided_closeout/exercise_level_change.csv`
- Profiles: `.../outputs/stage0b_individual_profiles/individual_profiles.csv`
- Features: `.../outputs/s5_explicit/`, `exercise_feature_changes.csv`
- Freeze: `.../outputs/guided_analysis_finalization/`, `reports/GUIDED_ANALYSIS_*.md`
- Transformer: `.../outputs/s6_transformer/ARCHITECTURE_RECOMMENDATION.json`
- PCA: `.../outputs/s5_pca/`, `reports/S5_PCA_BASELINE_REPORT.md`
- RQA: `.../rqa_guided_pilot/reports/STAGE2_*.md`, `outputs/stage2/STAGE2_GATE.json`

## What cannot be compared directly

JcvPCA signed NV, Conv embedding Drep, RQA metric Drep, and feature Drep are **method-specific** within-session repetition floors. They share a conceptual role but are **not numerically equivalent**. Cross-method synthesis uses categorical exceed/not-exceed and role-tagged evidence, not magnitude voting.
