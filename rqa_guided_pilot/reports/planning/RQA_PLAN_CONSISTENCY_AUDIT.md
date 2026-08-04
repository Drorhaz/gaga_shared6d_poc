# RQA Plan Consistency Audit

**Branch:** `exploratory/guided-rqa-plan`  
**Freeze verified untouched:** tag `guided-analysis-freeze-v1` / scientific freeze commit `5062e22`  
**Audit date:** 2026-08-04  
**Purpose:** Verify agreement across all RQA planning reports before Stage 1 implementation.

Audited files:

1. `RQA_PAPER_METHOD_REVIEW.md`
2. `RQA_EXISTING_PROJECT_AUDIT.md`
3. `RQA_SIGNAL_REPRESENTATION_OPTIONS.md`
4. `RQA_PILOT_DESIGN.md`
5. `RQA_PARAMETER_PLAN.md`
6. `RQA_COMPARISON_FRAMEWORK.md`
7. `RQA_COMPUTATIONAL_ESTIMATE.md`
8. `RQA_GO_NO_GO_CRITERIA.md`
9. `RQA_IMPLEMENTATION_RECOMMENDATION.md`

---

## Checklist

| Topic | Agreed decision | Consistent? |
|---|---|---|
| Sampling-rate selection | Stage 1 compares 120 / 60 / 30 Hz (30 diagnostic); primary rate locked from T1-only AMI/ACF/RR/R1–R2/DET–LAM–line/surrogate/compute criteria; ~1000 samples = heuristic | Yes |
| T1-only parameter estimation | AMI/FNN on all 4 pids × R1/R2 × ex09–ex13 × regions; T2/T3 excluded; common band preferred; upper \(m\) if moderate FNN spread | Yes |
| Duration control | Same-exercise matched claims; report duration, sample count, \(N_{\mathrm{embed}}\); Lmean primary; Lmax/\(N_{\mathrm{embed}}\) secondary; raw Lmax diagnostic; Stage 1 truncation sensitivity | Yes |
| R1/R2 framework | Multi-indicator T1-first; no 15% / 70% hard gates; \(|\Delta|/D_{\mathrm{rep}}>1\) descriptive only, not sufficient alone; not a complete noise floor | Yes |
| Surrogate controls | Full shuffle primary; block shuffle secondary (T1 block length); CRQA shuffle-one-signal; no phase-random/circular defaults; focus DET/LAM/Lmean; no pre-registered ENTR direction | Yes |
| Threshold strategy | Amp-preserving Auto: fixed mean-rescaled radius (RR as DV). Trial-z / MdRQA / CRQA: target-RR primary (RR not DV; report \(\varepsilon\)). No outcome-driven switching | Yes |
| Primary metrics | RR (when valid), DET, Lmean, LAM, ENTR; secondary Lmax/\(N_{\mathrm{embed}}\), optional TT | Yes |
| Interpretation language | Regional intensity-dynamics / multiregional angular-velocity-state recurrence; forbid posture/pose/configuration/motif claims for Candidates A/C | Yes |
| Staged gates | T1 diagnostics → Stage 1 (651/790, ex11/ex13, T1/T3) → Stage 2 (+T2, optional CRQA) → Stage 3 (all pids, ex09–13); stop gates in design + go/no-go | Yes |
| Implementation stop point | Planning stops after reports; no RQA computation yet; Stage 1 needs separate approval; readiness = READY FOR IMPLEMENTATION | Yes |

---

## Preserved design invariants (cross-checked)

| Invariant | Present in reports? |
|---|---|
| Frozen guided-analysis state untouched | Yes |
| Regional Auto-RQA primary | Yes |
| Compact MdRQA secondary | Yes |
| Trunk–arm CRQA only after Stage 1 gates | Yes |
| 651/790 first longitudinal participants | Yes |
| ex11/ex13 first longitudinal exercises | Yes |
| Compare to Conv + explicit features | Yes |
| Transformer secondary sensitivity only | Yes |
| No shared-direction reopen | Yes |
| No free-movement / clustering / motifs | Yes |
| Keep 10 Hz Butterworth unchanged | Yes |
| Full-exercise unit (not sliding-window primary) | Yes |

---

## Resolved prior inconsistencies (from methodological review)

| Former draft issue | Resolution now reflected everywhere |
|---|---|
| Pre-declare 120 Hz primary via N≈1000 | Removed; rate bake-off + empirical lock |
| AMI/FNN on 651/790 only | Replaced with balanced T1 four-participant sample |
| Ad hoc 15% / 70% stability gates | Removed |
| Raw Lmax as primary without duration policy | Demoted; Lmean + Lmax/\(N_{\mathrm{embed}}\) |
| Missing surrogates | Added full + block shuffle |
| Ambiguous RR under target-RR | Hierarchy formalized |
| Weak PASS gate | Hardened multi-criterion PASS/FAIL |

---

## Residual non-conflicts (intentional open values)

These are **not** inconsistencies; they are values that must be frozen empirically in Stage 1:

- Numeric primary sampling rate (60 Hz expected but not locked).
- Exact common \((\tau,m)\) values.
- Exact target RR (e.g., ~3%) and fixed-radius operating point.
- Exact block-shuffle duration.
- Exact scale-normalization formula for \(D_{\mathrm{rep}}\) (must be fixed from T1 diagnostics before viewing attractive T2/T3).

---

## Audit outcome

**PASS — reports are mutually consistent** on all required topics.

**Planning readiness:** `READY FOR IMPLEMENTATION`  
**Empirical RQA status:** not started  

No RQA metrics were computed for this audit. Frozen scientific outputs were not modified.
