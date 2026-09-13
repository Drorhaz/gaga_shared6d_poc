# Robustness figure design note

## 1. Exact title
Sensitivity testing shows where the body-link pattern is stable — and where it is not

## 2. One-sentence intended message
We stress-tested the detected body-link pattern across repetition design, PC selection, and QC choices, revealing both stable and sensitive cases rather than claiming global invariance.

## 3. What each robustness dimension measures
- **Repetition design:** top-5 link overlap of pooled R1+R2 vs R1-only and vs R2-only (authoritative `pooled_vs_R1_overlap`, `pooled_vs_R2_overlap` in file 06).
- **PC selection:** top-5 overlap vs the primary analysis across k = 4…10 (`k_grid_overlap_by_k`).
- **QC:** top-5 overlap after QC-drop (`qc_drop_overlap`; all eight cases = 100% in v2).
- **Coverage:** subspace coverage band (adequate/limited) as context only — not a robustness score.

Observed ranges (file 06):
- Pooled ↔ R1: 40–80%
- Pooled ↔ R2: 20–60%
- Median k-grid overlap: 20–80%
- QC-drop: 100% in all 8 cases

## 4. Why no composite robustness score
`overall_robustness_label` (stable/partial) comes from a specific QC-related heuristic and can disagree with moderate repetition overlaps. Replacing the three evidence tracks with one badge would hide real sensitivity. The figure therefore shows the raw dimensional evidence.

## 5. Which variant is clearer
**Variant A (fingerprint)** is clearer for a backup methods slide: aligned rows make stable vs sensitive cases scannable in seconds.  
**Variant B** is better if the audience needs an explicit verbal summary panel.

## 6. Recommendation
**BACKUP** — methodological strength / honesty slide.  
Not MAIN (the hero anatomical and variability figures carry the scientific story).  
Do **not** REMOVE: it answers a likely committee methods question without overclaiming.
