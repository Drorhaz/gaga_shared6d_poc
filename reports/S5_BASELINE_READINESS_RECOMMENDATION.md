# S5 baseline readiness recommendation

**Stop gate before S6.** No Transformer has been trained.

Primary representation remains:

```text
Raw global quaternions → parent-relative quaternions
→ rotvec (filter/QC only) → matrix → 6D model input
```

---

## Answers to the ten readiness questions

### 1. Does PCA already provide a stable and useful representation?

**Yes, as a linear compression.** d=32 explains 92–93% of time-mean 6D
variance; held-out T1 MSE is stable across folds; PC1 is not amplitude.
**But** a linear identity probe reaches 79–89% accuracy (chance 25%). PCA is
useful and identity-heavy.

### 2. Do explicit features show interpretable variation beyond amplitude?

**Weakly, descriptively.** Amplitude-controlled participation-entropy residuals
shift slightly T1→T2/T3 in pooled means. Effect sizes are small; N=4 forbids
intervention claims. Features are retained as an interpretable reference.

### 3. Does the convolutional model outperform its matched trivial baselines?

**Only for masked angular-velocity prediction** (mean skill +0.036).
**No for masked 6D reconstruction** (mean skill −0.98 vs best trivial).

### 4. Which reconstruction objective performs best on held-out T1 skill?

**`masked_angular_velocity`.** Selected solely from held-out T1 skill across
2 folds × 3 seeds. No T2/T3 or direction statistic entered the choice.

### 5. Which mask ratio was selected and how stable was the selection?

**30%.** Velocity skill at 30% (0.036) and 50% (0.043) tied within 0.02; the
conservative lowest ratio was frozen. 70% was worse for velocity. Documented in
`S5_MASK_RATIO_SWEEP.md`. Will not be retuned after T2/T3.

### 6. Are results stable across folds and seeds?

**Yes for the selected objective** (skill SD 0.005). 6D failure is also stable
(always largely negative).

### 7. Is participant identity dominating the learned representation?

**Partially.** Conv identity probe ~0.43–0.45 (chance 0.25) — elevated, but much
less than PCA (~0.8–0.9). Identity remains a risk for S7–S8; the predefined
probe and selection tie-break stay in force.

### 8. Does the 790 shoulder overshoot materially affect the result?

**No.** For `masked_angular_velocity`, excluding the link or the 790-T1
early-stop windows changes skill by ≤0.002. Keep in primary analysis.

### 9. Is there enough evidence to justify testing spatial-temporal attention in S6?

**Yes, narrowly.** Reasons to proceed:

* Velocity pretext is learnable but weak under a ~14k conv model.
* Shuffle-time destroys skill; shuffle-link reduces it — both structure axes
  that factorized attention is designed to use.
* PCA works but is more identity-dominated than the conv latent.

Reasons for caution (not blockers):

* Absolute conv skill is small (~3.6%).
* 6D reconstruction remains a failed pretext against interpolation; S6 should
  still run both objectives under the same held-out-T1 selection rule, but
  expect velocity to win again unless attention changes that.

### 10. What exact Transformer configuration should be run next?

| Setting | Value |
|---|---|
| Architecture | `SharedMotionTransformer`, 2 blocks, factorized spatial→temporal attention |
| `hidden_dim` / embedding | 32 / 32 (mean pool of 432 tokens) |
| Params | keep ≤ ~38k (smoke test measured 31,036 before any S6 change) |
| Mask ratio | **30%** (frozen) |
| Mask spans | 3–6 patches (30–60 frames) |
| Objectives | both; select on held-out T1 skill; identity probe tie-break |
| Folds × seeds | 2 × 3 |
| Early stop | held-out contiguous T1 blocks only |
| Device | CPU (deterministic); do not switch to MPS for reported runs |
| Aggregation | exercise-balanced ex09–13; ex11 breakdown |
| Do **not** | tune on T2/T3, direction cosine, or UMAP |

---

## Recommendation

**Proceed to S6 Transformer training** with the frozen mask ratio and the
configuration above, after this report is reviewed.

**Do not** begin longitudinal direction analysis (S7–S8) until S6 embeddings
pass the same held-out-T1 skill gate with `skill > 0` under the selected
objective.

---

## Artifact index

| Report | Path |
|---|---|
| PCA | `reports/S5_PCA_BASELINE_REPORT.md` |
| Explicit features | `reports/S5_EXPLICIT_FEATURE_REPORT.md` |
| Mask sweep | `reports/S5_MASK_RATIO_SWEEP.md` |
| Conv baseline | `reports/S5_CONV_BASELINE_REPORT.md` |
| This gate | `reports/S5_BASELINE_READINESS_RECOMMENDATION.md` |

Outputs: `outputs/s5_pca/`, `outputs/s5_explicit/`, `outputs/s5_masksweep/`,
`outputs/s5_conv/`. Figures under `figures/s5_*/`.
