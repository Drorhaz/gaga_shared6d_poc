# RQA Computational Estimate

**Freeze:** `guided-analysis-freeze-v1` @ `5062e22`  
**Branch:** `exploratory/guided-rqa-plan`  
**Goal:** Cheapest design that still answers the scientific question.

---

## 1. Workload inventory

| Quantity | Stage 1 (longitudinal subset) | Stage 3 upper bound |
|---|---|---|
| Guided segments | 16 (2 pid × 2 ex × 2 TP × 2 rep) | 120 |
| Auto-RQA signals | ~5–6 regions (+ optional total) | same |
| Compact MdRQA | 0–1 per segment | 1 per segment |
| CRQA | 0 in Stage 1; +1 pair in Stage 2 | optional |
| Rate conditions | 120 / 60 / 30 until lock | primary (+ neighbor if needed) |
| Normalization views | 2 | 2 |
| Sensitivity combos | ~20–40 (narrow grid) | locked defaults + narrow grid |
| Surrogates | 2 per evaluated series (shuffle, block) | diagnostic subset |

T1 AMI/FNN diagnostics additionally scan all 4 pids × R1/R2 × ex09–ex13 × regions at candidate rates (parameter estimation only; not full longitudinal grid).

---

## 2. Matrix sizes and memory

Embedded length \(N_{\mathrm{embed}}\) roughly tracks segment duration × rate (minus embedding span).

| Rate | Duration 10 s (median) | Approx \(N\) | Float64 distance matrix |
|---|---|---|---|
| 120 Hz | ~1200 | ~1200 | ~11 MB |
| 60 Hz | ~600 | ~600 | ~3 MB |
| 30 Hz | ~300 | ~300 | ~0.7 MB |
| 120 Hz × 18 s | ~2160 | ~2160 | ~37 MB |

Peak memory reporting must use **float pairwise-distance matrices**, not only binary recurrence plots.

Binary / sparse RPs after thresholding are smaller and need not be stored for every cell.

---

## 3. Design comparison

| Design | Scientific fit | Cost | Pilot decision |
|---|---|---|---|
| Full-resolution 120 Hz always | Oversampled after 10 Hz filter | Highest | Compare in Stage 1; lock empirically |
| Downsampled 60 Hz | Likely best compromise | Medium | Strong candidate primary |
| 30 Hz diagnostic | Artifact check | Lowest | Diagnostic only |
| Full-exercise RQA | Matches short segments | Necessary | **Primary unit** |
| Sliding-window RQA | Paper default for long trials | Poor fit (segments too short for ~1000-sample windows after downsample) | **Not primary** |
| Auto-RQA regional | Answers intensity-dynamics questions | Efficient | **Primary method** |
| Compact MdRQA 4–6D | Multiregion state | Moderate | Secondary |
| 18-link MdRQA | High-D collective state | Expensive; weakly justified | **Out of scope** |

---

## 4. Required efficiency rules (implementation)

The implementation **must**:

1. Cache embedded trajectories per `(signal, rate, τ, m)`.
2. Compute each float pairwise-distance matrix **once** per `(signal, rate, τ, m)`.
3. Reuse that distance matrix across radius / target-RR settings.
4. Avoid storing every recurrence matrix; keep numerical metrics + small diagnostics as primary outputs.
5. Save recurrence plots only for representative and pathological cases.
6. Prevent duplicated work across sensitivity settings (factorize by embedding → distance → threshold sweep).
7. Report peak memory based on float distance matrices.
8. Apply surrogates to the same cached pipeline without recomputing unrelated embeddings.

---

## 5. Runtime expectation

| Phase | Expected runtime (laptop/workstation CPU) |
|---|---|
| T1 AMI/FNN + rate diagnostics | Minutes to ~1 hour |
| Stage 1 Auto-RQA + surrogates + truncation | Minutes to low hours |
| Stage 2 (add T2, amp views, optional CRQA) | Low hours |
| Stage 3 full grid with reuse | **Hours, not days** |

If runtime approaches days, the design has violated reuse/caching or expanded the grid — stop and reduce, do not silently widen scope.

---

## 6. Storage expectation

| Artifact | Policy |
|---|---|
| Metric tables (CSV/Parquet) | Keep |
| AMI/FNN diagnostic plots | Keep representatives |
| Full distance matrices | Ephemeral / optional cache; not long-term bulk archive |
| All RPs | Do not store |
| Selected RPs | Representative + pathological only |
| Frozen Conv/explicit outputs | Read-only references |

---

## 7. Most efficient scientifically adequate design

1. Extract Candidate A regional speeds once from frozen rotvec.
2. T1-only AMI/FNN/rate bake-off with caching.
3. Lock primary rate + common \((\tau,m)\) band.
4. Stage 1 full-exercise Auto-RQA on 651/790 × ex11/ex13 with distance reuse, surrogates, truncation sensitivity.
5. Compact MdRQA only after Auto-RQA is technically stable.
6. CRQA only after Stage 1 gates.
7. Expand to Stage 3 only with locked parameters.

This answers complementarity vs redundancy without 18-link MdRQA, sliding windows, or retraining.
