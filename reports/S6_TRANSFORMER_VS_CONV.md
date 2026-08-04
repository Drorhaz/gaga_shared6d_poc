# S6 Transformer versus matched convolutional baseline

Comparison uses the **selected** objective (`masked_angular_velocity`), the
same 30% structured masks, the same held-out contiguous T1 blocks, the same
folds and seeds, and skill against the best matched trivial baseline
(mean-motion vs interpolation).

Primary comparison metric: held-out T1 skill from each run’s early-stopping
history (identical definition to S5). Paired re-scoring with a shared mask
stream and pooled-skill bootstrap CIs are reported as uncertainty.

---

## Observed skill

| Model | Params | Mean skill | SD | Min | Max |
|---|---|---|---|---|---|
| Conv (`ConvMaskedPredictor`) | 14,237 | **0.0359** | 0.0045 | 0.0297 | 0.0426 |
| Transformer (`SharedMotionTransformer`) | 30,046 | **0.0292** | 0.0418 | 0.0112 | 0.1145 |

Per-fold means:

| Fold | Conv | Transformer | Δ (TF − Conv) |
|---|---|---|---|
| A | 0.0326 | 0.0112 | −0.0214 |
| B | 0.0392 | 0.0472 | +0.0080 |

Paired run-level differences (history):

| Fold | Seed | TF | Conv | Δ |
|---|---|---|---|---|
| A | 0 | 0.0112 | 0.0357 | **−0.0245** |
| A | 1 | 0.0112 | 0.0297 | **−0.0185** |
| A | 2 | 0.0112 | 0.0325 | **−0.0214** |
| B | 0 | 0.0137 | 0.0426 | **−0.0289** |
| B | 1 | 0.1145 | 0.0374 | **+0.0770** |
| B | 2 | 0.0133 | 0.0374 | **−0.0242** |

Mean Δ = **−0.0067**. Transformer better in **1/6** runs (Fold B seed 1 only).

Pooled-skill bootstrap (500 resamples of held-out windows, shared masks):

| Fold | Seed | Paired Δ | 95% CI |
|---|---|---|---|
| A | 0 | −0.0276 | [−0.0333, −0.0224] |
| A | 1 | −0.0206 | [−0.0244, −0.0167] |
| A | 2 | −0.0242 | [−0.0292, −0.0197] |
| B | 0 | −0.0291 | [−0.0345, −0.0239] |
| B | 1 | +0.0757 | [+0.0632, +0.0894] |
| B | 2 | −0.0237 | [−0.0285, −0.0198] |

Five of six CIs exclude zero in favour of the **convolutional** model. The
single Transformer win is Fold B seed 1 and does not reverse the fold-A
deficit.

Figures: `figures/s6_transformer/transformer_vs_conv_skill.png`,
`paired_skill_differences.png`.

---

## Identity probe

| Model | Mean accuracy (chance 0.25) |
|---|---|
| Conv | 0.446 |
| Transformer | 0.413 |

Identity is **slightly lower** for the Transformer (Δ ≈ −0.032). That is
favourable but does not outweigh the skill deficit.

---

## Runtime

| Model | Mean wall time / run (non-resumed, velocity) |
|---|---|
| Conv | ~112 s (Fold B timed runs; Fold A resumed in S5) |
| Transformer | ~15 s |

The Transformer’s lower wall time reflects **early plateau / early stopping**
(Fold A velocity stops at epoch 0–2 with ~1.1% skill), not a more efficient
solution of the pretext. It is not evidence of architectural superiority.

---

## Advantage criteria (from the S6 brief)

| Criterion | Result |
|---|---|
| Skill consistently higher than conv | **No** (1/6 runs) |
| Improvement not driven by one fold/seed | **No** — the only TF win is one seed |
| Identity not materially higher | **Yes** (slightly lower) |
| Representation stable under controls | Partially (see training report) |

---

## Interpretation

The Transformer does **not** earn a reliable advantage over the matched
convolutional predictor on held-out T1 skill. Fold A shows a stable ~2
percentage-point deficit; Fold B is mixed and seed-sensitive. Prefer the
simpler convolutional model for downstream work unless a sensitivity analysis
explicitly requires both.

Artifact: `outputs/s6_transformer/transformer_vs_conv.csv`.
