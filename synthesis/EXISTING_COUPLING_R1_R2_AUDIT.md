# Existing coupling — R1/R2 audit

**Scope:** Already-computed `regional_coupling` and `trunk_arm_lagged_coupling` only.  
**No raw recompute. No new Chang-style xcorr. No Cardan/Euler.**

---

## 1. Implementation verification (source code)

File: [`src/gaga_shared6d/explicit_features.py`](../src/gaga_shared6d/explicit_features.py)

| Metric | Input signal | Correlation | Lag | Aggregation |
|---|---|---|---|---|
| `regional_coupling` | Per-link angular **speed magnitude** (deg/s from rotvec finite differences) → regional mean speed series | **Signed** Pearson (`np.corrcoef`) | **Zero-lag only** | Mean of all pairwise region–region correlations |
| `trunk_arm_lagged_coupling` | `trunk_spine` vs `0.5*(left_arm + right_arm)` regional speeds | **Absolute** `max \|corr\|` | Lags `range(-5, 6)` inclusive (= −5…+5 frames, **includes lag 0**) | Single scalar = max abs corr over lags |

**Sampling rate:** `configs/experiment.yaml` → `capture.frame_rate_hz: 120.0`  
**Physical lag window:** ±5/120 s ≈ **±41.7 ms**.

**Regions** (`configs/canonical_links_18.yaml`): `trunk_spine`, `head_neck`, `left_arm`, `right_arm`, `left_leg`, `right_leg`.

**Comment vs code note:** Comment says “±1..5”; code also evaluates lag 0. Reported here as implemented.

---

## 2. Why Fisher-z is not applied as primary scale

| Metric | Fisher-z appropriate? | Reason |
|---|---|---|
| `regional_coupling` | **No (primary)** | Already a **mean of multiple** pairwise correlations. Saved outputs do not store the underlying pair-wise *r* values. `atanh(mean(r))` is not equivalent to mean of Fisher-z. |
| `trunk_arm_lagged_coupling` | **No** | Feature is **max \|r\|** on [0,1], not a signed correlation coefficient. Fisher-z would not recover signed phase meaning. |

**Primary analysis scale:** native feature units, as saved.  
Optional sensitivity: Fisher-z of the mean `regional_coupling` was considered and **rejected** as primary.

---

## 3. Data availability

Source: `outputs/s5_explicit/window_features.csv` (1446 windows; coupling columns present).

| Axis | Available? |
|---|---|
| Participants 252, 651, 671, 790 | Yes |
| Timepoints T1, T2, T3 | Yes (`timepoint` = 1/2/3) |
| Repetitions R1, R2 | Yes (`repetition` = 1/2) |
| Exercises ex09–ex13 | Yes |

**Grid completeness for ex09–ex13:** **120/120** cells present (4×3×2×5).  
**Windows per cell:** min 3, median 5, max 21.

Also available (coarser):
- `recording_features.csv` — 24 rows = pid×T×R **pooled across exercises** (context only).
- `exercise_feature_changes.csv` — prior fold-level Δ vs Drep (used previously in guided freeze; this audit recomputes R1/R2 logic from window means for transparency).

**STOP condition not triggered:** resolution is sufficient for lightweight aggregation of already-computed values.

---

## 4. Aggregation used (not a new feature compute)

For each `(participant, timepoint, repetition, exercise)`:

`C = mean(window-level feature values in that cell)`

Then:

- `Drep(T1) = |C(T1,R1) − C(T1,R2)|`
- `Delta12_R1 = C(T2,R1) − C(T1,R1)` (and R2 analogously)
- Same for D13 with T3.

**Drep stability floor (descriptive QC):**  
`drep_floor = max(0.01, 0.05 × |mean T1 C|)`.  
If `Drep < drep_floor`, “exceeds Drep” claims are labeled `EXCEEDS_BUT_DREP_UNSTABLE` and treated as **UNRELIABLE**.

**Robust exceed criterion (preferred):**
1. `|Delta_R1| > Drep` and `|Delta_R2| > Drep`
2. Same sign of Delta across R1 and R2
3. Drep not unstable
4. ≥3 windows in each contributing cell

---

## 5. Limitations

1. Metrics are **regional speed-magnitude** coupling — not Chang signed joint-angle phase.
2. `regional_coupling` is a whole-body mean of region pairs — poor anatomical specificity.
3. `trunk_arm_lagged_coupling` collapses sign and lag into max \|r\| — cannot report in-phase vs anti-phase.
4. JcvPCA A2 in the concordance step is **pooled ex09–13**, not exercise-resolved A2 (Layer-2 NV is firewalled from A2).
5. Many exercise cells show **opposite-sign** R1 vs R2 longitudinal deltas → `INCONSISTENT_ACROSS_REPS`.
6. N-of-1 descriptive framework; no inferential p-values.

---

## 6. Outputs

- Longitudinal table: `EXISTING_COUPLING_LONGITUDINAL_RESULTS.csv`
- Concordance: `JCVPCA_COUPLING_CONCORDANCE.md`
- Interpretation: `COUPLING_INTERPRETATION_SUMMARY.md`
- Xcorr decision: `XCORR_FINAL_RECOMMENDATION.md`
