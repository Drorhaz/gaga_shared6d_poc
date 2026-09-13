# Committee figure data pack v2

Self-contained export for PhD-admissions figure generation.
Supersedes `committee_figure_data_pack/` (v1). No new scientific analyses were run.

## Recommended reading order

1. `README.md` (this file)
2. `00_FIGURE_PACKAGE_MANIFEST.json`
3. `05_FIGURE_REVIEW_AND_VISUAL_SPEC.json` (includes G3 Option A vs B decision)
4. `01_PARADIGM_AND_METHOD.json` (paradigm, corrected timeline, embedded geometry)
5. `02_REPETITION_VARIABILITY.csv`
6. `03_LONGITUDINAL_LINK_EVIDENCE.csv` (matched single-rep vs NV; primary A2 footing)
7. `06_JCVPCA_ROBUSTNESS.json` (pooled + R1/R2 + k-grid + QC; separate footing)
8. `04_ANATOMICAL_CONTRIBUTION_MAP_DATA.csv`

## Critical rules for visualization agents

- Do not claim treatment effects; analysis remains blinded.
- Do not mix pooled R1+R2 descriptive changes with matched single-rep / NV ratios.
- G4 is an anatomical contribution map (link/segment resolution), not a continuous body-surface heatmap.
- `visual_segment_*` fields are presentation-only mappings.
- Prefer G3 Option A (≈4 vs ≈10 class validated link evidence). Option B robustness is backup.
- Main G2 annotation: `12/12 sessions: Whole body > Hands` (slope is metadata only).
