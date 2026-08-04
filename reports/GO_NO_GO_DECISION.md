# Stage 0 GO / NO-GO decision

## Decision

# **LIMITED GO**

Useful individual-change instrument: many reliability-qualified cells show longitudinal magnitude above within-session repetition variability, and Conv beats trivial baselines on the velocity pretext with lower identity loading than PCA. Cross-participant direction similarity is not stable across folds, seeds, and scaling choices.

---

## Answers to the ten final questions

1. **Reliable within-participant T1/T2/T3 change?**  
   Partially. After Conv reliability gating, many (not all) participant×fold×seed
   cells have skill>0 at the relevant endpoints, and among interpretable cells a
   majority show |Δ| > Drep (D12 67%,
   D13 81%).

2. **For which participants and comparisons?**  
   252 and 651 are most consistently reliable; 671 and 790 fail more often
   (especially Fold B / T1 or T3). D12 has more interpretable cells than D13.
   See `outputs/s7_conv/reliability_t1_t2_t3.csv` and S8 inclusion table.

3. **Larger than within-session repetition variability?**  
   Often yes in interpretable cells (median D12 ratio
   1.53; D13
   2.48). Not uniformly.

4. **Preliminary shared change direction?**  
   **No** stable shared direction under the pre-registered criteria
   (`shared_direction_evidence=False`).
   Mean pairwise cosines are frequently negative or geometry-dependent; jackknife
   is fragile.

5. **Stable across folds, seeds, scaling, jackknife?**  
   No for direction similarity. Yes for the weaker claim that Conv velocity skill
   is positive and that many individual changes exceed Drep.

6. **Interpretable via explicit features or body regions?**  
   Suggestive only. Explicit-feature correlations with consensus projections are
   descriptive at N≤4. Region occlusion on Fold A seed 0 is available as a
   sensitivity (`outputs/s8_direction/region_occlusion_D12_A0.csv`) and should not
   drive the decision alone.

7. **Does Conv add value beyond PCA and explicit features?**  
   Yes as a **learned motion encoder with positive pretext skill and lower
   identity loading than PCA**. No as a source of a stable cross-participant
   direction. Explicit features remain necessary for interpretation.

8. **What is prevented by session–timepoint confounding?**  
   Any causal or intervention-effect reading of T1→T2/T3. Marker reapplication and
   skeleton/template changes (already documented for 651/671) can contribute to
   apparent change.

9. **Carry into the planned larger study?**  
   **Yes, as a LIMITED instrument**: Conv (or matched small masked predictor) +
   PCA + explicit features, with mandatory reliability gating and repetition
   references. Not as a shared-direction confirmatory pipeline without redesign.

10. **Exact modifications before scaling?**  
    See list below.

## Required modifications before scaling

- Increase N substantially before any population claim; Stage 0 is N=4.
- Resolve session–timepoint confounding (e.g., same-day retest or marker-reapplication controls).
- Re-gate reliability per participant×timepoint; do not pool failed cells.
- Keep Conv (or simpler) as primary; do not scale Transformer without a clear skill advantage.
- Pre-register amplitude controls and explicit-feature correlations; treat N=4 correlations as descriptive only.
- If pursuing shared direction, require co-primary raw/standardized agreement and jackknife stability a priori.
- Retain PCA + explicit features as mandatory baselines in any larger study.

## Conditional Stage 0b (not implemented)

- Clustering of windows/embeddings within participant (exploratory).
- Motif discovery on structured exercises only.
- Transition entropy on discrete motif sequences.
- Free-movement sessions as transfer / generalization tests.
- Structured-versus-free transfer; joint training only if transfer fails.

A separate `STAGE0B_PLAN.md` is written only for GO / LIMITED GO.
