# Stage 1 Gate Report

**Decision:** `PASS_TO_STAGE2`  
**Pre-freeze audit:** `STAGE1_FREEZE_APPROVED_WITH_DOCUMENTATION_FIXES`  
**Primary rate (locked):** 120 Hz  
**τ / m:** 18 frames (0.15 s) / 4 (embed span 0.45 s)  
**Block shuffle:** 0.30 s (secondary; full shuffle is primary negative control)

## Technical checks

| Check | Value |
|---|---|
| RR median (amp-preserving, radius 0.35) | ~0.036 |
| RR in 1–10% band | True |
| Median DET drop (full shuffle) | ~0.93 |
| Fraction DET drop > 0 (full shuffle) | 1.00 |
| Surrogate disrupts DET (full shuffle) | True |
| Block-shuffle DET drop | Weak (~0.04); Lmean drop clearer — graded secondary control |
| R1/R2 not pathological (DET) | True |
| Truncation median \|ΔDET\| | ~0 |
| Tau-band median \|ΔDET\| | ~0.001 |

## Descriptive longitudinal (not sufficient alone)

- Fraction cells with \|ΔDET\|/Drep > 1 (amp-preserving): ~0.23
- Fraction cells with \|ΔDET\|/Drep > 1 (trial z-score): ~0.30

These ratios are **not** the Stage 1 pass criterion.

## Interpretation language

Regional Auto-RQA measures recurrence of **regional angular-velocity-magnitude dynamics**, not posture or anatomical pose recurrence.

## Next step

Freeze Stage 1 (`rqa-stage1-feasibility-pass-v1`), then Stage 2 on `exploratory/guided-rqa-stage2` upon approval.

Artifacts: `outputs/stage1/*.csv`, `outputs/locks/parameter_lock_stage1.json`, `STAGE1_PRE_FREEZE_AUDIT.md`.
