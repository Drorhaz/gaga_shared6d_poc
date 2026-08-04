# Stage 0B-A2 — Region and link attribution

## A. Direct explicit energy-share changes

From amplitude-aware recording features (0B-A). `trunk_spine` shares include pelvis–abdomen and abdomen–chest links (no separate annotated pelvis-only cue stage).

| Participant | Delta | Region | mean |Δshare|/Drep | frac exceed |
|---|---|---|---|---|
| 252 | D13 | head_neck | 1.07 | 50% |
| 252 | D13 | right_arm | 0.73 | 50% |
| 252 | D13 | left_arm | 0.67 | 50% |
| 252 | D13 | left_leg | 0.62 | 50% |
| 651 | D12 | trunk_pelvis | 4.97 | 100% |
| 651 | D12 | left_leg | 1.19 | 100% |
| 651 | D12 | head_neck | 0.89 | 50% |
| 651 | D13 | trunk_pelvis | 3.37 | 100% |
| 651 | D13 | left_arm | 1.51 | 50% |
| 651 | D13 | right_arm | 1.11 | 50% |
| 651 | D13 | head_neck | 0.73 | 50% |
| 651 | D13 | left_leg | 0.71 | 50% |
| 671 | D12 | right_leg | 1.00 | 100% |
| 671 | D13 | trunk_pelvis | 4.86 | 100% |
| 671 | D13 | left_leg | 1.16 | 100% |
| 790 | D12 | head_neck | 1.93 | 100% |
| 790 | D12 | right_arm | 1.71 | 50% |
| 790 | D12 | right_leg | 1.44 | 50% |
| 790 | D12 | left_leg | 1.40 | 50% |
| 790 | D13 | right_leg | 7.41 | 100% |
| 790 | D13 | trunk_pelvis | 0.85 | 50% |
| 790 | D13 | head_neck | 0.80 | 50% |
| 790 | D13 | left_leg | 0.78 | 50% |

## B. Frozen-encoder region zeroing (Fold A seed 0)

Zeroing a whole region sets a large input fraction to zero (mean OOD-risk flag rate=0%). Treat encoder attribution as **secondary and potentially unreliable**; prefer explicit regional shares.

| Participant | Delta | Region | mean rel Δ‖Δ‖ |
|---|---|---|---|
| 252 | D13 | right_arm | +1.785 |
| 671 | D12 | left_arm | -0.657 |
| 252 | D13 | left_arm | +0.602 |
| 651 | D12 | left_arm | -0.560 |
| 790 | D12 | left_arm | -0.519 |
| 790 | D13 | right_arm | -0.486 |
| 651 | D13 | head_neck | +0.425 |
| 651 | D13 | right_arm | +0.411 |
| 671 | D12 | right_arm | -0.370 |
| 252 | D12 | left_arm | -0.356 |
| 651 | D13 | trunk_spine | +0.335 |
| 790 | D12 | right_arm | -0.288 |
| 651 | D13 | right_leg | +0.285 |
| 651 | D13 | left_leg | +0.246 |
| 651 | D13 | left_arm | +0.245 |
| 252 | D12 | right_arm | +0.231 |
| 252 | D13 | head_neck | +0.210 |
| 790 | D12 | right_leg | +0.147 |
| 671 | D12 | head_neck | +0.145 |
| 252 | D13 | trunk_spine | -0.112 |

**Language rule:** Do not claim ‘more pelvis use’ unless `energy_share_trunk_spine` (or link-level pelvis measures) exceed Drep and preferably agree with non-OOD attribution.
