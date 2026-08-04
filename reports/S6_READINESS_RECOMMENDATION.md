# S6 readiness recommendation

**Stop gate before S7–S8.** No longitudinal direction analysis has begun.

Primary representation unchanged. Mask ratio 30% unchanged. Objective and
architecture choices below use **held-out T1 only** (plus pre-registered
controls). T2/T3 reliability is reported separately and does not reverse the
held-out-T1 architecture decision.

---

## Answers to the ten readiness questions

### 1. Which objective was selected, and why?

**`masked_angular_velocity`.** It is the only objective with positive held-out
T1 skill in both folds. `masked_6d` mean skill −0.24 (failed pretext).

### 2. Does the Transformer produce positive held-out-T1 skill?

**Yes, weakly**, under the selected objective (mean **+0.029**, range
0.011–0.115). Skill is near-zero on Fold A and seed-unstable on Fold B.

### 3. Does it outperform the matched convolutional baseline?

**No.** Conv mean skill **0.036** vs Transformer **0.029**. Transformer wins
only 1/6 paired runs (Fold B seed 1). Pooled bootstrap CIs favour conv in five
of six runs.

### 4. Is the advantage stable across folds and seeds?

**There is no Transformer advantage to be stable.** Conv is more stable
(SD 0.0045 vs 0.042). The single TF win is an isolated seed.

### 5. Is participant identity higher, lower, or similar?

**Slightly lower** for the Transformer (0.413 vs 0.446). Not decisive.

### 6. Do shuffled-time and shuffled-link controls behave as expected?

**Yes.** Shuffle-time → skill ≈ 0 (destroys pretext). Shuffle-link → mild drop.
Temporal structure dominates.

### 7. Does the 790 overshoot materially influence the result?

**No.** Excluding the link or 790-T1 early-stop windows changes velocity skill
by ≤ ~0.002.

### 8. Does reconstruction skill remain positive at T2 and T3?

**Not uniformly.** Under Transformer + selected objective: T2 fails in 3/24
cells, T3 in 4/24; several further cells are positive but degraded vs paired
held-out T1. See `S6_RELIABILITY_GATE.md`.

### 9. Which participants or timepoints fail the reliability gate?

Mostly **671** (T3 under Fold A; T1 under Fold B) and **790** under Fold B
(including one full T1/T2/T3 failure at B seed 2). **252** has no
non-positive failures in this table. Full cell list in the reliability report.

### 10. Should S7–S8 use Transformer, conv, PCA, or multiple?

**Prefer the matched convolutional baseline** for any learned-latent S7–S8
path, with:

* **PCA (d=32)** and **explicit features** retained as co-primary /
  interpretable references (from S5);
* Transformer retained only as an optional **sensitivity** if a reviewer
  insists — not as the primary representation;
* Before interpreting any learned latent geometry, re-run the T1/T2/T3
  reliability gate on the **chosen** checkpoints (conv) and restrict analysis
  to cells with `skill > 0`.

Do **not** force a Transformer-based continuation: attention did not provide a
clear, reliable advantage on the registered comparison.

---

## Recommendation

| Decision | Value |
|---|---|
| Selected objective | `masked_angular_velocity` |
| Primary learned model for S7–S8 | **`ConvMaskedPredictor` (S5)** |
| Transformer | not primary; optional sensitivity only |
| PCA / explicit features | keep as references |
| S7–S8 status | **stopped pending review** |

A valid outcome of Stage 0 remains: learned masked models may be secondary to
PCA + explicit features if even the conv latent fails reliability or identity
controls at S7–S8. That question is deferred until those stages are reviewed.

---

## Artifact index

| Report | Path |
|---|---|
| Training | `reports/S6_TRANSFORMER_TRAINING_REPORT.md` |
| Objective selection | `reports/S6_OBJECTIVE_SELECTION.md` |
| TF vs Conv | `reports/S6_TRANSFORMER_VS_CONV.md` |
| Reliability | `reports/S6_RELIABILITY_GATE.md` |
| This gate | `reports/S6_READINESS_RECOMMENDATION.md` |

Outputs: `outputs/s6_transformer/`. Figures: `figures/s6_transformer/`.
