# S6 SharedMotionTransformer training report

**Observed** results from the frozen S6 configuration. **Derived** metrics
(skill, identity probe, bootstrap CIs) follow. **Interpretation** is separate
and does not retune any hyperparameter.

No clustering, motif discovery, or cross-participant direction analysis was
performed.

---

## Configuration (frozen)

| Item | Value |
|---|---|
| Model | `SharedMotionTransformer`, 2 factorized blocks (spatial→temporal) |
| Hidden / embedding | 32 / 32 (mean pool of 18×24 tokens, unmasked) |
| Params | 31,036 (`masked_6d`) / 30,046 (`masked_angular_velocity`) |
| Tokens | 18 links × 24 patches (10 frames) |
| Mask | structured link-by-span, **30%** (frozen), spans 3–6 patches |
| Folds × seeds × objectives | 2 × 3 × 2 = **12 runs** |
| Early stop | held-out contiguous T1 blocks only |
| Device | deterministic CPU |
| Optimiser | AdamW, lr=1e-3, wd=1e-4, batch=16, patience=8, max 60 epochs |

Snapshot: `outputs/s6_transformer/experiment_snapshot.yaml`.

---

## Observed: held-out T1 skill

| Objective | Mean | SD | Min | Max |
|---|---|---|---|---|
| `masked_6d` | **−0.243** | 0.172 | −0.513 | −0.093 |
| `masked_angular_velocity` | **+0.029** | 0.042 | +0.011 | +0.115 |

Selected objective (held-out T1 only): **`masked_angular_velocity`**
(see `S6_OBJECTIVE_SELECTION.md`).

Fold A velocity runs plateau near skill ≈ 0.011 and early-stop at epoch 0–2.
Fold B seed 1 is an outlier (0.114 at epoch 20); B seeds 0/2 stay near 0.013.

Loss curves: `figures/s6_transformer/loss_*.png`.
Run table: `outputs/s6_transformer/run_summary.csv`.

---

## Controls (selected objective)

| Control | Mean value | Notes |
|---|---|---|
| Identity probe | 0.413 (chance 0.25) | Above chance; below PCA (~0.8–0.9); slightly below conv (0.446) |
| Shuffle-time skill (best trivial) | **−0.001** | Destroys skill — temporal structure used |
| Shuffle-link skill (best trivial) | 0.025 | Mild reduction vs intact ~0.027 |
| Overshoot baseline skill | 0.027 | |
| Overshoot exclude `RShoulder_to_RUArm` | 0.025 | Δ ≈ −0.001 — not material |
| Overshoot exclude 790-T1 ES windows | 0.027 | Δ ≈ +0.001 — not material |
| Train-subset − held-out skill gap | −0.004 | No large train≫val skill gap |

Mean-motion-only shuffle scores match best-trivial scores for velocity (same
table columns `*_mean_motion_only`) and are sanity checks only.

Figures: `shuffle_controls.png`, `identity_probe_comparison.png`.

---

## Reconstruction error by region (held-out T1, velocity MSE)

| Region | Mean masked MSE |
|---|---|
| trunk_spine | 610 |
| head_neck | 1,223 |
| right_leg | 2,337 |
| left_leg | 2,458 |
| left_arm | 7,028 |
| right_arm | 7,413 |

Arms dominate velocity error, as expected from higher angular speeds.
Figures: `error_by_link.png`, `error_by_region.png`.
Table: `outputs/s6_transformer/link_errors_heldout_t1.csv`.

---

## Prediction examples

Masked input vs prediction examples (seed 0):  
`figures/s6_transformer/pred_example_{A,B}_{objective}.png`.

---

## Embeddings

Deterministic 32-D window embeddings for all evaluation recordings written to
`outputs/s6_transformer/recording_embeddings.csv` (coordinates **not** pooled
across folds/seeds). Exploratory PCA of recording embeddings is in
`exploratory_embedding_pca.png` and **did not enter any decision**.

---

## Provenance

* Checkpoints: `outputs/s6_transformer/checkpoints/`
* Histories: `outputs/s6_transformer/history_*.csv`
* Stamp + checksums: `outputs/s6_transformer/s6_transformer_provenance.json`
* Decision log entry appended to `reports/DECISION_LOG.md`

---

## Interpretation

1. The Transformer learns a weak but positive velocity pretext on average;
   6D reconstruction fails again.
2. Fold A velocity learning is shallow (≈1.1% skill plateau).
3. Structure controls behave as expected (time critical; link weaker).
4. 790 shoulder overshoot is not material.
5. Whether attention beats convolution is answered in
   `S6_TRANSFORMER_VS_CONV.md` — it does not, reliably.
