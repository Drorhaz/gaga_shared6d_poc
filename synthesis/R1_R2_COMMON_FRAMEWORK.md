# Common R1/R2 (within-session repetition) framework

## Shared scientific question

> Does the longitudinal change exceed that method’s **own** within-session repetition variability?

Do **not** compare raw effect magnitudes across methods.

---

## Method-specific definitions

### JcvPCA — signed natural variability (NV)

| Item | Definition |
|---|---|
| Repetitions | T1 take R1 vs T1 take R2 (separate takes) |
| Quantity | `nv_signed` = EVR-weighted signed sum of link JcvPCA across retained PCs for `T1_R1 vs T1_R2` |
| Longitudinal | `long_signed` = `T1_R1 vs T{2,3}_R1` (A2 estimand) |
| Exceed | `\|long_signed\| > \|nv_signed\|` |
| Direction gate | `sign(long_signed) = sign(long_signed_rev)` with `long_signed_rev = T1_R2 vs T{k}_R1` → S2/A2 |
| Source | `NV_PROFILE.csv`, `CLAIMS.md` |

Pooled longitudinal headline is descriptive only; A2 gate is single-rep signed.

### Conv — embedding Drep

| Item | Definition |
|---|---|
| Repetitions | Trajectory/repetition 1 vs 2 embeddings at a timepoint |
| Quantity | `Drep_T*` = embedding distance between R1 and R2 at that timepoint |
| Longitudinal | `norm_D12`, `norm_D13` = distance between timepoint embeddings |
| Exceed | e.g. `ratio_D12_over_DrepT2` or ratio vs `drep_max` > 1 (project reports use median across fold×seed) |
| Reliability | Per-cell positive skill required; gate PASS cohort-level |
| Source | `outputs/s7_conv/change_magnitudes.csv`, `individual_profiles.csv` |

### Explicit features — feature Drep

| Item | Definition |
|---|---|
| Repetitions | Feature values at R1 vs R2 (window/recording aggregates) |
| Quantity | `drep_max` over relevant repetition contrasts for that feature |
| Longitudinal | `abs_delta` of feature T1→T2 or T1→T3 |
| Exceed | `ratio_vs_drep_max > 1` (`exceeds_drep_max`) |
| Amp control | Parallel `*_amp_residual` features |
| Source | `exercise_feature_changes.csv`, `recording_features*.csv` |

### RQA — metric Drep

| Item | Definition |
|---|---|
| Repetitions | RQA metrics (DET/LAM/…) on R1 vs R2 segments |
| Quantity | Absolute difference of metric between R1 and R2 |
| Longitudinal | Δ metric across timepoints |
| Exceed | Novelty / complementary rules vs median \|Δ\|/Drep (Stage 2) |
| Source | `rqa_guided_pilot/outputs/stage2/r1r2_drep.csv`, Stage2 reports |

### Proposed cross-correlation (not computed)

If ever approved: Fisher-z of signed r0; `Drep,T = \|z(R1)−z(R2)\|`; longitudinal Δz matched by repetition. Classification remains `XCORR_OPTIONAL_BACKUP_ONLY`.

---

## Comparability classes

| Class | Meaning | Allowed use |
|---|---|---|
| **Exact numerical** | Same scalar quantity | **Not available** across methods |
| **Conceptual** | Within-session repetition floor for that method | Primary cross-method framing |
| **Categorical** | PRESENT / ABSENT / LIMITED / UNRELIABLE exceed of own floor | Participant matrix cells |

---

## Operational synthesis rule

For each method × participant × comparison:

1. State whether longitudinal change is interpretable under that method’s reliability gates.
2. State whether it **exceeds** that method’s R1/R2 floor (categorical).
3. Assign evidence **role** (detection / localization / interpretation / …).
4. Only then ask whether roles support convergent, complementary, discordant, or insufficient narratives.

D12 is the shared primary comparison; D13 is supplemental.
