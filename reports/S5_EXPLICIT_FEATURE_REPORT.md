# S5 explicit movement feature report

**Descriptive only.** No intervention-effect claims. Native units preserved.
Amplitude-controlled residuals are within-participant.

---

## Features

Computed on primary-path filtered rotvecs for each 2 s window:

| Feature | Unit / meaning |
|---|---|
| `total_energy_deg2_s2` | mean squared link angular speed |
| `energy_<region>` | regional energy (six regions) |
| `energy_share_<region>` | region / total (amplitude-controlled composition) |
| `active_link_count` | links above within-window energy median |
| `active_region_count` | regions with ≥1 active link |
| `participation_entropy_bits` | Shannon entropy of link energy shares |
| `effective_dimensionality` | participation ratio of link energies |
| `lr_symmetry` | 1 − mean relative L/R energy difference |
| `regional_coupling` | mean pairwise corr of regional speed series |
| `trunk_arm_lagged_coupling` | max \|corr\| at lags ±5 frames, trunk vs arms |

Recording aggregates: mean within exercise, equal-weight across ex09–13.

Amplitude control: within each participant, residualise coordination features
against `log1p(total_energy)`.

---

## Coverage

| Level | N |
|---|---|
| Windows | 1446 |
| Recording aggregates | 24 (4 participants × 3 timepoints × 2 reps) |

---

## Observed patterns (descriptive)

Pooled mean total energy by timepoint:

| T1 | T2 | T3 |
|---|---|---|
| 2.82e5 | 2.30e5 | 2.81e5 |

Participation entropy (bits):

| T1 | T2 | T3 |
|---|---|---|
| 2.77 | 2.88 | 2.85 |

Amplitude-controlled entropy residual (within-participant):

| T1 | T2 | T3 |
|---|---|---|
| −0.044 | +0.018 | +0.026 |

After removing linear energy dependence, entropy still shows a small T1→T2/T3
shift in the pooled means. That is **compatible with** a coordination change
beyond “moving more,” but with N=4 and no inferential test it is not evidence
of an intervention effect.

Figures:

* `figures/s5_explicit/energy_entropy_by_timepoint.png`
* `figures/s5_explicit/entropy_amplitude_controlled.png`
* `figures/s5_explicit/regional_energy_shares.png`

---

## Interpretation

1. Explicit features vary across participants, timepoints, repetitions and
   exercises; tables in `outputs/s5_explicit/` support per-cell breakdowns.
2. Amplitude-controlled entropy residuals suggest **some** non-amplitude
   structure, but effect sizes are small relative to between-participant
   spread.
3. These features remain the interpretable reference for later latent
   directions (correlation / occlusion), not a substitute for them.

Artifacts: `outputs/s5_explicit/`.
