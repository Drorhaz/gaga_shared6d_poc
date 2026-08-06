# Stage 2 B2 secondary analysis

**Classification:** `SECONDARY_COMPLEMENTARY_SUPPORTED`

B2 = pelvis/root-relative hand positional-speed magnitude (m/s).
Not part of the primary Stage 2 gate; cannot rescue a failed/limited A1 result.

## Scope

- Participants: 651, 790
- Exercises: ex11, ex13
- Channels: LHand / RHand root-relative speed
- T1-only parameter selection, then limited longitudinal sensitivity

## B2-specific parameters (T1-selected)

| Param | Value |
|---|---|
| rate | 60 Hz |
| τ | 12 frames (0.2000 s) |
| m | 3 |
| radius frac (mean) | 0.3 |
| Theiler | 12 |
| block shuffle | 0.3 s |

These are **not** the A1 Stage 1 locks.

## Empirical observations

- Median corr(B2 hand, A1 ipsilateral arm angular): **0.207**
- Median full-shuffle DET drop: **0.888**
- Median T1 R1/R2 |ΔDET|: **0.021428055141615387**
- Z-score longitudinal hits (|Δ|/Drep>1 descriptive): 13

| pid | ex | hand | delta | median ratio |
|---|---|---|---|---|
| 651 | 11 | LHand | D12 | 1.31 |
| 651 | 11 | LHand | D13 | 1.37 |
| 651 | 13 | LHand | D12 | 1.41 |
| 651 | 13 | LHand | D13 | 1.89 |
| 651 | 13 | RHand | D12 | 2.30 |
| 651 | 13 | RHand | D13 | 2.84 |
| 790 | 11 | LHand | D12 | 1.76 |
| 790 | 11 | LHand | D13 | 2.39 |
| 790 | 11 | RHand | D13 | 1.10 |
| 790 | 13 | LHand | D12 | 2.06 |
| 790 | 13 | LHand | D13 | 1.74 |
| 790 | 13 | RHand | D12 | 1.76 |
| 790 | 13 | RHand | D13 | 2.29 |

## Interpretation

Distinct from A1 (moderate corr) with some z-score longitudinal exceedances

Root-relative endpoint speed measures articulated displacement relative to the pelvis,
not regional joint-orientation-change intensity. Moderate correlation with A1 supports
a distinct construct without replacing A1.

## Comparison notes

- Compared against ipsilateral A1 arm angular speed (correlation).
- Surrogate disruption assessed under B2 params.
- Amplitude: amp-preserving + trial z-score (target-RR) both computed.
- Does not use PCA components as RQA input.

## Gate interaction

- `cannot_rescue_A1_gate`: true
- `promote_to_primary`: false
- Primary Stage 2 decision remains driven by A1 Auto-RQA.

## Limitations

- Bone positions require Length Units handling (T1 mm; 252_T3 meters not in this scope).
- No Procrustes / body-size normalization beyond root-centering.
- Small Stage 2 N; session–timepoint confounding remains.

Artifacts: `outputs/stage2/b2/`
