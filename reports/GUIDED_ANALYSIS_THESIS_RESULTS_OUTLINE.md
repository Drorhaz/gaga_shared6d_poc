# Guided Analysis — Thesis Results Chapter Outline

Recommended structure for the guided-improvisation Results chapter.
Keep **primary** vs **exploratory** separation explicit in headings and figure captions.

---

## 4.1 Data quality and representation validation

**Purpose:** Establish that subsequent change claims rest on a validated skeleton representation
and a pre-registered reliability framework.

Include:
- Canonical 18-link endpoint-relative representation (rotvec for QC; 6D model input).
- Preprocessing validation (filter, round-trip, unit handling, known exceptions).
- Windowing and fold definitions (A/B repetition-consistent trajectories; seeds 0/1/2).
- Reliability framework (held-out/timepoint skill > 0 gating; Drep = R1/R2 reference).
- Model-selection result: Conv + `masked_angular_velocity` + mask 30%; Transformer sensitivity only; PCA reference only.

**Primary vs exploratory:** All confirmatory unless marked sensitivity.

---

## 4.2 Reliability-gated detection of longitudinal change

Include:
- Conv prediction skill at T1/T2/T3 (framework pass; cell failures retained).
- Reliability gate and interpretable-cell counts (D12/D13).
- Change magnitude vs R1/R2 (Drep) for T1→T2 and T1→T3.
- Participant-level inclusion (do not average failed cells into primary claims).

**Key claim style:** Reliability-qualified longitudinal changes were observed for several
participants, particularly 651 and 790, and frequently exceeded within-session repetition
variability — not that “all participants learned the same way.”

---

## 4.3 Exercise-level localization

Include:
- Confirmatory unit: ex09–ex13 (Group4 curvilinear exploration).
- Participant-specific exercise drivers (ratios and/or fractions; prefer absolute change/Drep).
- Explicit statement: **no single shared exercise pattern** across participants.
- Note: session key `P1` = Task Part 1, **not** progressive cue stages.

---

## 4.4 Interpretable coordination changes

Include:
- Participation entropy, effective dimensionality, symmetry, coupling, regional shares.
- Amplitude-residual results (what survives energy control).
- R1/R2 comparisons for features.
- Separate participant profiles (651/790/252; 671 limited).

**Role split:** Conv detects/localizes; explicit features interpret.

---

## 4.5 Temporal and regional exploratory analyses

Label section **Exploratory**.
Include only stable descriptive findings from:
- temporal thirds;
- path/spread/mean-shift;
- region attribution / occlusion (with OOD caveat).

Do not promote these to confirmatory without new data/preregistration.

---

## 4.6 Cross-participant heterogeneity

Include:
- Failure of shared-direction hypothesis (S8).
- Fold/seed/scaling/jackknife instability.
- Interpretation: heterogeneous individual adaptation (descriptive), not group strategy.

---

## 4.7 Negative and methodological findings

Include:
- Conv versus Transformer (no TF advantage).
- Masked angular velocity versus masked 6D.
- PCA identity dominance → reference only.
- Unstable clustering and motifs.
- Unsupported P1–P5 segmentation.
- Partial reliability failures (671; some cells in others).

---

## Suggested narrative order rationale

Detection (4.2) before interpretation (4.4) prevents presenting features as if they were
discovered without a reliability screen. Heterogeneity (4.6) and negatives (4.7) close the
chapter so the thesis cannot be read as claiming a shared Gaga coordination strategy.
