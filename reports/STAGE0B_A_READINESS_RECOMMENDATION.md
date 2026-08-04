# Stage 0B-A readiness recommendation

Context: Stage 0 **LIMITED GO**. Shared-direction search stays closed. This module
characterises individual Conv-linked change only.

## Answers

### 1. Which participants show a reliable interpretable change?

Strongest: 651 (D12+D13), 790 (D12+D13), 252 (D13 only; D12 reliable but ≤ Drep). 671: D12 reliable on 3/6 cells; D13 only 1/6 (limited). See q1_detailed for per-comparison status.

Detail: 252/D12: reliable_but_le_repetition (cells 6/6, median ‖Δ‖/Drep=0.78); 252/D13: reliable_change_gt_repetition (cells 6/6, median ‖Δ‖/Drep=2.65); 651/D12: reliable_change_gt_repetition (cells 5/6, median ‖Δ‖/Drep=9.25); 651/D13: reliable_change_gt_repetition (cells 5/6, median ‖Δ‖/Drep=1.09); 671/D12: reliable_change_gt_repetition (cells 3/6, median ‖Δ‖/Drep=1.68); 671/D13: limited_reliable_change_gt_repetition (cells 1/6, median ‖Δ‖/Drep=1.24); 790/D12: reliable_change_gt_repetition (cells 4/6, median ‖Δ‖/Drep=1.61); 790/D13: reliable_change_gt_repetition (cells 4/6, median ‖Δ‖/Drep=5.65)

### 2. Which comparisons are reliable: T1→T2, T1→T3, or both?

T1→T2 (latent>Drep with ≥3 reliable cells): 651, 790 (671 borderline 3/6). T1→T3: 252, 651, 790 (671 only 1/6 — not a firm T1→T3 claim). Both firmly: 651 and 790.

### 3. Which exercises drive each participant’s change?

252/D12: ex10, ex9; 252/D13: ex12, ex10; 651/D12: ex11, ex13; 651/D13: ex10, ex11; 671/D12: ex11, ex13; 671/D13: ex9, ex13; 790/D12: ex11, ex13; 790/D13: ex11, ex13

(Fractions are mean ‖Δ_e‖ / ∑‖Δ_e‖ over reliability-qualified fold×seed cells.)

### 4. Which explicit features changed beyond repetition variability?

252/D12: lr_symmetry, lr_symmetry_amp_residual, regional_coupling, total_energy_deg2_s2; 252/D13: lr_symmetry_amp_residual, lr_symmetry, regional_coupling, trunk_arm_lagged_coupling; 651/D12: active_region_count, energy_share_trunk_spine, trunk_arm_lagged_coupling, participation_entropy_bits; 651/D13: effective_dimensionality, participation_entropy_bits_amp_residual, participation_entropy_bits, effective_dimensionality_amp_residual; 671/D12: trunk_arm_lagged_coupling, trunk_arm_lagged_coupling_amp_residual, total_energy_deg2_s2, regional_coupling; 671/D13: active_region_count, energy_share_trunk_spine, regional_coupling, total_energy_deg2_s2; 790/D12: effective_dimensionality, participation_entropy_bits, trunk_arm_lagged_coupling, energy_share_head_neck; 790/D13: energy_share_right_leg, participation_entropy_bits, effective_dimensionality, effective_dimensionality_amp_residual

Amplitude-residual exceedances matter more than raw energy for coordination claims.

### 5. Are the latent changes explained mainly by amplitude?

Amplitude-dominated cases: none. Cases with amp-residual feature support: [('252', 'D13'), ('651', 'D12'), ('651', 'D13'), ('671', 'D12'), ('790', 'D12'), ('790', 'D13')]. Overall: latent changes are not uniformly amplitude-only; check per participant.

No case met the strict amplitude-dominated flag (high |corr| with |ΔE|, energy
exceeds Drep, and zero amp-residual feature exceedances). Several cases still
show substantial energy change alongside coordination residuals — mixed, not
energy-only.

### 6. Is there evidence for different individual coordination adaptations?

Across participants, top-2 exercise contribution patterns for T1→T2 yield 2 distinct ordered pairs among 4 participants with data — suggests differentiated exercise drivers. Feature exceedance sets also differ (see profiles). Not a shared-direction claim.

### 7. Is the existing Conv representation suitable for a transfer test on free movement?

Yes, cautiously: Conv shows reliability-gated individual latent changes that often exceed repetition variability for multiple participants, with at least some cases not flagged as amplitude-dominated. Transfer should be a frozen-encoder test with the same skill/Drep discipline — not a search for shared direction.

### 8. Next stage recommendation

**structured-versus-free transfer benchmark**

Prefer a structured-versus-free transfer benchmark over dumping free movement into an untested latent space: embed free sessions with frozen Conv, compare neighbourhoods / reconstruction skill / feature alignment to structured exercises within participant, and keep R1–R2 and reliability gates. Direct unsupervised free-movement interpretation is premature.

---

## Stop gate

Do **not** start free-movement analysis, clustering, motif discovery, or new
training until this recommendation is reviewed.

Hard constraints from LIMITED GO remain: no shared-direction fishing; no
Transformer scaling; session–timepoint confounding unresolved.

Artifacts: `outputs/stage0b_individual_profiles/`, `figures/stage0b_individual_profiles/`.
