# Stage 1 Pre-Freeze Audit

**Date:** 2026-08-04  
**Branch:** `exploratory/guided-rqa-plan`  
**Scientific freeze (untouched):** `guided-analysis-freeze-v1` → `5062e22`  
**Classification:** `STAGE1_FREEZE_APPROVED_WITH_DOCUMENTATION_FIXES`

**External / feature audits (required before freeze):**

| Audit | Path | Result |
|---|---|---|
| Paper-code RQA reference | `PAPER_CODE_REFERENCE_AUDIT.md` | `NO_MATERIAL_DISCREPANCY_RETAIN_PRIMARY` |
| Source data & feature representation | `SOURCE_DATA_AND_FEATURE_AUDIT.md` | `CURRENT_FEATURE_VALID_ADD_SECONDARY_LATER` |
| Feature decision | `FEATURE_REPRESENTATION_DECISION.md` | A1 primary; A2 sensitivity; B2 secondary later |

---

## Verdict summary

Stage 1 technical feasibility is supported. The rate bake-off used **physically matched** delays. Selection of 120 Hz is defensible from T1 R1/R2 and surrogate evidence, not sample count alone. Full-shuffle surrogates strongly validate that DET/LAM/Lmean detect temporal organization. Parameter locks used balanced T1-only samples without T2/T3 outcome shopping.

The paper-code reference audit confirmed metric conventions against the pinned RQA backend. The source-data / feature audit confirmed that the primary input — regional angular-velocity magnitude from filtered parent-relative rotvecs — is mathematically adequate (geodesic A2 equivalent for Stage 1 conclusions) and scientifically appropriate; root-relative positional speed is optional secondary later and does **not** invalidate locks.

Documentation fixes are required before freeze: physical-time fields in the lock, revised rate-bakeoff table at radius 0.35, block-shuffle graded-control interpretation, input hashes, and environment manifest. These do **not** change the Stage 1 pass conclusion.

**Stage 2 may proceed after freeze** on the angular-speed primary.

---

## 1. Physical-time interpretation

| Quantity | Value |
|---|---|
| Primary rate | 120 Hz |
| τ | 18 frames = **0.15 s** |
| m | 4 |
| Embedding span `(m−1)τ` | 54 frames = **0.45 s** |
| Theiler | 18 frames = 0.15 s |
| Block shuffle (locked) | 0.30 s = 36 frames |

### Rate comparison physical matching

Code in `scripts/03_lock_parameters.py` sets `tau = round(tau_seconds * rate)` with `tau_seconds = 0.15` from the 60 Hz AMI aggregate.

Verified bake-off frames:

| Rate | τ frames | τ seconds | Embed span |
|---|---|---|---|
| 120 Hz | 18 | 0.150 | 0.45 s |
| 60 Hz | 9 | 0.150 | 0.45 s |
| 30 Hz | 4 | 0.133 | 0.40 s |

AMI medians in seconds were consistent across rates (~0.13–0.17 s). Theiler windows scaled with τ. Line lengths were re-expressed in seconds in the audit diagnostic (`Lmean_s`).

**Verdict:** Rate comparison was physically matched. Not a same-frame-τ error. Minor 30 Hz rounding (4 frames → 0.133 s) is acceptable for a diagnostic rate.

---

## 2. Justification for 120 Hz

Recomputed T1-only physically matched bake-off at locked radius 0.35 (`outputs/t1_diagnostics/rate_bakeoff_physical_r035_drep.csv`):

| Rate | median Drep DET | median DET drop (full shuffle) | median RR | median Lmean (s) | n samples |
|---|---|---|---|---|---|
| 120 | 0.014 | 0.932 | 0.033 | 0.051 | 1379 |
| 60 | 0.074 | 0.837 | 0.033 | 0.065 | 690 |
| 30 | 0.136 | 0.624 | 0.036 | 0.109 | 345 |

Answers:

1. **Was 120 Hz more stable/informative?** Yes on T1 R1/R2 DET repeatability and surrogate DET disruption—not merely because N is larger.
2. **Were 60 Hz results consistent?** Yes qualitatively (strong surrogate drop, usable RR); weaker R1/R2 than 120.
3. **Did 30 Hz show oversampling artifact?** It shows degraded R1/R2 and weaker surrogate disruption; Lmean in **seconds** is longer at 30 Hz, arguing against “120 Hz inflates line lengths via oversampling.”
4. **Did 120 Hz inflate line metrics via smoothness?** ACF lag-1 is high (0.987), confirming redundancy, but Theiler=τ removes trivial adjacency; physical Lmean is shorter at 120 than at 30 Hz.
5. **Was Theiler sufficient?** Default Theiler=τ; Stage 1 sensitivity `theiler_2τ` left DET nearly unchanged (gate: median |ΔDET| across τ band ≈ 0.0008).
6. **Would 60 Hz change Stage 1 conclusion?** No—full-shuffle disruption and technical feasibility would still pass; 120 Hz is preferred, not mandatory for the pass.

**Verdict:** 120 Hz retained on T1 technical grounds. Sample count was not the sole criterion.

---

## 3. Block-shuffle duration

Provenance: `block_shuffle_seconds_proposed = max(0.25, 2 × τ_median_seconds)` from AMI aggregates → locked **0.30 s**.

T1 diagnostic across block lengths (`block_shuffle_diagnostic.csv`):

| Block | DET drop (block) | DET drop (full) | Lmean drop (block) |
|---|---|---|---|
| 0.20 s | 0.084 | 0.930 | 2.56 |
| **0.30 s** | **0.041** | **0.930** | **1.75** |
| 0.45 s | 0.027 | 0.930 | 1.58 |
| 0.50 s | 0.028 | 0.930 | 1.43 |

Findings:

- 0.30 s > frame-level smoothness and ~2×τ; shorter than many multi-second exercise structures.
- Full shuffle and block shuffle are **clearly distinguishable** (opposite of identical).
- Block shuffle only weakly reduces DET because DET is near ceiling (~0.98) with `Lmin=2`; it does reduce Lmean more clearly.
- Longer blocks disrupt DET even less (preserve larger chunks).

**Verdict:** Keep 0.30 s as the locked secondary control. Treat **full shuffle as the primary negative control** for DET/LAM structure. Document block shuffle as a graded control that mainly shortens diagonal runs (Lmean) on these near-ceiling DET series. Stage 2 should include `Lmin=3` sensitivity because of DET ceiling—not a Stage 1 fail.

---

## 4. Parameter-lock integrity

| Parameter | T1-only? | Balanced 4-pid AMI/FNN? | Notes |
|---|---|---|---|
| Rate | Yes | Bake-off on 651/790 T1 (longitudinal cohort); AMI/FNN on all 4 | Acceptable: rate scored on Stage-1 cohort after common τ/m from all 4 |
| τ / m | Yes | Yes — 252/651/671/790 × R1/R2 × ex09–13 × 5 regions | At 120 Hz: tau_ami median 16 (q25–75: 14–19); m_fnn mostly 4; locked τ=18, m=4 (upper-common) |
| Radius 0.35 | Yes | T1 Stage-1 cells after RR diagnostic | Not tuned on T2/T3 deltas |
| Target RR 0.03 | Pre-registered | — | RR not a DV under target-RR |
| Theiler / Lmin | Yes | Defaults τ / 2 | — |
| Block 0.30 s | Yes | From AMI aggregates | — |

No evidence of selecting settings to maximize T1→T3 separation.

---

## 5. Threshold logic

- Amp-preserving Auto-RQA: fixed mean-rescaled radius; RR is an outcome.
- Trial z-score: target-RR; ε reported; RR not interpreted as DV.
- T1 amp-preserving RR @ radius 0.35: median ≈ 0.036; sparse RR<0.01: 0%; saturated RR>0.15: 7.5% (mostly some leg cells). Acceptable with noted heterogeneity.

---

## 6. R1/R2 and duration

- No 15% relative or 70% stable-cell hard gates in Stage 1 gate code.
- Multi-indicator summaries use absolute Drep, Drep/IQR scale normalization, descriptive `|Δ|/Drep`.
- `|Δ|/Drep > 1` reported descriptively only (frac ≈ 0.23–0.30)—not sole pass criterion.
- Duration: same-exercise claims; duration/`N_embed` recorded; Lmean primary; truncation sensitivity median |ΔDET| ≈ 0.

---

## 7. Surrogate validity

- Full shuffle: median DET drop ≈ 0.93; 100% cells drop > 0.
- Block shuffle: weak DET drop, clearer Lmean drop; seeds documented in scripts.
- Surrogates establish temporal sensitivity, not longitudinal meaning.

---

## 8. Isolation and reproducibility

| Check | Status |
|---|---|
| All RQA under `rqa_guided_pilot/` | Pass |
| Frozen inputs read-only | Pass |
| `guided-analysis-freeze-v1` = `5062e22` | Pass |
| Cache gitignored / empty at freeze | Pass |
| `EXTERNAL_TOUCHES.md` documents `.gitignore` | Pass |
| Unit tests | Pass (5/5) |
| Input hashes | Added `manifests/stage1_input_hashes.json` |
| Environment | Added `manifests/stage1_environment.json` |

---

## Corrections made (documentation / diagnostics only)

1. Wrote this audit.
2. Added physically matched rate bake-off tables at radius 0.35.
3. Added block-shuffle length diagnostic table.
4. Updated parameter lock with physical-time fields, revised rate scores, block-shuffle interpretation, DET-ceiling note.
5. Added input hashes + environment manifests.
6. Updated Stage 1 summary/gate language for block-shuffle and physical-time.
7. Added paper-code reference audit (`PAPER_CODE_REFERENCE_AUDIT.md`).
8. Added source-data / feature-representation audit and decision reports.

**No longitudinal T2/T3 retuning. No change to frozen scientific outputs outside `rqa_guided_pilot/`.**  
**No Stage 1 feature replacement; no parameter-lock invalidation.**

---

## Final classification

# `STAGE1_FREEZE_APPROVED_WITH_DOCUMENTATION_FIXES`

Supporting feature decision: `CURRENT_FEATURE_VALID_ADD_SECONDARY_LATER`  
Supporting paper-code decision: `NO_MATERIAL_DISCREPANCY_RETAIN_PRIMARY`

Stage 2 may proceed after Git freeze of Stage 1.
