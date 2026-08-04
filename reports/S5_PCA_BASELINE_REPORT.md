# S5 PCA baseline report

**Observed data** from the validated primary path (filtered rotvec → matrix → 6D).
**Derived measurements** below. **Interpretation** is descriptive only; T2/T3
distances were not used for tuning.

---

## Method

| Item | Setting |
|---|---|
| Input | time-mean of each 2 s window’s 6D tensor, flattened to 108-D |
| Fit | `StandardScaler` + `PCA` on **training-T1 of the current fold only** |
| Dimensionality | 32 (full rank available; never reduced below 32) |
| Aggregation | windows → mean within exercise → equal-weight mean across ex09–13 |
| Held-out T1 | early-stop contiguous blocks (not used for fitting) |

---

## Results

### Explained variance and reconstruction

| Fold | Train windows | Held-out T1 | Variance explained (32 PCs) | MSE train | MSE held-out T1 |
|---|---|---|---|---|---|
| A | 403 | 120 | **0.932** | 0.00230 | 0.00562 |
| B | 439 | 91 | **0.921** | 0.00261 | 0.00547 |

Both folds recover >92% of the 108-D variance at d=32. Held-out reconstruction
MSE is about 2× train MSE — expected generalisation gap, stable across folds.

Figures: `figures/s5_pca/pca_fold_A.png`, `pca_fold_B.png`.

### Amplitude sensitivity

Correlation of PC1 with within-window movement energy on held-out T1:

| Fold | r(PC1, energy) |
|---|---|
| A | 0.001 |
| B | −0.015 |

PC1 is **not** an amplitude axis in this representation. Amplitude sensitivity
is therefore low for the leading component.

### Participant-identity probe (held-out T1)

| Fold | Accuracy | Chance | Above chance |
|---|---|---|---|
| A | **0.792** | 0.25 | +0.54 |
| B | **0.890** | 0.25 | +0.64 |

Linear readout of participant ID from the 32-D PCA embedding is far above
chance. A stable representation exists, but it is heavily identity-laden. This
is a warning for any later shared-latent direction analysis: identity must be
controlled, not ignored.

### T2/T3 projection (descriptive only — not used for selection)

Mean L2 distance of recording embeddings from T1 (trajectory repetition),
pooled across folds/participants:

| Timepoint | Mean L2 from T1 | SD |
|---|---|---|
| T2 | 4.79 | 0.76 |
| T3 | 8.22 | 5.11 |

These distances show that projections move, but they are **not** evidence of
an intervention effect and were not used to choose PCA settings.

---

## Interpretation

1. PCA at d=32 is a **stable, useful compression** of window content (>92%
   variance, consistent folds).
2. It is **not amplitude-dominated** on PC1.
3. It **is identity-dominated** under a linear probe. That limits its use as a
   pure “motion quality” space without further controls.
4. Enough signal exists to justify asking whether a learned masked model adds
   anything beyond this linear baseline — that is the role of the conv baseline
   and, if earned, S6.

Artifacts: `outputs/s5_pca/`.
