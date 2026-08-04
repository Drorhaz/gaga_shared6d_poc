# RQA Comparison Framework

**Freeze:** `guided-analysis-freeze-v1` @ `5062e22`  
**Branch:** `exploratory/guided-rqa-plan`

Fair comparison of RQA against existing guided-improvisation results. Transformer is secondary only. Shared-direction hypothesis remains closed.

---

## 1. Method roles

| Method | Role in comparison |
|---|---|
| Conv | Reliability-gated `|Δ|`, `|Δ|/Drep`, recording/exercise localization |
| Explicit features | Energy, participation entropy, effective dimensionality, symmetry, coupling, amp residuals |
| RQA | Temporal organization of regional intensity dynamics / multiregional angular-velocity states |
| Transformer | Secondary architecture sensitivity only |
| PCA | Linear spatial-variance / identity reference only — **not** RQA input |

---

## 2. Comparison questions

1. Does RQA detect changes in the same participants (esp. 651, 790; 252 on T1→T3)?
2. Does it localize the same exercises (often ex11/ex13 for those cases)?
3. Does it reproduce only amplitude or energy effects?
4. Does it add temporal information beyond explicit features?
5. Does it clarify Conv changes that lack clear biomechanical interpretation?
6. Is it useful for 671 where Conv reliability was limited?
7. Is RQA more stable than learned embeddings across R1/R2?
8. Is RQA less affected by participant identity than PCA/Conv identity probes?
9. Does it require fewer modeling assumptions?
10. Does it create a large new parameter-sensitivity burden?

---

## 3. Alignment protocol

For each participant × exercise × delta (D12/D13):

| Layer | Compare |
|---|---|
| Detection | RQA structure-metric \(|\Delta|\) vs \(D_{\mathrm{rep}}\) alongside Conv `|Δ|/Drep` (descriptive continuity) |
| Localization | Concordance of exercises with largest RQA vs Conv changes |
| Amplitude control | RQA under trial z-score / energy residualization vs explicit amp residuals |
| Feature redundancy | Correlate ΔRQA with Δenergy, Δentropy, Δeff_dim, Δcoupling, latent spread/path |
| Reliability | Multi-indicator R1/R2 for RQA vs Conv skill/Drep framework |
| 671 | Report sparse cells honestly; do not overclaim |

Matched units: **same exercise**, same pid, same TP/reps. Report duration and \(N_{\mathrm{embed}}\).

---

## 4. R1/R2 and longitudinal reporting (shared language)

### Multi-indicator T1-first repeatability (no 15% / 70% hard gates)

For each metric cell:

1. Absolute \(D_{\mathrm{rep}} = |M_{R1}-M_{R2}|\);
2. Scale-normalized \(D_{\mathrm{rep}}\) (formula fixed from T1 diagnostics, e.g. relative to median \|M\| or T1 IQR — chosen once, not after seeing attractive T2/T3);
3. R1/R2 rank consistency across regions/metrics;
4. Metric dynamic range on T1;
5. Bootstrap uncertainty where technically appropriate;
6. Descriptive \(|\Delta|/D_{\mathrm{rep}}\) for continuity with S7.

\(|\Delta|/D_{\mathrm{rep}} > 1\) may be reported but is **not sufficient alone** for an RQA PASS.

R1/R2 remains within-session repetition variability / lower-bound stability reference — not a complete noise floor.

---

## 5. Novel-information criterion

RQA is valuable only if findings are **reliable and non-redundant**.

### Counts as novel (examples)

- Predictability (DET/Lmean) changes while amplitude/energy stay similar.
- LAM/dwelling changes without large mean-state or energy shift.
- Dissociation: less recurrent (RR↓ under fixed radius) but more deterministic (DET↑), or the reverse.
- Compact MdRQA shows multiregional intensity-state reorganization not visible in scalar coupling alone.
- Clarifies a Conv-localized exercise change with a temporal-organization account.

### Counts as redundant / FAIL evidence (examples)

- RR changes only because movement amplitude changed.
- RQA metrics strongly mirror energy, participation entropy, or latent spread.
- Effects appear only at one radius, one \(\tau\), or one sampling rate.
- Line metrics mainly track segment duration.
- Surrogates preserve supposed “structure.”
- R1/R2 variability comparable to longitudinal change.

### Novelty tests (required)

1. Amplitude-preserving vs trial-z-score concordance.
2. Residualize or partial out total/regional energy; reassess ΔDET/ΔLAM/ΔLmean.
3. Correlate with explicit-feature deltas; require residual temporal signal for novelty claims.
4. Surrogate disruption of structure metrics.
5. Duration-truncation robustness.
6. Parameter/rate band consistency.

---

## 6. What not to claim from concordance

- Concordant participant/exercise localization with Conv does **not** prove RQA is redundant — it may supply the missing temporal interpretation.
- Discordant localization is informative but not automatically “better.”
- Transformer disagreement is not a primary failure mode (Transformer is sensitivity only).
- Absence of shared cross-participant RQA direction is expected and not a FAIL criterion.

---

## 7. Interpretation language in comparisons

When writing comparison narratives:

- Say “regional intensity-dynamics recurrence/predictability/persistence.”
- Do not say “pose recurrence,” “posture return,” or “motif reuse” for Candidates A/C.
- Keep Conv as detector/localizer; explicit features as biomechanical interpretation; RQA as temporal-organization extension.
