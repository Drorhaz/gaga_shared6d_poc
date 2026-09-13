# Existing coupling — interpretation summary

Based on already-computed window features, R1/R2 matched longitudinal contrasts, D12 primary.

---

## Did coupling decrease anywhere?

**Yes (robust D12, both reps, stable Drep):**

| Pid | Exercise | Metric |
|---|---|---|
| 252 | ex09 | trunk_arm_lagged_coupling |
| 252 | ex10, ex13 | regional_coupling |
| 671 | ex10 | regional_coupling |
| 790 | ex13 | regional_coupling |

Preferred wording when citing:  
> “Selected coupling relationships weakened longitudinally beyond within-session repetition variability, consistent with increased regional independence of speed-magnitude time series.”

Do **not** call this motor learning or DOF unfreezing.

---

## Did coupling increase / reorganize anywhere?

**Yes (robust D12):**

| Pid | Exercise | Metric |
|---|---|---|
| 252 | ex10 | trunk_arm_lagged_coupling ↑ |
| 651 | ex09, ex10, **ex13** | trunk_arm_lagged_coupling ↑ |
| 651 | ex12 | regional_coupling ↑ |
| 671 | **ex12** | trunk_arm_lagged_coupling ↑ (largest Δ_mean ≈ +0.20) |

Preferred wording:  
> “Selected coupling relationships strengthened longitudinally beyond within-session repetition variability, consistent with refinement of a trunk–arm coordination association (max lagged \|corr\| of regional speeds).”

---

## Did coupling change beyond R1/R2?

**Yes, in selected participant×exercise×metric cells** (11 robust D12 cells after Drep-stability QC).  
**Also:** a large fraction of cells are `INCONSISTENT_ACROSS_REPS` (~18 of 40 D12 metric×exercise cells) — those are **not** interpreted.

Recording-level (exercise-pooled) context: 651 and 671 show pooled trunk_arm ↑ and/or regional ↓ beyond Drep at D12 — consistent with exercise-resolved pattern but less localized.

---

## Which changes are robust enough to interpret?

Interpret only `EXCEEDS_R1R2_DIRECTION_CONSISTENT` with stable Drep:

1. **651–ex13–trunk_arm ↑** — highest scientific priority (aligns with Conv/RQA ex13 story + arm A2 links).
2. **671–ex12–trunk_arm ↑** and **671–ex10–regional ↓** — best coupling support for the strongest JcvPCA case.
3. **252** mixed ↑/↓ — supports prior coupling/symmetry feature theme; modest JcvPCA A2.
4. **790–ex13–regional ↓** — limited; **not** at RQA’s ex11 cell.

Do **not** interpret `EXCEEDS_BUT_DREP_UNSTABLE` or opposite-sign cells.

---

## Which JcvPCA findings have compatible coupling evidence?

| JcvPCA finding | Compatible coupling? |
|---|---|
| 671 D12 strong A2/S3 (arm/trunk/leg) | **Yes, partial** — trunk–arm ↑ (ex12), regional ↓ (ex10); ex09 stable |
| 651 D12 A2 (arm + leg; exclusions) | **Yes at ex13** — trunk–arm ↑ |
| 790 D12 A2 | **Partial** — regional ↓ at ex13; **no** robust coupling at ex11 |
| 252 D12 modest arm A2 | **Yes, mixed** coupling changes at several exercises |

---

## Which JcvPCA findings occur without coupling change?

- **671 ex09:** pooled A2 present, both coupling metrics within Drep → whole-body redistribution **not reducible** to these simple regional coupling metrics for that exercise.
- Many exercises with inconsistent R1/R2 coupling deltas despite nonzero pooled A2 → insufficient coupling evidence, not proof of absence.

---

## What this adds to motor-adaptation interpretation

| Adds | Does not add |
|---|---|
| A third **descriptive coordination layer** (regional speed coupling) that sometimes moves beyond its own R1/R2 floor | Proof of motor learning |
| Evidence that coordination change is not only JcvPCA reweighting or Conv latent shift | Chang-style joint phase / in-phase–anti-phase anatomy |
| For 651/671, support that **reorganization** (↑ and ↓ in different metrics/exercises) is more apt than “coupling always decreases” | Causal Gaga / psilocybin claims |
| Clarifies that **790–ex11 RQA cell lacks robust coupling corroboration** | Exercise-resolved JcvPCA A2 |

**Claim ladder placement:**  
Coupling longitudinal changes beyond R1/R2 → support **CONSISTENT WITH** participant-specific motor adaptation / coordination change; **NOT PROVEN** as learning, unfreezing, or intervention effect.

---

## Relationship to Conv / RQA (contextual only)

| Cell | Conv | RQA | Existing coupling |
|---|---|---|---|
| 651–ex13–D12 | Conv emphasizes ex13 | Complementary amp-preserving | **trunk_arm ↑ robust** — biomechanical layer present |
| 790–ex11–D12 | Conv emphasizes ex11 | Complementary amp-preserving | **No robust coupling** (inconsistent reps) |
| 671 D12 | Sparse Conv | No RQA cell | Coupling **partially** fills interpretive gap |
| 252 D12 | Conv ≤Drep | — | Coupling changes without latent >Drep |

Do not count these as independent statistical votes.
