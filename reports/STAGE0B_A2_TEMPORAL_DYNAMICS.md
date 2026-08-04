# Stage 0B-A2 — Temporal dynamics within guided exercises

Window-ordered Conv embeddings. Metrics compared to R1/R2 at the later timepoint.

| Metric | Meaning |
|---|---|
| mean_position_shift | ‖mean(Tb)−mean(T1)‖ — average posture/state shift |
| spread_rms | RMS distance to within-exercise mean — exploration/spread |
| traj_length | Sum of consecutive window steps — path length |
| mean_step | Mean consecutive step — local velocity in latent space |
| half_shift | ‖late half mean − early half mean‖ — within-exercise progression |
| eff_dim | Covariance participation ratio — latent diversity |

### mean_position_shift

Fraction of exercise×fold×seed cells exceeding Drep:

- 252 D12: 40%
- 252 D13: 90%
- 651 D12: 96%
- 651 D13: 68%
- 671 D12: 80%
- 671 D13: 80%
- 790 D12: 85%
- 790 D13: 60%

### spread_rms

Fraction of exercise×fold×seed cells exceeding Drep:

- 252 D12: 60%
- 252 D13: 43%
- 651 D12: 48%
- 651 D13: 60%
- 671 D12: 60%
- 671 D13: 60%
- 790 D12: 60%
- 790 D13: 65%

### traj_length

Fraction of exercise×fold×seed cells exceeding Drep:

- 252 D12: 67%
- 252 D13: 27%
- 651 D12: 44%
- 651 D13: 76%
- 671 D12: 53%
- 671 D13: 40%
- 790 D12: 55%
- 790 D13: 60%

### half_shift

Fraction of exercise×fold×seed cells exceeding Drep:

- 252 D12: 63%
- 252 D13: 63%
- 651 D12: 52%
- 651 D13: 52%
- 671 D12: 53%
- 671 D13: 60%
- 790 D12: 55%
- 790 D13: 35%

## Pattern sketch (descriptive)

- **252 D12**: altered temporal path length (with/without mean shift) (shift exceed 40%, spread 60%, path 67%)
- **252 D13**: mixed / weak temporal-metric exceedances (shift exceed 90%, spread 43%, path 27%)
- **651 D12**: altered temporal path length (with/without mean shift) (shift exceed 96%, spread 48%, path 44%)
- **651 D13**: altered temporal path length (with/without mean shift) (shift exceed 68%, spread 60%, path 76%)
- **671 D12**: altered temporal path length (with/without mean shift) (shift exceed 80%, spread 60%, path 53%)
- **671 D13**: altered temporal path length (with/without mean shift) (shift exceed 80%, spread 60%, path 40%)
- **790 D12**: altered temporal path length (with/without mean shift) (shift exceed 85%, spread 60%, path 55%)
- **790 D13**: altered temporal path length (with/without mean shift) (shift exceed 60%, spread 65%, path 60%)

Caveat: overlapping 2 s windows inflate path length; interpret ratios vs Drep, not raw lengths.
