# RQA Signal Representation Options

**Freeze:** `guided-analysis-freeze-v1` @ `5062e22`  
**Branch:** `exploratory/guided-rqa-plan`

## Locked interpretation language

| Method | Measures |
|---|---|
| Regional Auto-RQA | Recurrence and temporal organization of **regional angular-velocity-magnitude dynamics** |
| Compact MdRQA | Recurrence of **multiregional angular-velocity states** |

**Do not describe as:** posture recurrence; return to the same body configuration; recurrence of anatomical poses; stable movement motifs.

---

## Candidate evaluation

### Candidate A — regional angular-velocity magnitudes (PRIMARY)

**Definition:** For each region in `canonical_links_18.yaml` (`trunk_spine`, `left_arm`, `right_arm`, `left_leg`, `right_leg`; optional `head_neck`, total-body aggregate), compute link geodesic speeds as in `explicit_features.py` (`‖Δrotvec‖ × fps` in deg/s), then region-mean across member links. Full-exercise series.

| Criterion | Assessment |
|---|---|
| Interpretability | High for intensity dynamics; not posture |
| Dimensionality | 1 per Auto-RQA series (low) |
| Sampling density | Full frame rate before optional downsample |
| Noise sensitivity | Moderate; inherits 10 Hz filter smoothness |
| Amplitude dependence | High unless normalized / residualized |
| R1/R2 compatibility | Natural per-segment metric comparison |
| Compute cost | Low–moderate (Auto-RQA) |
| Auto-RQA suitability | **Best primary match** |
| MdRQA suitability | Channels feed compact MdRQA |

**Role:** Primary Stage-1 signal family.

### Candidate B — selected explicit coordination time series (SECONDARY / redundancy)

Examples: trunk–arm instantaneous coupling envelopes, bilateral arm difference, active-region indicators.

| Criterion | Assessment |
|---|---|
| Interpretability | High, but overlaps existing scalar coupling features |
| Dimensionality | 1 |
| Novelty risk | High redundancy with `regional_coupling` / `trunk_arm_lagged_coupling` |
| Role | Stage-2 sensitivity / redundancy checks only — not primary discovery |

### Candidate C — low-dimensional multiregion state (SECONDARY)

**Definition:** Simultaneous vector of 4–6 regional speed channels (e.g., trunk, L/R arm, L/R leg; optional head). Compact MdRQA.

| Criterion | Assessment |
|---|---|
| Interpretability | Multiregional intensity-state recurrence |
| Dimensionality | 4–6 (acceptable) |
| Compute | Higher than Auto-RQA; still feasible |
| vs 18-link MdRQA | Strongly preferred (cost + geometry) |

**Role:** Stage 1b smoke test if Auto-RQA is technically stable; Stage 2 secondary analysis.

### Candidate D — Conv window embeddings (SENSITIVITY ONLY)

| Criterion | Assessment |
|---|---|
| Sampling density | Median **5** windows/exercise (range 3–9) |
| RQA reliability | **Insufficient** relative to ~1000-sample heuristic and embedding needs |
| Role | Optional smoke test only; expected FAIL on sample count |

Do **not** use as primary RQA input.

---

## Comparison summary

| Candidate | Pilot role | Auto-RQA | MdRQA | CRQA |
|---|---|---|---|---|
| A regional speeds | **Primary** | Yes | Channels for C | Trunk vs arms (Stage 2) |
| B coordination scalars | Redundancy check | Optional | No | Optional |
| C compact multiregion | **Secondary** | n/a | Yes (4–6D) | n/a |
| D Conv embeddings | Sensitivity only | Unsuitable | Unsuitable | No |

---

## Recommendation

1. Build Candidate A from frozen filtered rotvec without changing preprocessing.
2. Run regional Auto-RQA as the primary analysis.
3. Form Candidate C from the same regional series for compact MdRQA.
4. Keep Candidate B for explicit novelty/redundancy tests.
5. Do not begin with all 18 links in MdRQA.
6. Maintain amplitude-preserving and trial-z-scored views of Candidate A/C.
