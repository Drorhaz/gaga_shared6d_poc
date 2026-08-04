# Guided Analysis — Limitations (Freeze Text)

Do not soften these to strengthen conclusions.

1. **N=4** — no population-level inference; participant case studies only.
2. **Participant-level rather than group-level inference** — by design and by evidence (no shared direction).
3. **Variable reliability** across participants, folds, seeds, and timepoints (notably 671; partial 790/651).
4. **Endpoint gating** — failed cells are excluded from interpretable claims; remaining cells are a selected subset.
5. **R1/R2 is a within-session variability reference**, not a complete across-session noise floor.
6. **Timepoint–session confounding** — T1/T2/T3 changes cannot be attributed solely to intervention.
7. **No untreated / external movement control** in this guided package.
8. **Exercise segmentation limited to supported ex09–ex13** confirmatory blocks.
9. **Unsupported P1–P5 progressive cue segmentation** — session `P1` means Task Part 1.
10. **Potential residual amplitude influence** despite residual features and non-dominated flags.
11. **Conv identity leakage above chance** — lower than PCA in controls, not zero.
12. **Post-hoc exploratory temporal and region analyses** — thirds, path/spread, occlusion.
13. **Unstable clustering** — not confirmatory.
14. **Inability to infer stable movement motifs** on current guided data.
15. **Multiple derived features** and descriptive analysis burden — multiplicity not fully corrected at N=4.
16. **Marker/skeleton/template exceptions** documented in source validation (e.g., participant-specific unit/template issues) can contribute to apparent change.
17. **Documentation gap for VCS freeze** — `gaga_shared6d_poc` currently has no git repository; reproducibility relies on content hashes and locked requirements (see manifest).

These limitations are part of the scientific result package, not optional caveats.
