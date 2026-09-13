# Final recommendation — new Chang-style cross-correlation

## Classification

**`EXISTING_COUPLING_INFORMATIVE_BUT_LIMITED`**

(Not upgraded to `NEW_XCORR_MAY_ADD_VALUE`. Not downgraded to `EXISTING_COUPLING_SUFFICIENT_FOR_INTERPRETATION` or `NEW_XCORR_NOT_JUSTIFIED`.)

---

## Justification

### Why existing coupling is informative

1. Full pid×T×R×exercise grid already exists; robust D12 changes beyond R1/R2 are detectable in selected cells without new compute.
2. Adds interpretive value especially for:
   - **651–ex13** trunk–arm lagged coupling **increase** (alongside Conv/RQA context);
   - **671** mixed reorganization (regional ↓ / trunk–arm ↑) where Conv is sparse.
3. Shows both **decreases and increases** — correctly blocks a “reduced coupling = better learning” narrative.

### Why it is limited (not sufficient alone)

1. Metrics are regional **speed-magnitude** associations, not signed anatomical joint-angle coupling.
2. `trunk_arm_lagged_coupling` is max \|r\| — no in-phase/anti-phase meaning.
3. `regional_coupling` is a whole-body mean of region pairs — weak anatomical localization vs JcvPCA links.
4. JcvPCA A2 is pooled; cannot exercise-match A2 to coupling cells.
5. Many cells are R1/R2 direction-inconsistent.
6. Does **not** resolve joint-level questions (e.g. shoulder–elbow vs hip–knee) posed by Chang-style designs.

### Why not `NEW_XCORR_MAY_ADD_VALUE` (now)

Upgrade would require **all** of:

- an important anatomical question still unresolved **and**
- promising but insufficient existing evidence **and**
- a **trustworthy signed** signal **and**
- a specific (not exploratory) question.

Current blockers:

- No validated anatomical Cardan/Euler calibration from the rotvec pipeline (CLAIMS forbid anatomical joint-angle statements from these features).
- Parent-relative rotvec component correlation would **not** inherit Chang phase interpretation.
- Existing coupling already answers the narrower question (“do regional speed couplings move beyond R1/R2 in ways compatible with JcvPCA?”) at a useful descriptive level.
- Thesis packaging does not depend on new xcorr (`XCORR_OPTIONAL_BACKUP_ONLY` remains appropriate as a future option, not a current need).

### Relation to prior roadmap lock

Prior lock: `XCORR_OPTIONAL_BACKUP_ONLY`.  
This audit **does not change** that optional status into a recommendation to implement now. It clarifies that **existing** coupling already supplies limited interpretive value, so urgency for new xcorr is **lower**, not higher.

---

## If a future separate approval revisits xcorr

Only consider if a scientifically valid signed anatomical (or explicitly limited non-anatomical) representation is defined first. Do **not** reconstruct Cardan angles from current rotvecs without calibration. Prefer pre-registered intra-limb pairs, Fisher-z, R1/R2 Drep, D12 primary — as previously sketched — and stop if QC fails.

---

## Language reminder

Do not write: “cross-correlation showed reduced coupling with learning.”  
Allowed when supported: “Selected regional coupling relationships changed longitudinally beyond within-session repetition variability.”
