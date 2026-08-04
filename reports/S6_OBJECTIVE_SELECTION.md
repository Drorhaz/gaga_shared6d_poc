# S6 objective selection

**Frozen from held-out T1 only.** No T2/T3, direction cosine, UMAP, or
trajectory statistic entered this decision.

Primary representation unchanged:

```text
Raw global quaternions → parent-relative quaternions
→ rotvec (filter/QC only) → matrix → 6D model input
```

Mask ratio remains **30%** (S5 freeze). Architecture: `SharedMotionTransformer`
(~30–31k params), 2 blocks, d=32, CPU.

---

## Observed: held-out T1 skill (2 folds × 3 seeds)

| Objective | Mean | SD | Min | Max | Positive in both folds |
|---|---|---|---|---|---|
| `masked_6d` | **−0.243** | 0.172 | −0.513 | −0.093 | No |
| `masked_angular_velocity` | **+0.029** | 0.042 | +0.011 | +0.115 | **Yes** |

Per-fold means (`masked_angular_velocity`): Fold A **0.011**, Fold B **0.047**.

Artifact: `outputs/s6_transformer/objective_selection_heldout_t1.csv`,
`OBJECTIVE_SELECTION.json`.

---

## Selection rule (pre-registered)

1. Prefer objectives with positive held-out-T1 skill in **both** folds.
2. Among those, higher mean skill across folds and seeds.
3. Tie within 0.02 → lower participant-identity probe accuracy.

---

## Decision

**Selected objective: `masked_angular_velocity`.**

Reason: only objective with positive skill in both folds. `masked_6d` is again
a failed pretext against interpolation (skill < 0 at every fold/seed),
consistent with S5.

Seed variability for velocity is high (SD 0.042) relative to the mean,
driven largely by Fold B seed 1 (skill 0.114). The other five velocity runs
cluster near 0.011–0.014. The objective still clears the positive-both-folds
gate; the instability is recorded for the architecture comparison.

Written to `outputs/s6_transformer/SELECTED_OBJECTIVE.txt` **before** T2/T3
reliability tables were used for any decision.

---

## Interpretation

* Angular-velocity remains the leading self-supervised target for this data
  scale and mask protocol.
* Masked 6D reconstruction remains non-viable for both the convolutional and
  Transformer models against the interpolation trivial baseline.
* Objective selection does **not** decide architecture; that is
  `S6_TRANSFORMER_VS_CONV.md`.
