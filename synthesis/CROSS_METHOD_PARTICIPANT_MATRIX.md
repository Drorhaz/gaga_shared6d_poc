# Cross-method participant matrix (populated)

**Machine-readable:** [`CROSS_METHOD_PARTICIPANT_MATRIX.csv`](CROSS_METHOD_PARTICIPANT_MATRIX.csv) (84 rows)  
**Primary shared comparison:** D12 / T1→T2  
**Supplemental:** D13 / T1→T3 (with coverage flags)  
**Rule:** categorical evidence only; no cross-method magnitude voting; roles tagged.

Authoritative sources verified against marker-gap JcvPCA stack and guided-analysis freeze (not July-18 stale packs).

---

## Evidence roles

| Method | Role |
|---|---|
| JcvPCA | DETECTION · ANATOMICAL_LOCALIZATION · INTERPRETATION |
| Conv | DETECTION · EXERCISE_LOCALIZATION |
| Explicit features | INTERPRETATION |
| RQA | TEMPORAL_CHARACTERIZATION |
| Transformer | SENSITIVITY |
| PCA | REFERENCE |

---

## Shared D12 summary (primary)

| Pid | JcvPCA A2 / n_links | Coverage | rep_pass | S3 | Conv status (median \|Δ\|/Drep) | Conv top exercises | Explicit exceed themes | RQA |
|---|---|---|---|---|---|---|---|---|
| **671** | 8 / 18 | adequate | **True** | **4** | reliable_change_gt_repetition (1.68); **3/6 cells** | ex11, ex13, ex12 | coupling / active-region (sparse) | N/A complementary cell |
| **252** | 3 / 20 | adequate | False | 0 | reliable_but_**le**_repetition (0.78); 6/6 cells | ex10, ex12, ex09 | symmetry + regional/trunk-arm coupling (+ amp residuals) | N/A |
| **651** | 4 / 10 | adequate | False | 0 | reliable_change_gt_repetition (**9.25**); 5/6 | ex13, ex09, ex10 | entropy / dimensionality / active-region (+ amp residuals) | **651–ex13–D12 complementary** |
| **790** | 7 / 20 | adequate | False | 0 | reliable_change_gt_repetition (1.61); 4/6 | ex13, ex11, ex12 | entropy / dimensionality (+ amp residuals) | **790–ex11–D12 complementary** |

Sources: `09_headline_a2_summary.csv`; `individual_profiles.csv`; `exercise_level_change.csv`; `STAGE2_GATE.json`.

### D13 supplemental (coverage-flagged)

| Pid | JcvPCA A2 | Coverage | Conv status (median ratio) | Note |
|---|---|---|---|---|
| 671 | 9 | **limited** | limited_reliable (1/6 cells) | Do not headline without coverage caveat |
| 252 | 12 | **limited** | reliable_change_gt_repetition (2.65) | Strong Conv D13; JcvPCA coverage limited |
| 651 | 2 | **limited** | reliable_change_gt_repetition (1.09) | Weaker JcvPCA A2 than D12 |
| 790 | 3 | adequate | reliable_change_gt_repetition (5.65) | Strong Conv D13; JcvPCA A2 fewer than D12 |

---

## Participant narratives

### 252

1. **Strongest supported JcvPCA:** D12 A2 = **3/20** links (`Chest_to_LShoulder`, `LFArm_to_LHand`, `RFArm_to_RHand`) with **adequate** coverage — formal A2 but modest count. D13 has A2=12 but **limited** coverage → supplemental only. S3=0. Persistence: 0 persistent A2 links.
2. **Exceeds R1/R2?** Yes for those 3 A2 links (S2 definition). Many other links are S1 (exceed magnitude only).
3. **Anatomical localization:** bilateral forearm→hand plus left chest–shoulder chain at D12.
4. **Conv independent detection?** Endpoint reliability excellent (6/6), but D12 status = `reliable_but_le_repetition` (median 0.78×Drep) → **no** pooled Conv exceed at primary D12. D13 Conv exceeds (2.65×) under limited JcvPCA coverage.
5. **Exercises (Conv D12):** ex10 (1.58×), ex12 (1.03×), ex09 (0.80×).
6. **Explicit features:** lr_symmetry, regional_coupling, trunk_arm_lagged_coupling (+ amp residuals) exceed feature Drep — **complementary interpretation**, not link-level explanation of JcvPCA.
7. **RQA:** no complementary Stage2 cell for 252.
8. **Transformer:** no added claim (Conv preferred cohort-wide).
9. **Pattern:** **Discordant / complementary tension at D12** — JcvPCA A2 PRESENT (limited links) while Conv pooled change ≤Drep; features show symmetry/coupling shifts. Not a single convergent adaptation story at D12.
10. **Motor adaptation claim:** Participant-specific link redistribution beyond T1 R1–R2 is supported for **few links** at D12; latent dynamics change is reliable but not above repetition at D12. Adaptation language must stay narrow.

### 651

1. **Strongest supported JcvPCA:** D12 A2 = **4/10** (`LFArm_to_LHand`, `LUArm_to_LFArm`, `RShoulder_to_RUArm`, `RThigh_to_RShin`); adequate coverage; S3=0. Heavy marker-gap exclusions (n_links=10). Stale July-18 “S3=5” **discarded**.
2. **Exceeds R1/R2?** Yes for 4 A2 links.
3. **Anatomy:** left arm chain + right shoulder–upper arm + right thigh–shin.
4. **Conv:** Yes — `reliable_change_gt_repetition`, median **9.25×Drep**, 5/6 cells.
5. **Exercises:** ex13 (2.85×), ex09 (1.75×), ex10 (1.73×).
6. **Explicit features:** participation entropy, effective dimensionality, active_region_count, trunk_arm_lagged_coupling (+ amp residuals) — compatible with broader participation / redistribution theme, **not** proof of DOF unfreezing (Newell).
7. **RQA:** adds temporal complementary cell **651–ex13–D12** (amp-preserving); not z-score novel; not primary.
8. **Transformer:** sensitivity only.
9. **Pattern:** **Convergent detection** (JcvPCA A2 + Conv >Drep) with **complementary interpretation** (entropy/dimensionality features + RQA temporal cell on ex13). Still N-of-1; exclusions limit anatomical completeness.
10. **Motor adaptation claim:** Strongest multi-method D12 case for participant-specific longitudinal change exceeding method-specific repetition floors, with exercise focus including ex13 — still not causal Gaga/learning proof.

### 671

1. **Strongest supported JcvPCA:** D12 A2 = **8/18**, only comparison with **S3=4**, only `rep_pass=True`, adequate coverage. Persistent A2 links = 6. This is the **cleanest JcvPCA interpretive stack** (still pending supervisor A3 sign-off).
2. **Exceeds R1/R2?** Yes (S2/S3).
3. **Anatomy (A2):** includes `671_to_Ab`, `671_to_LThigh`, `671_to_RThigh`, `Ab_to_Chest`, `LFArm_to_LHand`, `LShin_to_LFoot`, `LThigh_to_LShin`, `LUArm_to_LFArm`. S3 subset: left thigh chain + left hand + left foot links.
4. **Conv:** D12 exceeds Drep **where cells pass** (median 1.68) but only **3/6** reliable cells → **LIMITED** detection confidence vs JcvPCA.
5. **Exercises (among reliable cells):** ex11 (2.39×), ex13, ex12.
6. **Explicit features:** trunk_arm_lagged_coupling / regional_coupling where available; amp-residual support thin.
7. **RQA:** no complementary cell for 671.
8. **Transformer:** no add.
9. **Pattern:** **Complementary disagreement in confidence** — JcvPCA strongest / most robust; Conv sparse. Do not let Conv weakness erase JcvPCA A2; do not claim latent-model confirmation.
10. **Motor adaptation claim:** Best-supported link-level redistribution beyond R1/R2 with robustness + S3 candidates; Conv does not robustly corroborate at embedding level. A3 still not formally approved.

### 790

1. **Strongest supported JcvPCA:** D12 A2 = **7/20**, adequate coverage, S3=0, rep_pass False. One persistent link (`LFArm_to_LHand`). D13 A2=3 with adequate coverage (unusual — coverage OK but fewer A2).
2. **Exceeds R1/R2?** Yes for 7 A2 links at D12.
3. **Anatomy:** bilateral thighs, chest–RShoulder, left arm proximal, right shin–foot, right thigh–shin, left hand.
4. **Conv:** Yes at D12 (1.61×, 4/6); stronger median ratio at D13 (5.65×).
5. **Exercises D12:** ex13, ex11, ex12.
6. **Explicit features:** effective_dimensionality, participation_entropy (+ amp residuals) dominate.
7. **RQA:** complementary **790–ex11–D12** (amp-preserving).
8. **Transformer:** no add.
9. **Pattern:** **Convergent detection** JcvPCA A2 + Conv >Drep at D12; features suggest entropy/dimensionality shifts; RQA adds limited temporal complement on ex11. Supervisor docs treat 790 as caution/limits case — keep confidence moderate (rep_pass false; some Conv cell failures).
10. **Motor adaptation claim:** Participant-specific D12 redistribution and latent change above repetition floors are supported at moderate confidence; not a cohort prototype.

---

## Cross-participant synthesis (no forced pattern)

| Relationship | Who |
|---|---|
| Convergent detection (JcvPCA A2 + Conv >Drep) at D12 | **651**, **790** |
| JcvPCA strong / Conv limited | **671** |
| JcvPCA limited A2 / Conv ≤Drep at D12 | **252** |
| RQA temporal complement | **651–ex13–D12**, **790–ex11–D12** only |
| Only S3 candidates | **671 T2** |

Task-variable stabilisation: **NOT_APPLICABLE** for all (not measured).

---

## Disagreements documented

| Conflict | Resolution |
|---|---|
| July-18: 651 S3=5 | **Stale**; marker-gap S3=0 for 651 |
| July-18: 252 T3 org 19/19 | **Stale**; marker-gap 10/0/0 |
| Hand-copied S3=0 snapshot | **Stale**; NV S3=4 @ 671 T2 |
| 252 D12 JcvPCA A2 vs Conv ≤Drep | **Real complementarity/discordance** — keep both; do not average |

---

## CSV schema note

Each row = participant × comparison × exercise scope × method, with categorical fields and `source_file`. Exercise-level Conv rows included for ex09–ex13; pooled rows carry primary narrative fields.
