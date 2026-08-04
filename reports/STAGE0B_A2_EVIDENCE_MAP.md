# Stage 0B-A2 — Evidence map

Compiled from Stage 0 and Stage 0B-A artifacts without reopening failed hypotheses.

## Already tested and passed

| Claim | Evidence |
|---|---|
| Primary path / 18-link / 6D / windowing valid | S1–S4 |
| Mask 30%; velocity objective; Conv > Transformer on held-out T1 | S5–S6 |
| Conv T1/T2/T3 reliability proceed rule | S6b PASS (per-cell failures remain) |
| Exercise-balanced recording embeddings + Drep | S7 |
| Individual latent ‖Δ‖ often > Drep in qualified cells | S7, 0B-A |
| Amplitude alone does not explain all individual changes | 0B-A amp-residual exceedances |
| Different participants have different exercise/feature profiles | 0B-A |
| Conv less identity-dominated than PCA; positive velocity skill | S5, S9 |

## Already tested and failed / rejected

| Claim | Evidence |
|---|---|
| Stable shared cross-participant direction | S8 FAIL (sign/geometry/jackknife unstable) |
| Transformer as primary representation | S6 FAIL vs Conv |
| Masked 6D reconstruction as viable pretext | S5–S6 FAIL |
| Population / intervention inference at N=4 | Methodologically barred |

## Already partially characterized (0B-A)

| Topic | Status |
|---|---|
| Recording-level individual profiles | Done |
| Exercise contribution fractions (descriptive) | Done — needs absolute/Drep-normalized supplement |
| Explicit features vs R1–R2 + amp residuals | Done at recording/exercise level |
| Latent vs energy correlation | Done |

## Unresolved before this closeout

| Question | Plan in A2 |
|---|---|
| Supported segmentation units (P1–P5?) | Map annotations; do not invent stages |
| Absolute exercise-level Δ vs Drep | Section 4 |
| Early/mid/late within-exercise localization | Section 4–5 |
| Temporal path vs mean-shift vs spread | Section 5 |
| Region/link attribution (explicit + occlusion validity) | Section 7 |
| Whether local states/motifs are feasible | Section 8 |
| Best primary analysis framework | Sections 9–10 |

## Would duplicate without adding value

* Full S5–S8 re-runs
* Shared-direction / sign-flip re-search
* Transformer retraining
* Recomputing recording-level profiles already in 0B-A (reuse, extend)

## Decision context

Stage 0: **LIMITED GO**. Shared direction closed. Free-movement not authorized until guided closeout.
