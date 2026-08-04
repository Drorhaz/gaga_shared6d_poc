# Guided Analysis — Thesis Figure Plan

Original analysis figures are **not overwritten**. Thesis-selected copies live in
`figures/guided_analysis_thesis_selected/`. Manifest:
`outputs/guided_analysis_finalization/thesis_figure_selection.csv`.

---

## Figure 1 — Analysis and reliability framework
**Recommended title:** Reliability-gated Conv framework for longitudinal movement change  
**Takeaway:** Longitudinal claims are restricted to cells with positive endpoint skill and are
compared against within-session R1/R2 variability.  
**Placement:** Main text.

| Panel | Source data | Source script | Source output |
|---|---|---|---|
| Reliability T1–T3 skill | `outputs/s7_conv/reliability_t1_t2_t3.csv` | `scripts/s7_conv_embeddings_change.py` | `figures/s7_conv/reliability_t1_t2_t3.png` → `fig01_reliability_framework.png` |
| Inclusion / status | `outputs/s8_direction/inclusion_table.csv` | `scripts/s8_direction_similarity.py` | `fig01b_reliability_status_heatmap.png` |

Optional schematic (redraw for thesis): 18-link → Conv encoder → skill gate → change/Drep.

---

## Figure 2 — Participant-level longitudinal change
**Recommended title:** Reliability-qualified Conv change versus within-session repetition variability  
**Takeaway:** Several participants show T1→T2 and/or T1→T3 changes exceeding Drep; magnitude and
reliability differ across participants (651/790 strongest; 252 mainly T1→T3; 671 limited).  
**Placement:** Main text.

| Panel | Source | Script | Output copy |
|---|---|---|---|
| D12 change vs Drep | `change_magnitudes.csv` | `s7_conv_embeddings_change.py` | `fig02a_change_vs_drep_D12.png` |
| D13 change vs Drep | same | same | `fig02b_change_vs_drep_D13.png` |
| Participant median ratios | `individual_profiles.csv` | `stage0b_a_individual_profiles.py` | `fig02c_participant_latent_ratios.png` |
| Result classes | S8 inclusion/classes | `s8_direction_similarity.py` | `fig02d_change_classes.png` |

---

## Figure 3 — Exercise-level localization
**Recommended title:** Exercise-resolved change across ex09–ex13  
**Takeaway:** Change localization is participant-specific; no shared exercise driver.  
**Placement:** Main text.

| Panel | Source | Script | Copy |
|---|---|---|---|
| Ratio D12/D13 | `exercise_level_change.csv` | `stage0b_a2_guided_closeout.py` | `fig03a/b_exercise_ratio_*.png` |
| Fraction panels | `exercise_contributions.csv` | `stage0b_a_individual_profiles.py` | `fig03c/d_exercise_frac_*.png` |

---

## Figure 4 — Explicit coordination profiles
**Recommended title:** Explicit coordination feature changes and amplitude-residual exceedances  
**Takeaway:** Interpretable claims rest on feature exceedances vs R1/R2 and amplitude residuals,
not on Conv magnitude alone; profiles differ by participant.  
**Placement:** Main text.

| Panel | Source | Script | Copy |
|---|---|---|---|
| Feature exceed D12/D13 | `recording_feature_changes.csv` | `stage0b_a_individual_profiles.py` | `fig04a/b_feature_exceed_*.png` |
| Latent vs energy | `latent_vs_amplitude.csv` | same | `fig04c_latent_vs_energy.png` |
| Per-participant profiles | closeout profiles | `stage0b_a2_guided_closeout.py` | `fig04_profile_{252,651,671,790}.png` |

---

## Figure 5 — Heterogeneous change directions
**Recommended title:** No stable shared cross-participant change direction  
**Takeaway:** Pairwise direction similarity is unstable across folds/seeds/scaling and jackknife;
shared-direction hypothesis is rejected for this dataset.  
**Placement:** Main text (negative result).

| Panel | Source | Script | Copy |
|---|---|---|---|
| Cosine matrices D12/D13 | `pairwise_cosines.csv` | `s8_direction_similarity.py` | `fig05a/b_direction_raw_D*.png` |
| Mean pairwise stability | `similarity_summary.csv` | same | `fig05c_direction_stability_mean_pairwise.png` |
| Jackknife | `jackknife.csv` | same | `fig05d/e_jackknife_D*.png` |

---

## Optional exploratory figure (supplement preferred)
Use only with explicit “exploratory” labeling:
- `figX_temporal_mean_shift_D13.png`
- `figX_region_occlusion_D13.png`

**Not recommended as main-text confirmatory figures:** clustering dendrograms, P1–P5 stage plots,
Transformer-primary panels, pooled group-mean “learning” bars.

---

## Redundancy rules
- Prefer one D12+D13 pair over repeating the same ratio in both Stage0B-A and A2 styles.
- Fold×seed heatmaps of every skill cell → supplement unless needed to justify exclusions.
- Do not add free-movement figures (analysis not started).
