# RQA Implementation Recommendation

**Freeze:** `guided-analysis-freeze-v1` @ `5062e22` (do not modify)  
**Branch:** `exploratory/guided-rqa-plan`  
**Planning decision:** **READY FOR IMPLEMENTATION** (superseded for Stage 1)  
**Implementation home:** `rqa_guided_pilot/` (all RQA artifacts confined here)  
**Stage 1 empirical gate:** `PASS_TO_STAGE2` — see `../STAGE1_GATE_REPORT.md`  
**Overall RQA outcome:** not yet determined (PASS / LIMITED PASS / FAIL after full stage gates)

Stage 1 has been implemented and executed under `rqa_guided_pilot/`. Stages 2–3 still require separate approval.

---

## 1. Decision answers

### 1. Is RQA scientifically relevant?

**Yes**, as an exploratory temporal-organization extension of the frozen guided-improvisation analysis. It addresses predictability, persistence, recurrence density (when RR is a valid DV), and complexity of **regional angular-velocity-magnitude dynamics** — not shared direction, not free movement, not motifs.

### 2. What exact new information could it provide?

- Whether intensity dynamics become more/less recurrent (fixed-radius RR).
- Whether revisits become more/less predictable (DET, Lmean).
- Whether dwelling/laminarity changes (LAM; TT if warranted).
- Whether recurrent timescale diversity changes (ENTR).
- Whether those changes survive amplitude normalization, energy control, duration matching, surrogates, and parameter/rate bands — i.e., whether they are **non-redundant** relative to Conv and explicit features.

### 3. Primary signal representation

**Candidate A:** regional angular-velocity magnitudes (`trunk_spine`, `left_arm`, `right_arm`, `left_leg`, `right_leg`; optional `head_neck` / total).

### 4. RQA types

- **Primary:** regional Auto-RQA  
- **Secondary:** compact MdRQA (4–6 channels)  
- **Optional after Stage 1 gates:** trunk–arm CRQA  
- **Not used:** 18-link MdRQA; Conv-embedding RQA as primary

### 5. First participants and exercises

- Longitudinal Stage 1: **651, 790**; **ex11, ex13**; T1 and T3; R1 and R2  
- Parameter estimation (AMI/FNN/rate): **all four participants**, T1-only, ex09–ex13, R1/R2  
- Then Stage 2 adds T2; Stage 3 adds 252/671 and ex09–ex13

### 6. Primary metrics

**RR** (only under fixed-radius strategy), **DET**, **Lmean**, **LAM**, **ENTR**.  
Secondary: **Lmax/\(N_{\mathrm{embed}}\)**; TT if LAM is central. Raw Lmax diagnostic only.

### 7. How to select \(\tau\), \(m\), radius, line parameters

- AMI/FNN on **balanced T1-only** sample (all pids × R1/R2 × ex09–ex13 × regions).  
- Prefer common band; upper \(m\) if moderate FNN spread; region-specific only if large systematic T1 differences.  
- Amp-preserving Auto-RQA: fixed mean-rescaled radius primary (RR as DV).  
- Trial-z-score / MdRQA / CRQA: target-RR primary (RR not a DV; report \(\varepsilon\)).  
- Theiler default \(\tau\) (sensitivity \(2\tau\)); \(L_{\min}=2\) (raise to 3 if DET ceiling).  
- Primary **sampling rate locked empirically** from Stage 1 T1 bake-off (120 / 60 / 30 diagnostic) — **not** pre-declared as 120 Hz.

### 8. How to evaluate R1/R2 stability

Multi-indicator T1-first framework: absolute \(D_{\mathrm{rep}}\), scale-normalized \(D_{\mathrm{rep}}\), rank consistency, dynamic range, bootstrap where appropriate, descriptive \(|\Delta|/D_{\mathrm{rep}}\).  
**Removed:** fixed 15% relative and 70% stable-cell gates.  
\(|\Delta|/D_{\mathrm{rep}} > 1\) is continuity with Conv, **not sufficient alone**.

### 9. How to control amplitude

Parallel amplitude-preserving and trial-level z-score analyses; energy residualization / partialling for novelty tests; threshold hierarchy that prevents interpreting RR under target-RR.

### 10. How to compare with Conv and explicit features

Matched pid/exercise cells; localization concordance; novelty tests vs energy/entropy/dimensionality/coupling/latent path-spread; Transformer secondary only; PCA reference only (not RQA input).

### 11. What counts as genuinely new information

Reliable, surrogate-sensitive, duration-robust, amplitude-controlled changes in DET/LAM/Lmean/ENTR (and RR only when valid) that are not reducible to existing features — phrased as intensity-dynamics / multiregional angular-velocity-state organization.

### 12. How long should the pilot take?

| Phase | Estimate after implementation approval |
|---|---|
| T1 diagnostics + rate lock | ~1–2 days |
| Stage 1 | ~2–3 days |
| Stage 2 | ~3–5 days |
| Stage 3 | ~3–5 days |

Planning stage is complete with this package.

### 13. Main implementation risks

- Oversampling / filter smoothness inflating DET/LAM  
- Duration confounding of line metrics (esp. ex13)  
- Amplitude-driven RR  
- Parameter fishing if T2/T3 enter locking  
- Multiplicity across metrics/regions  
- 671 limited reliability  
- Overinterpretation as posture/motif recurrence  
- Compute blow-up without distance-matrix reuse

### 14. Next step classification

**Planning readiness:** `READY FOR IMPLEMENTATION`  

This is **not** an empirical RQA PASS. PASS / LIMITED PASS / FAIL are Stage outcomes under `RQA_GO_NO_GO_CRITERIA.md`.

### 15. Exact implementation sequence if approved

Do **not** run these steps until separately authorized:

1. Remain on `exploratory/guided-rqa-plan` (or implementation sub-branch); never modify `guided-analysis-freeze-v1`.
2. Implement Candidate A extraction from frozen filtered rotvec (read-only inputs).
3. T1-only AMI, ACF, FNN across all four participants × R1/R2 × ex09–ex13 × regions at 120/60/30 Hz.
4. Lock common \((\tau,m)\) band; choose block-shuffle length from T1 diagnostics.
5. Run recurrence-density diagnostics; assign threshold strategies per hierarchy.
6. Stage 1 Auto-RQA for 651/790 × ex11/ex13 × T1/T3 × R1/R2 with caching, surrogates, truncation sensitivity, dual normalization.
7. Apply Stage 1 stop gate; freeze primary sampling rate.
8. If pass: compact MdRQA smoke; then Stage 2 (+T2, novelty vs Conv/explicit, optional CRQA).
9. If Stage 2 pass: Stage 3 four-participant expansion with locked parameters.
10. Write empirical go/no-go decision report; stop.

**Forbidden during implementation:** retrain models; change preprocessing/filter; alter segmentation; free-movement; clustering/motifs; shared-direction reopen; merge to `main` without explicit approval.

---

## 2. What is frozen before implementation begins

| Item | Status |
|---|---|
| Scientific freeze tag `guided-analysis-freeze-v1` | Untouched |
| Pilot aim and staged structure | Locked in this package |
| Primary/secondary methods and signals | Locked |
| T1-only parameter estimation rules | Locked |
| Rate bake-off procedure | Locked (primary rate value TBD empirically) |
| Duration / surrogate / threshold / R1/R2 / PASS rules | Locked |
| Interpretation language | Locked |

---

## 3. Readiness statement

**`READY FOR IMPLEMENTATION`**

Documentation is consistent across the RQA planning reports (`RQA_PLAN_CONSISTENCY_AUDIT.md`). No RQA metrics have been computed. Stage 1 requires separate approval.
