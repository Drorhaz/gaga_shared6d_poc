# S7 embedding, standardization and within-participant change

Primary representation: **ConvMaskedPredictor** / `masked_angular_velocity` /
mask 30%. Reliability re-gate: **PASS** (`S6B_CONV_RELIABILITY_GATE.md`).

**No S8 work** (no mean-pairwise cosine, no sign-flip null, no cross-participant
direction claim).

---

## Method (frozen)

1. Full unmasked 6D → encoder → mean-pool 18×24 tokens → 32-D window embedding.
2. Aggregation: windows → mean within exercise → equal-weight mean across
   ex09–13 → recording embedding (ex11 retained as breakdown columns).
3. Balanced standardization fitted on **training-T1 only** within each
   (fold, seed): block centroids → equal participant×exercise weight → per-dim
   mean/std. Applied unchanged to held-out T1/T2/T3. No whitening.
4. Raw-centred and standardized geometries are co-primary.
5. Trajectory repetition per fold supplies z(T1), z(T2), z(T3).
6. Change: `D12=z(T2)-z(T1)`, `D13=z(T3)-z(T1)`, `D23=z(T3)-z(T2)`.
7. Repetition reference: `Drep_Tp = ||z(Tp,R1)-z(Tp,R2)||` at T2 and T3
   (T1 reported descriptively). `max(Drep_T2, Drep_T3)` as conservative
   sensitivity only.
8. A delta is marked interpretable only if both endpoint timepoints have
   `skill > 0` for that participant×fold×seed.

---

## Observed — reliability (Conv)

| | T1 | T2 | T3 |
|---|---|---|---|
| Mean skill | 0.0010 | 0.0219 | 0.0180 |
| % positive | 75% | 92% | 79% |

Interpretable D12 cells: 18/24  
Interpretable D13 cells: 16/24  
Interpretable D23 cells: 18/24

---

## Observed — change magnitude vs repetition (descriptive)

Raw geometry, interpretable cells only:

* |D12| / Drep_T2: mean=3.570, median=1.534, n=18
* |D13| / Drep_T3: mean=2.943, median=2.483, n=16
* |D12| / max(Drep_T2,T3): mean=2.065, median=1.368, n=18
* |D13| / max(Drep_T2,T3): mean=1.814, median=1.179, n=16

Standardized geometry, interpretable cells only:

* |D12| / Drep_T2: mean=3.278, median=1.831, n=18
* |D13| / Drep_T3: mean=2.468, median=2.263, n=16

Figures: `figures/s7_conv/change_vs_repetition_D12.png`,
`change_vs_repetition_D13.png`.

Tables:

* `outputs/s7_conv/recording_embeddings.csv` — raw + standardized recording vectors
* `outputs/s7_conv/change_vectors.csv` — D12/D13/D23 coordinates
* `outputs/s7_conv/change_magnitudes.csv` — norms, Drep, ratios, interpretability flags
* `outputs/s7_conv/standardizer_params.json` — per fold/seed mean/std

---

## Interpretation (limited — not S8)

1. Conv reconstruction skill clears the proceed rule; embeddings are usable
   with per-cell gating.
2. Change magnitudes and repetition references are reported for both
   geometries. Ratios > 1 mean change exceeds within-session repetition
   distance for that cell; this is descriptive only.
3. **No cross-participant direction similarity was computed.** That is S8.
4. Participant 252 is retained; longer T1–T3 interval is not time-normalised.

---

## Status

S7 complete. **Stop before S8.**
