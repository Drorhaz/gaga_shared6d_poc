# Cross-correlation existing-work audit

**Question:** What Chang-style coupling has already been computed, and what is missing?

---

## Already computed

### 1. `regional_coupling` (explicit features)

| Property | Value |
|---|---|
| Source code | `gaga_shared6d_poc/src/gaga_shared6d/explicit_features.py` |
| Input | Per-link angular **speed magnitude** (deg/s) → regional mean speed series |
| Correlation | Signed Pearson; mean over region pairs |
| Lag | Zero-lag only |
| Anatomical grain | **Regional** (6 regions), not joint pairs |
| Outputs | Window / recording / exercise feature tables; Drep contrasts exist |
| Chang-equivalent? | **No** — speed magnitude, not joint-angle phase |

### 2. `trunk_arm_lagged_coupling`

| Property | Value |
|---|---|
| Input | `trunk_spine` vs mean(`left_arm`,`right_arm`) regional speeds |
| Lag | `range(-5, 6)` frames ≈ **±41.7 ms** at 120 Hz |
| Aggregation | **max \|corr\|** (absolute, not signed phase) |
| Outputs | Same feature pipeline; amp residuals exist |
| Chang-equivalent? | **No** |

### 3. RQA CRQA trunk–arms

| Property | Value |
|---|---|
| Source | `rqa_guided_pilot/outputs/stage2/crqa_trunk_arms.csv` |
| Construct | Recurrence of regional intensity series |
| Chang-equivalent? | **No** |

### 4. JcvPCA / preprocessing

No signed zero-lag joint-pair cross-correlation matrix found in the authoritative JcvPCA marker-gap stack. Relative rotvecs feed JcvPCA contribution metrics, not Chang r0.

---

## Missing for Chang-style analysis

| Component | Status |
|---|---|
| Signed zero-lag joint-level correlations on anatomical Cardan angles | Missing |
| Plane-wise in-phase / anti-phase interpretation | Missing (and not safely derivable from current rotvecs) |
| Intra-limb pair set (neck–trunk; shoulder–elbow–wrist; hip–knee–ankle) | Not computed as joint-angle r0 |
| Fisher-z longitudinal + R1/R2 Drep for correlations | Not computed |
| Joint-pair × exercise × repetition matrix | Missing |

---

## Conclusion

Existing coupling features measure **regional speed synchrony / lagged intensity association**, useful as descriptive explicit features, but they do **not** substitute for Chang-style signed joint-angle coupling. No duplicate Chang analysis exists; any future compute would be new — currently classified optional backup only (see feasibility doc).
