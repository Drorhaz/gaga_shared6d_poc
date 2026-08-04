# Stage 0B-A — Exercise contributions to Conv latent change

For each reliability-qualified fold×seed, recording Δ is the equal-weight mean of per-exercise Δ (ex09–ex13). Contribution metrics: ‖Δ_e‖ fraction, cos(Δ_e, Δ_rec), and leave-one-exercise-out drop in ‖Δ_rec‖.

## T1→T2

| Participant | Top exercises (mean frac of ‖Δ_e‖) | Most aligned (mean cos) |
|---|---|---|
| 252 | ex10=0.27, ex9=0.24, ex12=0.24 | ex9=0.90, ex10=0.89 |
| 651 | ex11=0.25, ex13=0.22, ex10=0.21 | ex12=0.92, ex13=0.92 |
| 671 | ex11=0.23, ex13=0.20, ex9=0.20 | ex11=0.94, ex10=0.93 |
| 790 | ex11=0.26, ex13=0.22, ex12=0.19 | ex13=0.76, ex11=0.68 |

## T1→T3

| Participant | Top exercises (mean frac of ‖Δ_e‖) | Most aligned (mean cos) |
|---|---|---|
| 252 | ex12=0.27, ex10=0.22, ex11=0.19 | ex11=0.85, ex12=0.77 |
| 651 | ex10=0.25, ex11=0.22, ex13=0.21 | ex9=0.72, ex11=0.59 |
| 671 | ex9=0.29, ex13=0.23, ex12=0.19 | ex9=0.99, ex11=0.98 |
| 790 | ex11=0.37, ex13=0.20, ex12=0.18 | ex13=0.95, ex11=0.94 |

Full tables: `exercise_contributions.csv`, `exercise_contribution_stability.csv`.
Figures: `figures/stage0b_individual_profiles/exercise_frac_*.png`.
