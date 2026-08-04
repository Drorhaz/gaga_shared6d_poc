# Stage 0 final report — shared 6D motion POC

## Scope

Feasibility study (N=4): can a compact shared motion model on local 6D rotations
detect within-participant T1/T2/T3 change exceeding repetition variability, and
are change directions similar across participants? Not for intervention or
population inference.

Primary learned representation after S5–S6: **ConvMaskedPredictor**,
`masked_angular_velocity`, mask 30%, deterministic 32-D embeddings.
Transformer is sensitivity only. PCA and explicit features are references.

---

## Pipeline status

| Stage | Result |
|---|---|
| S1–S4 | Data, 18-link extraction, 6D path, windowing — validated |
| S5 | PCA / explicit / conv baselines; mask 30% frozen; velocity selected |
| S6 | Transformer does **not** beat Conv; Conv preferred |
| S6b | Conv T1/T2/T3 reliability re-gate **PASS** (with per-cell failures) |
| S7 | Embeddings, balanced standardization, Δ and Drep — done |
| S8 | Direction similarity — **no stable shared direction** |
| S9 | Representation comparison — done |
| S10 | Decision — **LIMITED GO** |

---

## Observed findings (compressed)

* Conv held-out T1 velocity skill ≈ 0.036
  (stable across folds/seeds); 6D reconstruction fails for both Conv and TF.
* Identity: PCA ≫ Conv (0.84 vs
  0.45).
* Reliability: majority of cells skill>0 at T2/T3; T1 mean skill barely positive
  due to outliers (671/790).
* Change vs repetition: among interpretable cells, most ratios > 1.
* Shared direction: not supported (sign/geometry/jackknife instability).

---

## Decision

**LIMITED GO**

Useful individual-change instrument: many reliability-qualified cells show longitudinal magnitude above within-session repetition variability, and Conv beats trivial baselines on the velocity pretext with lower identity loading than PCA. Cross-participant direction similarity is not stable across folds, seeds, and scaling choices.

Full decision document: `reports/GO_NO_GO_DECISION.md`.

---

## Limitations

* N=4; sign-flip floor p=0.125; no conventional significance.
* Session ≡ timepoint confounding.
* Skeleton template changes mid-study (endpoint-relative links mitigate, do not erase).
* Reliability gating yields unequal participant sets across fold×seed.
* Amplitude and explicit-feature links are descriptive only.

---

## Artifacts

* `outputs/s5_*`, `outputs/s6_transformer`, `outputs/s7_conv`, `outputs/s8_direction`, `outputs/s9_final`
* Reports under `reports/S5_*` … `S9_*`, `STAGE0_FINAL_REPORT.md`, `GO_NO_GO_DECISION.md`
