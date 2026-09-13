# JcvPCA × existing coupling concordance

**JcvPCA source (READ-ONLY):** `gaga_jcvpca/.../marker_gap_policy_ex09_13/` (`09_headline_a2_summary.csv`, `NV_PROFILE.csv`)  
**Coupling source:** `EXISTING_COUPLING_LONGITUDINAL_RESULTS.csv` (window means from `window_features.csv`)  
**Primary comparison:** D12. D13 supplemental.  
**Important:** JcvPCA A2 is **pooled** across ex09–13; coupling is **exercise-resolved**. Concordance is therefore participant-level anatomical/regional compatibility, not exercise-matched A2.

Categorical labels:

| JcvPCA (pooled A2) | Coupling (exercise metric) | Label |
|---|---|---|
| change | robust change | `CONVERGENT_COORDINATION_EVIDENCE` |
| change | stable | `GLOBAL_REDISTRIBUTION_WITHOUT_SIMPLE_COUPLING_CHANGE` |
| stable | change | `LOCAL_OR_REGIONAL_COUPLING_CHANGE_WITHOUT_CLEAR_JCVPCA_REDISTRIBUTION` |
| either unreliable | — | `INSUFFICIENT_OR_UNRELIABLE` |

“Robust change” = `EXCEEDS_R1R2_DIRECTION_CONSISTENT` (both reps, stable Drep).

---

## D12 robust coupling exceeds (both reps)

| Pid | Exercise | Metric | Direction | Δ_mean | Drep_T1 | JcvPCA A2 (pooled) | Regions in A2 links | Concordance |
|---|---|---|---|---:|---:|---|---|---|
| 252 | ex09 | trunk_arm_lagged | DECREASE | −0.032 | 0.016 | 3/20 | arm (+) | CONVERGENT |
| 252 | ex10 | regional_coupling | DECREASE | −0.035 | 0.026 | 3/20 | arm | CONVERGENT |
| 252 | ex10 | trunk_arm_lagged | INCREASE | +0.111 | 0.036 | 3/20 | arm | CONVERGENT |
| 252 | ex13 | regional_coupling | DECREASE | −0.035 | 0.012 | 3/20 | arm | CONVERGENT |
| 651 | ex09 | trunk_arm_lagged | INCREASE | +0.094 | 0.036 | 4/10 | arm, leg | CONVERGENT |
| 651 | ex10 | trunk_arm_lagged | INCREASE | +0.109 | 0.057 | 4/10 | arm, leg | CONVERGENT |
| **651** | **ex13** | **trunk_arm_lagged** | **INCREASE** | **+0.127** | **0.066** | 4/10 | arm, leg | **CONVERGENT** |
| 651 | ex12 | regional_coupling | INCREASE | +0.036 | 0.021 | 4/10 | arm, leg | CONVERGENT |
| **671** | **ex10** | **regional_coupling** | **DECREASE** | **−0.084** | **0.023** | **8/18 (+S3)** | arm, leg, trunk | **CONVERGENT** |
| **671** | **ex12** | **trunk_arm_lagged** | **INCREASE** | **+0.203** | **0.096** | **8/18 (+S3)** | arm, leg, trunk | **CONVERGENT** |
| 790 | ex13 | regional_coupling | DECREASE | −0.075 | 0.011 | 7/20 | arm, leg, trunk | CONVERGENT |

Excluded as unreliable despite raw exceed: 790 ex10 regional (Drep≈0), 790 ex13 trunk_arm (unstable Drep), 252/671 some trunk_arm cells with Drep below floor.

---

## Participant-specific answers

### 671 — strongest JcvPCA case

| Question | Answer |
|---|---|
| JcvPCA | D12 A2=8, S3=4, rep_pass=True, adequate coverage; links include trunk/Ab, bilateral thighs, left arm (hand, UArm–FArm), left shin–foot |
| Coupling beyond R1/R2? | **Yes, selected exercises:** ex10 `regional_coupling` **decreases**; ex12 `trunk_arm_lagged_coupling` **increases** strongly (+0.20) |
| Compatible regions? | Yes — A2 includes arm + trunk (+ legs); trunk–arm metric is region-compatible |
| Helps interpret JcvPCA vs sparse Conv? | **Partially.** Coupling provides an independent **regional coordination** layer where Conv detection is sparse: mixed pattern (some regional mean coupling down, trunk–arm max\|r\| up) is consistent with **reorganization**, not a single “coupling reduced = learning” story |
| Discordance | ex09: both coupling metrics **stable** within Drep despite strong pooled A2 → some exercises show **global redistribution without simple coupling change** |
| Conv/RQA context | Conv limited (3/6 cells); no RQA complementary cell |

**Summary:** Existing coupling **adds useful but limited** interpretive support for 671 — reorganization of trunk–arm association at ex12 and reduced mean regional speed coupling at ex10 — without replacing JcvPCA or confirming DOF unfreezing.

### 651 — strong multi-method D12 convergence

| Question | Answer |
|---|---|
| JcvPCA | D12 A2=4/10 after marker-gap exclusions (`LFArm_to_LHand`, `LUArm_to_LFArm`, `RShoulder_to_RUArm`, `RThigh_to_RShin`); S3=0 |
| Coupling | **ex13 trunk_arm_lagged INCREASE** beyond R1/R2 (same-sign both reps) — anatomically compatible with arm A2 links |
| ex13 + RQA/Conv | Aligns with prior Conv exercise emphasis on ex13 and RQA complementary cell **651–ex13–D12** |
| Caveat | Marker-gap exclusions limit anatomical completeness; `regional_coupling` at ex13 is **inconsistent across reps** (not robust) |
| Pattern | Coupling adds a biomechanical layer: **strengthened trunk–arm lagged association** at ex13, not reduced coupling |

### 790 — D12 JcvPCA + Conv convergence

| Question | Answer |
|---|---|
| JcvPCA | D12 A2=7/20; adequate coverage; S3=0 |
| Focus ex11 (RQA cell) | Both coupling metrics **INCONSISTENT across R1/R2** — **no robust coupling change** at 790–ex11–D12 |
| Other | Robust **decrease** in `regional_coupling` at **ex13** |
| Clarifies RQA/Conv? | **Weakly.** Does **not** add a clean third layer on the RQA complementary ex11 cell; modest support at ex13 (also a Conv-emphasized exercise) |

### 252 — modest D12 JcvPCA; symmetry/coupling features previously noted

| Question | Answer |
|---|---|
| JcvPCA | D12 A2=3/20 (arm/hand-focused); adequate coverage |
| Coupling | Several robust D12 changes: regional **decrease** (ex10, ex13); trunk_arm **increase** (ex10); trunk_arm **decrease** (ex09) |
| vs Conv | Conv pooled D12 ≤Drep — coupling changes are **feature-level**, not latent-embedding confirmation |
| D13 | Supplemental only for shared synthesis; not used to replace D12 |
| Pattern | Coupling **complements** modest JcvPCA A2 with mixed increase/decrease — consistent with prior “symmetry/coupling” feature theme, not a single directional learning claim |

---

## Discordance highlights (D12)

| Case | Interpretation |
|---|---|
| 671 ex09: JcvPCA A2 present (pooled) + coupling stable | `GLOBAL_REDISTRIBUTION_WITHOUT_SIMPLE_COUPLING_CHANGE` for that exercise |
| 790 ex11: RQA complementary + coupling inconsistent | Coupling does **not** corroborate that specific cell |
| Many cells opposite-sign across reps | `INSUFFICIENT_OR_UNRELIABLE` — do not interpret |

---

## What not to conclude

- Exercise-level coupling change ≠ exercise-resolved JcvPCA A2 (not available as A2 gate).
- Increased trunk–arm max\|r\| ≠ Chang in-phase anatomical coupling.
- Decreased regional mean speed correlation ≠ proven local DOF freeing.
