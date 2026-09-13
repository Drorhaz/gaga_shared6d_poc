# Pooled method definition — ex09–ex13 hard-boundary block

**Date:** 2026-08-07  
**Workspace:** `gaga_shared6d_poc/pooled_ex09_13/`  
**Primary contrast:** D12 (T1→T2); D13 supplemental  
**Participants:** 252, 651, 671, 790 × T1/T2/T3 × R1/R2 (= 24 recording units)

---

## Binding pooled definition

For each `participant × timepoint × repetition`, the analysis unit is the set of all valid observations from exercises **09–13**.

### Hard boundary rule (non-negotiable)

Observations from all five exercises belong to one pooled **dataset**, but temporal continuity remains **exercise-specific**.

**MUST NOT cross exercise boundaries:**

- finite differences / angular velocity  
- lagged correlations  
- Conv / Transformer / explicit feature windows  
- RQA delay embeddings / Theiler / surrogate blocks  
- any operation assuming temporal adjacency  

**Allowed:**

- pool **statistics** or **clouds of within-exercise observations**  
- equal-weight aggregation across the five exercises after within-exercise processing  

Boundary indices for every exercise are stored in `manifests/pooled_input_manifest.csv`.

---

## Method-by-method definition

### 1. JcvPCA (Project A — READ-ONLY reference)

| Item | Definition |
|---|---|
| Current input | Marker-gap stack `ex09_13_contiguous`: frame slices for ex09–13 **row-concatenated** (soft splice into one cloud for PCA) |
| Proposed pooled input for this phase | **Do not recompute.** Extract authoritative A2/S3/coverage/NV as the reference table |
| Boundary handling | Soft-concat is the **historical committee estimand** (cloud PCA; not derivative-based). Hard-boundary recompute would be a **new estimand** → not authorized here |
| Retrain? | N/A |
| Inference reuse? | Extract-only |
| R1/R2 | Signed NV: T1 R1 vs R2 on same window definition |
| Output | `outputs/jcvpca_reference.csv` with provenance paths |
| Estimand change? | **None** — frozen marker-gap results unchanged |

**STOP avoided:** we do not redefine A2.

---

### 2. Explicit features

| Item | Definition |
|---|---|
| Current input | 2 s within-exercise windows → `window_features.csv`; recording-level = mean within exercise → **equal-weight mean across ex09–13** |
| Proposed pooled input | Same equal-weight recipe, rebuilt under this workspace from window features **and** verified against segment boundaries |
| Boundary handling | Features computed only within windows/segments that never cross exercises; pooling is post-hoc equal-weight across exercises |
| Retrain? | No |
| R1/R2 | `|C(T,R1) − C(T,R2)|` on pooled recording feature |
| Output | `outputs/explicit/` |
| Estimand change? | **None** vs locked shared6d recording aggregation; re-derived for provenance |

Distribution features (energy, entropy, dimensionality, symmetry): within-exercise window means → equal-weight across exercises.  
Temporal features (coupling): see §3–4.

---

### 3. `regional_coupling`

| Item | Definition |
|---|---|
| Current | Signed zero-lag mean pairwise corr of regional **speed-magnitude** series within each window |
| Pooled | Per-exercise aggregate (mean of windows in that exercise) → equal-weight mean across ex09–13 |
| Boundary | No series concatenation; no cross-exercise covariance |
| R1/R2 / D12 / D13 | On pooled scalar |
| Estimand | Same construct as recording-level `regional_coupling` |

---

### 4. `trunk_arm_lagged_coupling`

| Item | Definition |
|---|---|
| Current | max \|corr\| trunk vs mean-arms over lags −5…+5 frames (~±42 ms @ 120 Hz) within window |
| Pooled | Same as §3: per-exercise then equal-weight |
| Boundary | Lagged pairs remain inside one exercise/window; **never** across boundaries |
| Not Chang joint-angle xcorr | Confirmed |

---

### 5. PCA reference

| Item | Definition |
|---|---|
| Current | Per-window 108-D → PCA 32-D; recording aggregation identical to Conv |
| Pooled | Reuse frozen recording embeddings / identity probe; report D12/D13 vs Drep as **reference only** |
| Retrain? | No (do not refit on T2/T3) |
| Role | REFERENCE — not primary longitudinal outcome |
| Newell guardrail | Dimensionality direction ≠ better/worse |

---

### 6. Conv

| Item | Definition |
|---|---|
| Current | Within-exercise 2 s windows; frozen `masked_angular_velocity` Conv; embed → mean within exercise → equal-weight across ex09–13 |
| Proposed | **Reuse frozen checkpoints / existing `s7_conv` recording embeddings and `change_magnitudes.csv`** — already the pooled hard-boundary estimand |
| Retrain? | **Not authorized / not required** |
| Boundary | Windows never cross exercises (`s4_window.py`) |
| R1/R2 | Embedding Drep between R1 and R2 at same T |
| Output | `outputs/conv/` extracted + summarized |
| Estimand change? | None |

**STOP if** splicing multi-exercise sequences into the Conv receptive field — we do not do that.

---

### 7. Transformer

| Item | Definition |
|---|---|
| Same window/aggregation logic as Conv | Sensitivity only |
| Reuse frozen s6 outputs | Yes |
| Retrain? | No |
| Question | Does architecture preference change under pooled evaluation? (Expect: no) |

---

### 8. RQA

| Item | Definition |
|---|---|
| Current Stage2 | Exercise-resolved; focus 651/790 × ex11/ex13; gate `LIMITED_PASS_STOP` |
| **Chosen pooled estimand: B — boundary-block recurrence** | Compute Auto-RQA **within each exercise segment**, then **equal-weight mean** of metrics (DET, LAM, Lmean, ENTR) across ex09–13 for each pid×T×R |
| Rejected: A — pooled state-set recurrence | Would allow cross-exercise state recurrence; scientifically interesting but **not** implemented in frozen pipeline and would be a new exploratory estimand |
| Rejected: continuous concat | Synthetic boundaries — **forbidden** |
| Parameters | Stage1 lock: 120 Hz, τ=18, m=4, radius 0.35×mean (amp-preserving); not retuned on T2/T3 |
| Retrain / Stage3? | No |
| Coverage note | Stage1 metrics currently exist only for 651/790 × ex11/13. Pooled RQA therefore **requires new within-exercise Auto-RQA** for the full 120-segment grid under `pooled_ex09_13/outputs/rqa/` (isolated; does not modify freeze) |
| If full recompute fails/too costly | Report available cells + mark missing as `NOT_COMPUTABLE_IN_PHASE` rather than silently approximate |

---

## Common R1/R2 logic

For method-specific quantity `C` at a timepoint:

`Drep(T) = |C(T,R1) − C(T,R2)|`

`D12 = distance/change between pooled T1 and T2` (method-specific; for scalars often mean of matched R1/R2 deltas or \|mean(T2)−mean(T1)\| as documented per method)

Categorical:

- `EXCEEDS` — longitudinal > own Drep with direction consistency where applicable  
- `WITHIN` — ≤ Drep  
- `UNRELIABLE` — gates fail / opposite-sign reps / unstable Drep  
- `NOT_INTERPRETABLE`

No cross-method magnitude comparison.

---

## Stop-condition checklist (pre-execution)

| Condition | Status |
|---|---|
| Changing original segmentation | Not required |
| Inconsistent preprocessing | Not required — reuse immutable rotvec + frozen windows |
| Conv/Transformer require retrain | **No** — inference/extract only |
| RQA needs synthetic boundaries | **No** — choose block-B |
| Missing source data | Segment index 120/120 present; rotvec parquet present |
| Changing JcvPCA definition | **No** — extract-only |

**Proceed** under these locked definitions.
