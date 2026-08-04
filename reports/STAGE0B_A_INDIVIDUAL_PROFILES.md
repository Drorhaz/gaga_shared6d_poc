# Stage 0B-A — Individual movement-change profiles
Primary representation: reliability-qualified **Conv** embeddings (`masked_angular_velocity`, mask 30%). No retraining. No shared-direction claim.

Layers of statement:
1. **Reliable observed change** — latent ‖Δ‖ vs Drep with skill>0 endpoints.
2. **Feature-level description** — explicit features vs R1–R2.
3. **Possible movement interpretation** — only when measurements agree.
4. **Unsupported speculation** — avoided (no unmeasured anatomical claims).

---
## Participant 252
### T1→T2 (`D12`)
- Status: **reliable_but_le_repetition**
- Reliable cells: 6/6 (100%)
- Median latent ‖Δ‖/Drep: 0.778
- Top exercises by latent ‖Δ_e‖ fraction: ex10:0.27,ex9:0.24,ex12:0.24
- Total energy exceeds R1–R2 max: True
- Coordination features exceeding R1–R2 (majority folds): lr_symmetry,lr_symmetry_amp_residual,regional_coupling,effective_dimensionality_amp_residual,trunk_arm_lagged_coupling_amp_residual,trunk_arm_lagged_coupling
- Amplitude-residual features exceeding R1–R2: lr_symmetry_amp_residual,effective_dimensionality_amp_residual,trunk_arm_lagged_coupling_amp_residual,regional_coupling_amp_residual,participation_entropy_bits_amp_residual
- corr(latent ‖Δ‖, |Δenergy|) on reliable cells: -0.281
- Amplitude-dominated flag: False

**Possible interpretation (cautious):** No robust interpretable longitudinal claim for this comparison.

### T1→T3 (`D13`)
- Status: **reliable_change_gt_repetition**
- Reliable cells: 6/6 (100%)
- Median latent ‖Δ‖/Drep: 2.655
- Top exercises by latent ‖Δ_e‖ fraction: ex12:0.27,ex10:0.22,ex11:0.19
- Total energy exceeds R1–R2 max: False
- Coordination features exceeding R1–R2 (majority folds): lr_symmetry_amp_residual,lr_symmetry,regional_coupling,trunk_arm_lagged_coupling,trunk_arm_lagged_coupling_amp_residual,regional_coupling_amp_residual
- Amplitude-residual features exceeding R1–R2: lr_symmetry_amp_residual,trunk_arm_lagged_coupling_amp_residual,regional_coupling_amp_residual,effective_dimensionality_amp_residual
- corr(latent ‖Δ‖, |Δenergy|) on reliable cells: -0.932
- Amplitude-dominated flag: False

**Possible interpretation (cautious):** Some amplitude-controlled coordination features exceed repetition variability alongside latent change → compatible with a non-amplitude coordination shift; still descriptive at this N.

---
## Participant 651
### T1→T2 (`D12`)
- Status: **reliable_change_gt_repetition**
- Reliable cells: 5/6 (83%)
- Median latent ‖Δ‖/Drep: 9.247
- Top exercises by latent ‖Δ_e‖ fraction: ex11:0.25,ex13:0.22,ex10:0.21
- Total energy exceeds R1–R2 max: False
- Coordination features exceeding R1–R2 (majority folds): active_region_count,trunk_arm_lagged_coupling,participation_entropy_bits,effective_dimensionality,participation_entropy_bits_amp_residual,active_region_count_amp_residual
- Amplitude-residual features exceeding R1–R2: participation_entropy_bits_amp_residual,active_region_count_amp_residual,effective_dimensionality_amp_residual,trunk_arm_lagged_coupling_amp_residual
- corr(latent ‖Δ‖, |Δenergy|) on reliable cells: 0.578
- Amplitude-dominated flag: False

**Possible interpretation (cautious):** Some amplitude-controlled coordination features exceed repetition variability alongside latent change → compatible with a non-amplitude coordination shift; still descriptive at this N.

### T1→T3 (`D13`)
- Status: **reliable_change_gt_repetition**
- Reliable cells: 5/6 (83%)
- Median latent ‖Δ‖/Drep: 1.095
- Top exercises by latent ‖Δ_e‖ fraction: ex10:0.25,ex11:0.22,ex13:0.21
- Total energy exceeds R1–R2 max: False
- Coordination features exceeding R1–R2 (majority folds): effective_dimensionality,participation_entropy_bits_amp_residual,participation_entropy_bits,effective_dimensionality_amp_residual,active_region_count,active_region_count_amp_residual
- Amplitude-residual features exceeding R1–R2: participation_entropy_bits_amp_residual,effective_dimensionality_amp_residual,active_region_count_amp_residual,trunk_arm_lagged_coupling_amp_residual
- corr(latent ‖Δ‖, |Δenergy|) on reliable cells: 0.744
- Amplitude-dominated flag: False

**Possible interpretation (cautious):** Some amplitude-controlled coordination features exceed repetition variability alongside latent change → compatible with a non-amplitude coordination shift; still descriptive at this N.

---
## Participant 671
### T1→T2 (`D12`)
- Status: **reliable_change_gt_repetition**
- Reliable cells: 3/6 (50%)
- Median latent ‖Δ‖/Drep: 1.684
- Top exercises by latent ‖Δ_e‖ fraction: ex11:0.23,ex13:0.20,ex9:0.20
- Total energy exceeds R1–R2 max: True
- Coordination features exceeding R1–R2 (majority folds): trunk_arm_lagged_coupling,trunk_arm_lagged_coupling_amp_residual,regional_coupling,active_region_count_amp_residual
- Amplitude-residual features exceeding R1–R2: trunk_arm_lagged_coupling_amp_residual,active_region_count_amp_residual
- corr(latent ‖Δ‖, |Δenergy|) on reliable cells: nan
- Amplitude-dominated flag: False

**Possible interpretation (cautious):** Some amplitude-controlled coordination features exceed repetition variability alongside latent change → compatible with a non-amplitude coordination shift; still descriptive at this N.

### T1→T3 (`D13`)
- Status: **limited_reliable_change_gt_repetition**
- Reliable cells: 1/6 (17%)
- Median latent ‖Δ‖/Drep: 1.236
- Top exercises by latent ‖Δ_e‖ fraction: ex9:0.29,ex13:0.23,ex12:0.19
- Total energy exceeds R1–R2 max: True
- Coordination features exceeding R1–R2 (majority folds): active_region_count,regional_coupling,trunk_arm_lagged_coupling
- Amplitude-residual features exceeding R1–R2: none
- corr(latent ‖Δ‖, |Δenergy|) on reliable cells: nan
- Amplitude-dominated flag: False

**Possible interpretation (cautious):** Latent change exceeds repetition variability, but explicit-feature support is weak or mixed → reliable latent observation without a strong feature-level interpretation.

---
## Participant 790
### T1→T2 (`D12`)
- Status: **reliable_change_gt_repetition**
- Reliable cells: 4/6 (67%)
- Median latent ‖Δ‖/Drep: 1.613
- Top exercises by latent ‖Δ_e‖ fraction: ex11:0.26,ex13:0.22,ex12:0.19
- Total energy exceeds R1–R2 max: True
- Coordination features exceeding R1–R2 (majority folds): effective_dimensionality,participation_entropy_bits,trunk_arm_lagged_coupling,effective_dimensionality_amp_residual,active_region_count,participation_entropy_bits_amp_residual
- Amplitude-residual features exceeding R1–R2: effective_dimensionality_amp_residual,participation_entropy_bits_amp_residual
- corr(latent ‖Δ‖, |Δenergy|) on reliable cells: -0.963
- Amplitude-dominated flag: False

**Possible interpretation (cautious):** Some amplitude-controlled coordination features exceed repetition variability alongside latent change → compatible with a non-amplitude coordination shift; still descriptive at this N.

### T1→T3 (`D13`)
- Status: **reliable_change_gt_repetition**
- Reliable cells: 4/6 (67%)
- Median latent ‖Δ‖/Drep: 5.645
- Top exercises by latent ‖Δ_e‖ fraction: ex11:0.37,ex13:0.20,ex12:0.18
- Total energy exceeds R1–R2 max: False
- Coordination features exceeding R1–R2 (majority folds): participation_entropy_bits,effective_dimensionality,effective_dimensionality_amp_residual,participation_entropy_bits_amp_residual,lr_symmetry_amp_residual,regional_coupling
- Amplitude-residual features exceeding R1–R2: effective_dimensionality_amp_residual,participation_entropy_bits_amp_residual,lr_symmetry_amp_residual,regional_coupling_amp_residual
- corr(latent ‖Δ‖, |Δenergy|) on reliable cells: 0.167
- Amplitude-dominated flag: False

**Possible interpretation (cautious):** Some amplitude-controlled coordination features exceed repetition variability alongside latent change → compatible with a non-amplitude coordination shift; still descriptive at this N.

---
Tables: `outputs/stage0b_individual_profiles/individual_profiles.csv`.
Gate summary: shared_direction not reopened; participants_with_reliable_gt_rep=['252', '651', '671', '790'].
