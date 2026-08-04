# S5 matched convolutional baseline report

Primary representation unchanged. No Transformer trained. Latent coordinates
are kept separate across folds and seeds; only statistics are pooled.

---

## Configuration

| Item | Value |
|---|---|
| Model | `ConvMaskedPredictor` (~14.2–14.3k params) |
| Input | primary-path 6D, 18 links × 240 frames |
| Tokens | 18 × 24 patches (10 frames) |
| Mask | structured link-by-span, **30%** (frozen) |
| Folds × seeds × objectives | 2 × 3 × 2 = **12 runs** |
| Early stop | held-out contiguous T1 blocks only |
| Embedding | deterministic 32-D mean pool + linear proj (unmasked) |

---

## Observed: held-out T1 skill

Skill uses the best matched trivial baseline (mean-motion vs interpolation)
computed during training.

| Objective | Mean skill | SD | Min | Max |
|---|---|---|---|---|
| `masked_6d` | **−0.983** | 0.197 | −1.283 | −0.789 |
| `masked_angular_velocity` | **+0.036** | 0.005 | +0.030 | +0.043 |

**Selected objective (held-out T1 only): `masked_angular_velocity`.**

6D reconstruction loses to interpolation at every fold and seed. Angular
velocity shows weak but consistently positive skill. Folds and seeds agree
(velocity SD 0.005).

Figure: `figures/s5_conv/skill_by_objective_fold.png`. Loss curves:
`figures/s5_conv/loss_*.png`.

---

## Controls

| Control | `masked_6d` (mean) | `masked_angular_velocity` (mean) |
|---|---|---|
| Identity probe accuracy (chance 0.25) | 0.43 | **0.45** |
| Shuffle-time skill | 0.46* | **−0.008** |
| Shuffle-link skill | 0.17* | 0.023 |
| Overshoot baseline skill† | 0.60* | 0.036 |
| Overshoot exclude `RShoulder_to_RUArm`† | 0.48* | 0.034 |
| Overshoot exclude `790_T1` ES windows† | 0.60* | 0.038 |

\* Control scoring for these rows uses skill vs **mean-motion only** (fast path);
training selection used best-of trivials, which is why 6D training skill is
negative while mean-motion-only skill can look positive. Velocity conclusions
are unaffected.

† Overshoot sensitivity for the **selected** objective: excluding the affected
link changes skill by −0.002; excluding 790-T1 early-stop windows changes it by
+0.002. **Not material.** Primary analysis retains the link and recording.

### Interpretation of controls

1. **Identity** is above chance (~0.45) but far below PCA (~0.8–0.9). The conv
   latent is less identity-dominated than PCA, but not identity-free.
2. **Shuffle-time** destroys velocity skill (→ negative). The model uses
   temporal structure.
3. **Shuffle-link** halves velocity skill (0.036 → 0.023). Spatial coordination
   contributes, but less than time.
4. **790 shoulder overshoot** does not move the selected-objective result.

---

## Runtime and capacity

| Objective | Params | Mean wall time / run |
|---|---|---|
| `masked_6d` | 14,342 | ~168 s (includes resumed 0s rows in average) |
| `masked_angular_velocity` | 14,237 | ~56 s |

Both stay clearly below the Transformer budget (~31k in the smoke test / ~38k
planned).

---

## Aggregation

Recording embeddings written to
`outputs/s5_conv/recording_embeddings.csv` with the planned structure
(window → exercise mean → equal-weight ex09–13 mean), one row per
(fold, objective, seed, recording). Coordinates are **not** averaged across
folds/seeds.

---

## Interpretation

1. The matched conv baseline **beats trivial baselines only for angular
   velocity**, and only weakly (~3.6% skill).
2. **6D reconstruction is not a viable pretext** for this architecture at this
   data scale against interpolation.
3. Results are **stable across folds and seeds** for the selected objective.
4. There is a narrow but real gap where spatial-temporal attention might help
   (velocity skill is small; shuffle-link still leaves residual skill). That is
   the case for running S6 — not a claim that attention will succeed.

Artifacts: `outputs/s5_conv/`, `figures/s5_conv/`.
