# Stage 1 Implementation Summary

**Package:** `rqa_guided_pilot/`  
**Branch:** `exploratory/guided-rqa-plan`  
**Freeze (scientific, untouched):** `guided-analysis-freeze-v1` @ `5062e22`  
**Pre-freeze audit:** `STAGE1_FREEZE_APPROVED_WITH_DOCUMENTATION_FIXES`  
**Stage 1 decision:** `PASS_TO_STAGE2`

## Isolation

All RQA artifacts under `rqa_guided_pilot/`. Frozen inputs read-only. External touch: root `.gitignore` only (`manifests/EXTERNAL_TOUCHES.md`).

## Locked parameters (T1-only)

| Parameter | Value | Physical time |
|---|---|---|
| Primary rate | **120 Hz** | — |
| τ | **18 frames** (band 17–19) | **0.15 s** |
| m | **4** | embed span **0.45 s** |
| Theiler | 18 | 0.15 s |
| Lmin | 2 | Stage 2: also test 3 (DET ceiling) |
| Block shuffle | 36 frames | **0.30 s** (secondary control) |
| Fixed radius | **0.35 × mean distance** | RR median ≈ 3.6% |
| Target RR (z-score) | 0.03 | RR not a DV |

AMI/FNN used all four participants × R1/R2 × ex09–ex13 × regions at T1. Rate bake-off used physically matched τ (0.15 s → 18/9/4 frames at 120/60/30 Hz).

## Why 120 Hz

Under physically matched τ and radius 0.35, 120 Hz had the lowest T1 R1/R2 DET variability and strongest full-shuffle DET disruption. 60 Hz was qualitatively consistent; 30 Hz weaker. Physical Lmean was not inflated at 120 Hz vs 30 Hz. See `STAGE1_PRE_FREEZE_AUDIT.md`.

## Surrogates

- **Full shuffle (primary):** median DET drop ≈ 0.93 — validates temporal sensitivity.
- **Block shuffle (secondary):** weak DET drop at near-ceiling DET; clearer Lmean reduction; distinguishable from full shuffle.

## Gate highlights

- RR in 1–10% band after radius 0.35.
- R1/R2 not pathological (no 15%/70% hard rules).
- Duration truncation does not abolish structure.
- τ-band DET stable.

## Reproduce

```bash
.venv/bin/python rqa_guided_pilot/scripts/run_stage1.py
```

Manifests: `manifests/stage1_run_manifest.json`, `stage1_input_hashes.json`, `stage1_environment.json`.

## Next

Stage 2 only after Git tag `rqa-stage1-feasibility-pass-v1`, on branch `exploratory/guided-rqa-stage2`.
