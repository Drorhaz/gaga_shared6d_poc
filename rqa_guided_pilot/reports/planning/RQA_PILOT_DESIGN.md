# RQA Pilot Design

**Freeze:** `guided-analysis-freeze-v1` @ `5062e22`  
**Branch:** `exploratory/guided-rqa-plan`  
**Status:** Planning complete — Stage 1 not executed

---

## 1. Scientific role of RQA

RQA tests whether guided improvisation shows reliable changes in the **temporal organization of regional angular-velocity-magnitude dynamics** that Conv embeddings, explicit features, PCA, and Transformer sensitivity do not already capture.

### Metric-linked questions

| Question | Metric(s) |
|---|---|
| Do intensity states recur more/less often? | RR (only under fixed-radius strategy) |
| Are revisits more/less predictable? | DET, Lmean |
| Are the longest structured episodes relatively longer/shorter? | Lmax/\(N_{\mathrm{embed}}\) (secondary) |
| More/less dwelling in quasi-stable intensity regimes? | LAM; TT if LAM effects appear |
| More/less diverse recurrent timescales? | ENTR |
| Independent of amplitude? | Parallel amp-preserving vs trial-z-score; energy residualization |
| Participant-specific temporal reorganization without shared direction? | Within-pid profiles vs R1/R2 |

Do **not** reopen the shared-direction hypothesis.

### Terminology lock

- Regional Auto-RQA → recurrence of **regional angular-velocity-magnitude dynamics**
- Compact MdRQA → recurrence of **multiregional angular-velocity states**
- Forbidden: posture recurrence; same body configuration; anatomical pose recurrence; stable movement motifs

---

## 2. Methods selected

| Method | Role | When |
|---|---|---|
| Regional Auto-RQA | Primary | Stages 1–3 |
| Compact MdRQA (4–6D) | Secondary | Stage 1b if Auto stable; Stages 2–3 |
| Trunk–arm CRQA | Optional pairwise coupling | **Only after Stage 1 gates** (Stage 2) |
| 18-link MdRQA | Not used | — |
| Conv-embedding RQA | Sensitivity smoke only | Optional; expected insufficient N |

---

## 3. Staged structure

```text
T1 diagnostics (all 4 pids) → Stage 1 (651/790) → Stage 2 (+T2, CRQA) → Stage 3 (all pids, ex09–13)
```

### Stage 0 / T1 diagnostics (before longitudinal claims)

**Purpose:** Lock \(\tau\), \(m\), primary sampling rate, block-shuffle length, and threshold operating points without using T2/T3.

**Sample:** participants 252, 651, 671, 790; R1 and R2; ex09–ex13 where valid; all primary regional signals; **T1 only**.

**Tasks:**

1. AMI + autocorrelation redundancy at 120 / 60 / 30 Hz.
2. FNN across the balanced sample; prefer common band; upper \(m\) if moderate spread.
3. Recurrence-density diagnostics under fixed mean-rescaled radius and target-RR.
4. Surrogate disruption (full shuffle, block shuffle).
5. R1/R2 multi-indicator repeatability distributions.
6. Computational timing / memory for float distance matrices.
7. **Freeze primary rate** using the selection criteria in `RQA_PARAMETER_PLAN.md`.

### Stage 1 — technical + first longitudinal feasibility

| Factor | Value |
|---|---|
| Participants | **651, 790** |
| Exercises | **ex11, ex13** |
| Timepoints | **T1, T3** |
| Repetitions | R1, R2 |
| Signals | Candidate A regional Auto-RQA; compact MdRQA smoke if Auto stable |
| Rates | 120, 60, 30 Hz (30 diagnostic) until primary locked |
| Duration | Same-exercise claims; truncation sensitivity |

**Goals:** validate pipeline; confirm common \((\tau,m)\) band; RR pathology checks; R1/R2 repeatability; surrogate disruption of DET/LAM/Lmean; duration robustness; runtime.

**Stop gate 1 (pass to Stage 2):**

- Usable common \((\tau,m)\) band from T1 diagnostics.
- Primary rate locked from T1 criteria (not sample count alone).
- No systematic gap/interpolation fabrication.
- Surrogates clearly disrupt DET/LAM/Lmean relative to real series on Stage-1 cells.
- R1/R2 variability does not dominate T1 dynamic range for the majority of Stage-1 core-metric cells (distributional assessment — **no 70% magic cutoff**).
- Duration-matched truncation does not abolish all structure contrasts of interest (or documents that raw duration drove them).
- Compute practical for Stage 2.

### Stage 2 — limited longitudinal pilot

| Factor | Value |
|---|---|
| Participants | 651, 790 |
| Exercises | ex11, ex13 |
| Timepoints | T1, T2, T3 |
| Views | Amplitude-preserving + trial-z-score |
| Optional | Trunk–arm CRQA (shuffle-one-signal control) |
| Comparison | Conv `|Δ|/Drep`, explicit features, energy residuals |

**Stop gate 2:**

- Longitudinal contrasts for ≥2 participant×exercise cells on ≥2 core structure metrics show \(|\Delta|\) exceeding \(D_{\mathrm{rep}}\) **and** survive the pre-specified sensitivity/rate band.
- Effects persist after amp-normalization or energy control for at least one clear case, **or** redundancy is clearly documented.
- Surrogate and duration controls remain satisfied.
- Outcomes: continue to Stage 3, declare LIMITED PASS, or FAIL.

### Stage 3 — four-participant feasibility

| Factor | Value |
|---|---|
| Participants | 252, 651, 671, 790 |
| Exercises | ex09–ex13 |
| Timepoints | T1–T3 |
| Parameters | **Locked** from T1/Stage 1–2 — no retuning on T2/T3 |

**Stop gate 3:** Apply `RQA_GO_NO_GO_CRITERIA.md` → PASS / LIMITED PASS / FAIL.

---

## 4. Core metrics

| Priority | Metrics |
|---|---|
| Primary | RR (only if fixed-radius strategy), DET, **Lmean**, LAM, ENTR |
| Secondary | **Lmax/\(N_{\mathrm{embed}}\)**; TT if LAM effects central |
| Diagnostic only | Raw Lmax |

Always report: raw duration (s), downsampled sample count, \(N_{\mathrm{embed}}\).

No “higher = better learning/creativity” language without contextual support.

---

## 5. Threshold strategy assignment

| Analysis view | Primary threshold strategy | RR as outcome? |
|---|---|---|
| Amplitude-preserving Auto-RQA | Fixed mean-rescaled radius | Yes (monitor scale dependence) |
| Trial-z-scored Auto-RQA | Target RR (e.g., ~3%) | **No** — report \(\varepsilon\); interpret DET/LAM/Lmean/ENTR |
| Compact MdRQA | Target RR primary (heterogeneous channels); fixed radius sensitivity | RR only under fixed-radius sensitivity |
| CRQA | Target RR primary (scale equalization across pair) | RR only under fixed-radius sensitivity |

Do **not** switch strategies based on which yields stronger longitudinal separation.

---

## 6. Surrogate controls (Stage 1 mandatory)

1. **Full time shuffle** — primary negative control (preserve marginal distribution; destroy order).
2. **Block shuffle** — secondary; block length from T1 diagnostics (exceed trivial frame smoothness; preserve short local behavior; disrupt longer organization).

CRQA: shuffle one signal, keep the other.

Expected focus: disruption of DET, LAM, Lmean, recurrent line structure.  
Do **not** pre-register ENTR direction under surrogates.

---

## 7. Preprocessing compatibility

| Topic | Decision |
|---|---|
| Filter | Keep 10 Hz Butterworth; no new cutoffs |
| Interpolation | No new gap filling; enforce paper \(g_{\max}\) if any fill unavoidable |
| Unit | Full exercise |
| Normalization | Amp-preserving + trial z-score; no local sliding z-score for between-TP claims |
| Smoothness checks | Rate bake-off, AMI/ACF, Theiler, \(L_{\min}\) ceiling, surrogates |

---

## 8. What this pilot will not do

- Modify freeze tag / historical outputs
- Retrain Conv/Transformer
- Change ex09–ex13 segmentation
- Free-movement analysis
- Clustering / motif discovery
- Shared-direction confirmatory analysis
- New architectures

---

## 9. Implementation stop point for this planning stage

Planning ends after the report package and consistency audit.  
Stage 1 implementation requires **separate approval** and must not start from this document alone.
