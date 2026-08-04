# RQA Go / No-Go Criteria

**Freeze:** `guided-analysis-freeze-v1` @ `5062e22`  
**Branch:** `exploratory/guided-rqa-plan`

RQA cannot pass merely because it produces a visible T1/T3 difference.

Treat RQA initially as:

> an exploratory temporal-organization extension of the frozen guided-improvisation analysis.

Do not treat a positive RQA result as confirmation of psilocybin or Gaga effects. Preserve N=4, session–timepoint confounding, and closed shared-direction status.

---

## 1. PASS

Use when **all** of the following hold:

1. **R1/R2 repeatability acceptable** under the multi-indicator T1-first framework (absolute/scale-normalized \(D_{\mathrm{rep}}\), rank consistency, dynamic range; no ad hoc 15%/70% single cutoff).
2. **Robustness** across the pre-specified parameter and sampling-rate band (not a single \(\tau\), radius, or rate).
3. **Surrogate disruption:** full shuffle (and block shuffle) clearly disrupt DET, LAM, and Lmean / line structure relative to real series.
4. **Duration robustness:** same-exercise matched claims; truncation sensitivity does not show that line metrics merely track segment length.
5. **Amplitude control:** findings persist after trial-level z-scoring and/or energy residualization for the claimed effects (or RR claims are explicitly restricted to fixed-radius amp-preserving analyses with amplitude caveats).
6. **Non-redundancy:** information not fully reducible to energy, participation entropy, effective dimensionality, coupling, or latent path/spread.
7. **Interpretable** participant- or exercise-specific temporal finding in intensity-dynamics / multiregional angular-velocity-state language.
8. **Compute practical** under caching/reuse rules.

**Recommendation if PASS:** Implement the full guided-improvisation RQA extension (still exploratory; no group-causal claims).

---

## 2. LIMITED PASS

Use when:

- RQA is useful only for selected participants, exercises, regions, or metrics;
- parameter/rate sensitivity is moderate but not catastrophic;
- temporal information appears useful but not robust enough for broad analysis;
- 671 or other limited-reliability cases remain sparse;
- novelty holds in a narrow subset only.

**Recommendation:** Continue only with a **narrowly scoped** participant-/exercise-specific exploratory extension. Do not expand to a full confirmatory RQA program.

---

## 3. FAIL

Use when any of the following dominate:

- R1/R2 variability dominates longitudinal contrasts;
- results depend on one \(\tau\), one radius/target-RR, or one sampling rate;
- line metrics mainly reflect duration;
- surrogates preserve the supposed temporal structure (DET/LAM/Lmean not disrupted);
- results are fully explained by amplitude or existing explicit/Conv-spread features;
- RR is interpreted after being fixed by target-RR construction;
- posture/motif language is required to make results sound meaningful (overinterpretation);
- computation is disproportionate to likely scientific value after efficiency rules are applied.

**Recommendation:** Do **not** expand RQA for the current guided dataset.

---

## 4. Stage stop gates (operational)

### After T1 diagnostics + Stage 1

Proceed to Stage 2 only if:

- common \((\tau,m)\) band locked from balanced T1 sample;
- primary rate locked from T1 criteria;
- surrogates disrupt structure metrics;
- R1/R2 multi-indicator picture is not pathological;
- duration truncation check completed;
- no preprocessing fabrication issues;
- runtime acceptable.

### After Stage 2

- **Pass → Stage 3** if multiple qualified longitudinal cases show non-redundant, robust structure-metric change.
- **Limited → stop** with LIMITED PASS documentation.
- **Fail → stop** without Stage 3 expansion.

### After Stage 3

Apply sections 1–3 for final PASS / LIMITED PASS / FAIL.

---

## 5. Explicitly insufficient criteria

The following alone do **not** justify PASS:

- visible T1/T3 difference;
- \(|\Delta|/D_{\mathrm{rep}} > 1\) without other gates;
- concordance with Conv localization without novelty tests;
- high DET or high ENTR without contextual interpretation and controls;
- results at 120 Hz solely because N≈1000.

---

## 6. Statistical / interpretive limits (always retain)

- N=4; participant-level feasibility only.
- No group-level causal claims.
- Timepoint confounded with session.
- R1/R2 is not a complete noise estimate.
- Multiple metrics create multiplicity — keep primary set small.
- Parameter sensitivity can create false-positive flexibility — use pre-specified grid.
- 671 has limited existing reliability.
- No stable shared direction was previously found — do not reopen.
