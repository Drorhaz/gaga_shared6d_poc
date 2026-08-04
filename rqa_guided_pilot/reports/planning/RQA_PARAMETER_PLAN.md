# RQA Parameter Plan

**Freeze:** `guided-analysis-freeze-v1` @ `5062e22`  
**Branch:** `exploratory/guided-rqa-plan`

Parameters are estimated and locked using **T1-only** diagnostics. T2/T3 must not enter \(\tau\), \(m\), radius, rate, or block-length selection.

---

## 1. Analysis unit and sampling rate

| Item | Decision |
|---|---|
| Unit | **Full-exercise** series (no sliding-window primary analysis) |
| Native rate | 120 Hz filtered rotvec |
| Stage 1 rate comparison | **120 Hz**, **60 Hz**, **30 Hz (diagnostic only)** |
| ~1000-sample guidance | **Heuristic**, not a hard rule |
| Primary rate lock | After T1-only bake-off (criteria below) |

### Primary rate selection criteria (T1-only)

Freeze the primary rate using joint evidence from:

1. AMI redundancy / curve class at each rate;
2. temporal autocorrelation (effective independence);
3. recurrence-density diagnostics (avoid saturation/sparsity);
4. R1/R2 repeatability of DET, LAM, Lmean;
5. sensitivity of DET, LAM, and line metrics across nearby \(\tau\)/radius;
6. temporal-surrogate disruption of structure metrics;
7. computational efficiency.

Provisional expectation (not a lock): **60 Hz** is the most likely compromise after 10 Hz filtering; 120 Hz retained only if Theiler/τ remove trivial adjacency and metrics are stabler; 30 Hz used to detect oversampling artifacts, not as default primary.

---

## 2. Embedding delay \(\tau\) (AMI)

### Estimation sample (balanced T1-only)

- Participants: **252, 651, 671, 790**
- Repetitions: **R1 and R2**
- Exercises: **ex09–ex13** where valid
- Signals: all primary regional angular-velocity-magnitude series
- Timepoints: **T1 only**

Do **not** estimate \(\tau\) from 651/790 alone (prior Conv-success bias).

### Reporting

Classify each AMI curve as: clear first minimum; plateau/shallow trough; oscillatory minima; slow decay.

### Locking rule

- Prefer a **common \(\tau\) band** (typically 3 values) spanning the central tendency of T1 estimates across pid/exercise/region.
- Region-specific \(\tau\) only if T1 diagnostics show **large, systematic, reproducible** regional differences.
- Sensitivity uses the full locked band; do not cherry-pick the \(\tau\) that maximizes T2/T3 separation.

---

## 3. Embedding dimension \(m\) (FNN)

### Estimation sample

Same balanced T1-only sample as AMI.

### Locking rule

- Prefer a **common \(m\)** across the pilot.
- Pose literature / paper case studies commonly \(m \in \{3,4,5\}\).
- If FNN estimates differ **moderately**, choose the **upper** plausible common dimension (over-embedding safer than under-embedding).
- Region-specific \(m\) only under the same strict systematic-difference rule as \(\tau\).

---

## 4. Recurrence threshold hierarchy

### Strategy A — fixed mean-rescaled radius

- Rescale distances by mean pairwise distance; set fixed \(\varepsilon\) (e.g., explore ~0.15–0.25 with RR diagnostic ~2–5%).
- **RR is an interpretable outcome**.
- Monitor amplitude/scale dependence and saturation/sparsity.

**Primary for:** amplitude-preserving Auto-RQA.

### Strategy B — fixed target recurrence rate

- Adjust \(\varepsilon\) to a target RR (e.g., ~3%).
- **RR is fixed by construction and must not be interpreted as an outcome**.
- Report \(\varepsilon\); interpret DET, LAM, Lmean, ENTR, Lmax/\(N_{\mathrm{embed}}\) under matched density.

**Primary for:** trial-z-scored Auto-RQA; compact MdRQA; CRQA.

### Assignment (locked)

| View | Primary | Secondary sensitivity |
|---|---|---|
| Amp-preserving Auto-RQA | Fixed mean-rescaled radius | Target-RR if RR pathological |
| Trial-z-scored Auto-RQA | Target RR | Fixed radius |
| Compact MdRQA | Target RR | Fixed radius |
| CRQA | Target RR | Fixed radius |

Do **not** switch strategies according to which produces stronger longitudinal results.

---

## 5. Theiler window

| Setting | Value |
|---|---|
| Default | \(\tau\) |
| Sensitivity | \(\tau\) and \(2\tau\) |
| Purpose | Exclude trivial temporal adjacency after 10 Hz filtering / high sampling |

---

## 6. Minimum line length \(L_{\min}\)

| Setting | Value |
|---|---|
| Default | 2 |
| Raise to 3 | If DET near ceiling (~0.95–1.0) or insufficient variability |
| Role | Reduce noise/interpolation-driven short diagonals |

---

## 7. Duration control parameters

Always report per segment:

- raw duration (s);
- downsampled sample count;
- embedded trajectory length \(N_{\mathrm{embed}} = N - (m-1)\tau\).

### Comparison policy

- Longitudinal and R1/R2 claims only for **matched units within the same exercise**.
- Primary diagonal duration metric: **Lmean**.
- Secondary: **Lmax / \(N_{\mathrm{embed}}\)**.
- Raw Lmax: descriptive diagnostic only.

### Stage 1 truncation sensitivity

Within each participant × exercise comparison set, truncate all series to the shortest duration in that set and recompute core metrics.  
Repeated random duration-matched subsampling: **only if** deterministic truncation materially changes conclusions (Stage 2 optional).

---

## 8. Surrogate parameters

| Control | Rule |
|---|---|
| Full shuffle | Primary negative control |
| Block shuffle | Secondary; block length from **T1-only** ACF/AMI diagnostics |
| Block length criteria | Exceed trivial frame-to-frame smoothness; preserve short local behavior; disrupt longer organization |
| CRQA | Shuffle one signal; keep the other |
| Defaults not used | Phase-randomized surrogates; circular shifts |

Focus surrogate PASS evidence on disruption of DET, LAM, Lmean, and line structure. Do not pre-register ENTR direction.

---

## 9. Normalization

| View | Method |
|---|---|
| Amplitude-preserving | Raw regional angular-velocity magnitude |
| Amplitude-normalized | Trial-level z-score of the full exercise series |
| Forbidden for between-TP claims | Local sliding-window z-scoring |

---

## 10. Narrow sensitivity grid (pre-specified)

Vary one factor at a time around locked defaults:

| Factor | Grid |
|---|---|
| Rate | 120, 60, 30 (diagnostic) until lock; then primary ± one neighbor if needed |
| \(\tau\) | Locked band (3 values) |
| \(m\) | Common value; {3,4,5} if ambiguous |
| Radius / target RR | 2–3 settings |
| Theiler | \(\{\tau, 2\tau\}\) |
| \(L_{\min}\) | {2, 3} if ceiling risk |
| Normalization | preserving, trial z-score |
| Representation | regional Auto, compact MdRQA |
| Duration truncation | on/off (Stage 1) |

Summarize consistency as the fraction of grid cells preserving sign/rank of key contrasts.

---

## 11. Explicit non-tuning rule

Do not choose \(\tau\), \(m\), \(\varepsilon\), target RR, rate, Theiler, or \(L_{\min}\) to maximize T1→T2 or T1→T3 separation. All locking uses T1 (and Stage-1 technical diagnostics) without outcome shopping.
