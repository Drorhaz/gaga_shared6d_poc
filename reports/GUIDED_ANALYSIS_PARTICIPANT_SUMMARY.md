# Guided Analysis — Participant-Level Synthesis Table

Cautious wording. Failed fold/seed cells are not hidden.
Source rows: `outputs/stage0b_individual_profiles/individual_profiles.csv`,
`outputs/s7_conv/reliability_t1_t2_t3.csv`,
`outputs/stage0b_guided_closeout/exercise_level_change.csv`.

Machine-readable: `outputs/guided_analysis_finalization/participant_synthesis_table.csv`.

---

| Participant | Reliable comparisons | Endpoint reliability | Change > Drep | Main exercises | Main explicit features | Amp-residual findings | Main regions | Temporal findings | Conv–feature agreement | Confidence | Main limitation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 252 | T1→T2 (6/6 cells; status=reliable_but_le_repetition); T1→T3 (6/6 cells; status=reliable_change_gt_repetition) | pos skill cells T1/T2/T3 = 6/6/6 of 6 | T1→T2 no/≤Drep (median=0.78); T1→T3 yes (median \|Δ\|/Drep=2.65) | D12: ex10(1.58×Drep), ex12(1.03×Drep), ex09(0.80×Drep); D13: ex10(1.85×Drep), ex09(1.71×Drep), ex13(1.40×Drep) | D12: lr_symmetry, regional_coupling, trunk_arm_lagged_coupling; D13: lr_symmetry, regional_coupling, trunk_arm_lagged_coupling | D12: lr_symmetry_amp_residual, effective_dimensionality_amp_residual, trunk_arm_lagged_coupling_amp_residual, regional_coupling_amp_residual, participation_entropy_bits_amp_residual; D13: lr_symmetry_amp_residual, trunk_arm_lagged_coupling_amp_residual, regional_coupling_amp_residual, effective_dimensionality_amp_residual | symmetry/coupling features more than entropy profile of 651/790 | exploratory only | mixed: D13 latent>Drep with amp-residual symmetry/coupling; D12 latent≤Drep | high endpoint reliability (6/6) but T1→T2 change ≤Drep; T1→T3 stronger | T1→T2 not >Drep; feature interpretation still descriptive |
| 651 | T1→T2 (5/6 cells; status=reliable_change_gt_repetition); T1→T3 (5/6 cells; status=reliable_change_gt_repetition) | pos skill cells T1/T2/T3 = 5/6/6 of 6 | T1→T2 yes (median \|Δ\|/Drep=9.25); T1→T3 yes (median \|Δ\|/Drep=1.09) | D12: ex13(2.85×Drep), ex09(1.75×Drep), ex10(1.73×Drep); D13: ex09(1.23×Drep), ex13(1.08×Drep), ex10(0.79×Drep) | D12: active_region_count, trunk_arm_lagged_coupling, participation_entropy_bits, effective_dimensionality; D13: effective_dimensionality, participation_entropy_bits, active_region_count | D12: participation_entropy_bits_amp_residual, active_region_count_amp_residual, effective_dimensionality_amp_residual, trunk_arm_lagged_coupling_amp_residual; D13: participation_entropy_bits_amp_residual, effective_dimensionality_amp_residual, active_region_count_amp_residual, trunk_arm_lagged_coupling_amp_residual | entropy/dimensionality/active-region features; occlusion exploratory only | exploratory thirds/path only; no confirmatory stage structure | partial: latent \|Δ\|>Drep co-occurs with amp-residual entropy/dimensionality exceedances | moderate–high for reliable cells; one fold/seed cell fails T1 gate | Not all 6 fold×seed cells pass; session–timepoint confounding; N=1 case study |
| 671 | T1→T2 (3/6 cells; status=reliable_change_gt_repetition); T1→T3 limited/weak (1/6; status=limited_reliable_change_gt_repetition) | pos skill cells T1/T2/T3 = 3/6/2 of 6 | T1→T2 yes (median \|Δ\|/Drep=1.68); T1→T3 yes among sparse reliable cells (median=1.24) | D12: ex11(2.39×Drep), ex13(1.31×Drep), ex12(1.29×Drep); D13: ex09(1.88×Drep), ex13(1.30×Drep), ex12(1.02×Drep) | D12: trunk_arm_lagged_coupling, regional_coupling; D13: active_region_count, regional_coupling, trunk_arm_lagged_coupling | D12: trunk_arm_lagged_coupling_amp_residual, active_region_count_amp_residual; D13: none (majority) | sparse; coupling/active-region only where cells pass | not interpretable under current reliability | weak: latent>Drep in sparse cells; amp-residual support inconsistent | low–limited; frequent T1/T3 gate failures (pos T1 3/6, T3 2/6) | Limited endpoint reliability; D13 only 1/6 reliable cells; weak amp-residual support on D13 |
| 790 | T1→T2 (4/6 cells; status=reliable_change_gt_repetition); T1→T3 (4/6 cells; status=reliable_change_gt_repetition) | pos skill cells T1/T2/T3 = 4/4/5 of 6 | T1→T2 yes (median \|Δ\|/Drep=1.61); T1→T3 yes (median \|Δ\|/Drep=5.65) | D12: ex13(1.51×Drep), ex11(1.19×Drep), ex12(1.16×Drep); D13: ex11(2.45×Drep), ex13(1.74×Drep), ex12(1.05×Drep) | D12: effective_dimensionality, participation_entropy_bits, trunk_arm_lagged_coupling, active_region_count; D13: participation_entropy_bits, effective_dimensionality, regional_coupling | D12: effective_dimensionality_amp_residual, participation_entropy_bits_amp_residual; D13: effective_dimensionality_amp_residual, participation_entropy_bits_amp_residual, lr_symmetry_amp_residual, regional_coupling_amp_residual | entropy/dimensionality dominant; regional coupling secondary | exploratory only | partial: strong D13 latent ratio with amp-residual entropy/dimensionality | moderate; 4/6 cells typically reliable; some T1/T2 gate failures | Endpoint failures in some fold×seed cells; identity/session confounds; descriptive features |

---

## Reading notes

### 651
Reliable T1→T2 and T1→T3 latent changes exceed Drep in 5/6 cells, with amplitude-residual
support for participation entropy / effective dimensionality / active-region counts.
Exercise drivers differ by delta (D12 often ex13/ex09/ex10; D13 ex09/ex13/ex10). Treat as the
clearest individual case study, not a group prototype.

### 790
Reliable T1→T2 and T1→T3 in 4/6 cells; D13 median latent ratio is large (~5.65×Drep) with
amp-residual entropy/dimensionality exceedances. Endpoint failures remain in some cells — report
them. Exercise emphasis often includes ex11/ex13.

### 252
Endpoint reliability is excellent (6/6), but **T1→T2 latent change is ≤Drep**
(`reliable_but_le_repetition`). The primary reliable change claim is **T1→T3**, with symmetry /
coupling residuals more prominent than the entropy profile of 651/790.

### 671
Limited reliability: positive skill in 3/6 (T1) and 2/6 (T3) cells. D13 has only 1/6 reliable
cells. Any “change > Drep” statements for 671 apply only to sparse gated cells and should not be
narrated as a robust participant-level adaptation profile.

---

## Confidence scale used here
- **moderate–high:** majority cells reliable and change >Drep with some amp-residual support.
- **moderate:** majority or near-majority cells, with known endpoint failures.
- **mixed/high-endpoint but comparison-specific:** strong gates, weak D12 magnitude.
- **low–limited:** frequent gate failures.
