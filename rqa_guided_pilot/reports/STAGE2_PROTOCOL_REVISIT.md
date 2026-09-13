# Stage 2 protocol revisit — LIMITED_PASS_STOP

**Date:** 2026-08-07  
**Gate that triggered this revisit:** `LIMITED_PASS_STOP`  
**Primary feature:** A1 regional angular-velocity magnitude  
**Stage 1 freeze:** `rqa-stage1-feasibility-pass-v1` @ `e3ab3f3`  
**Scientific freeze (untouched):** `guided-analysis-freeze-v1` @ `5062e22`  
**Stage 2 tip:** `exploratory/guided-rqa-stage2` @ `4c3f075`

---

## 0. Binding decisions (do not reopen casually)

| Decision | Status |
|---|---|
| Expand to Stage 3 (252/671, ex09–ex13) | **No** |
| Merge RQA into `main` as confirmatory | **No** |
| Retrain Conv / Transformer | **No** |
| Change preprocessing / segmentation / rotvec freeze | **No** |
| Reopen shared-direction / clustering / motifs | **No** |
| Replace A1 with A2, B1, or Hybrid C as primary | **No** (unless a dedicated revisit finding forces it) |
| Promote B2 to primary without separate approval | **No** |
| Claim psilocybin / Gaga causal effects from RQA | **No** |

This revisit is a **protocol and evidence review**, not an automatic green light to re-run a broader analysis.

---

## 1. What Stage 2 established

### 1.1 Technical validity (keep)

A1 Auto-RQA is a working measurement of **temporal organization of regional angular-velocity-magnitude dynamics**:

- Full-shuffle median DET drop ≈ **0.92** (structure is real, not artifact-only).
- Duration truncation does not explain the structure metrics.
- Narrow sensitivity band (τ±1, radius 0.30/0.40, Lmin=3) does not flip signs of DET contrasts.
- Locked A1 parameters remain appropriate for this representation:
  - 120 Hz; τ = 18 (0.15 s); m = 4; radius = 0.35 × mean; block shuffle = 0.30 s.

**Implication:** The method is not broken. The stop is about **scientific novelty and amplitude-controlled longitudinal evidence**, not about discarding RQA as invalid.

### 1.2 Scientific gate (why LIMITED_PASS_STOP)

Under the pre-registered novelty rules:

| Outcome | Count / result |
|---|---|
| `NOVEL_TEMPORAL_INFORMATION` | **0** |
| `COMPLEMENTARY_INTERPRETATION` (amp-preserving only) | **2** (651–ex13–D12; 790–ex11–D12) |
| `UNSTABLE` | **22** exercise-level rows |
| Z-score cells with median \|Δ\|/Drep > 1 for structure metrics | **0** qualified cases |
| Amp ∩ z-score persistence of DET ratio > 1 | low (~0.18 of matched cells) |

**Plain-language verdict:**

> RQA detects predictable recurrence structure in regional movement-intensity dynamics, but Stage 2 did **not** show multiple participant×exercise longitudinal changes that remain distinguishable from R1/R2 variability **after amplitude normalization**, and that are clearly non-redundant with Conv/explicit features.

### 1.3 Secondary channels (context only)

| Channel | Role after Stage 2 | Gate impact |
|---|---|---|
| Compact MdRQA | Secondary; surrogate-sensitive | Does not unlock Stage 3 |
| Trunk–arm CRQA | Limited coordination check | Does not unlock Stage 3 |
| B2 root-relative hand speed | `SECONDARY_COMPLEMENTARY_SUPPORTED` (corr≈0.21 with A1 arm; own params) | **Cannot rescue** A1 gate; not primary |

---

## 2. Diagnosis: why the protocol stopped short of PASS_TO_STAGE3

Ranked hypotheses (to be tested in revisit — not assumed true):

1. **Amplitude confounding**  
   Amp-preserving complementary signals vanish under trial z-score → many “changes” may track intensity scale / energy rather than temporal reorganization.

2. **DET ceiling**  
   Amp-preserving DET often near ~0.98 with Lmin=2 → limited dynamic range for longitudinal DET; Lmean/LAM/ENTR may be more informative but were not sufficient under the median-ratio rule.

3. **R1/R2 as a hard bar**  
   Within-session repetition variability is large relative to T1→T2/T3 structure deltas for most cells; `|Δ|/Drep > 1` rarely holds after z-score.

4. **Scope too narrow or wrong contrast**  
   Only 651/790 × ex11/ex13; complementary hits were D12-heavy. The scientifically interesting reorganization may be exercise-specific, metric-specific, or not aligned with Conv localization.

5. **Redundancy with existing features**  
   Even when structure ratios look large, energy / participation / coupling may already capture the same story.

6. **Representation mismatch (secondary)**  
   A1 is validated; B2 is distinct but was not the primary gate. A revisit may ask whether endpoint displacement (B2) deserves a **separate**, pre-registered mini-protocol — still without Stage 3 expansion.

---

## 3. Goals of the protocol revisit

### In scope

1. Decide whether RQA remains useful as a **narrow exploratory descriptor** for selected cells, or should be **parked**.
2. Identify **one** of the following outcomes for the next decision point:
   - `REVISIT_PARK_RQA` — document and stop further RQA work on this dataset.
   - `REVISIT_NARROW_EXTENSION` — one tightly scoped follow-up (no 252/671; no full Stage 3).
   - `REVISIT_PROTOCOL_REVISION_THEN_RERUN_STAGE2` — change pre-registered analysis rules / metric emphasis, then re-run Stage 2 **only** on 651/790 × ex11/ex13 under a new written protocol (new branch; do not silently retune).
3. Preserve all frozen scientific artifacts and Stage 1 locks for A1 unless a material bug is found.

### Out of scope

- Stage 3 participant/exercise expansion.
- Free-movement analysis.
- Causal inference.
- Broad feature search or Hybrid C as a fishing expedition.
- Replacing A1 merely to imitate the paper’s positional/PCA pipeline.

---

## 4. Revisit workstreams

### Workstream A — Evidence autopsy (read-only first)

**Purpose:** Understand *where* A1 failed the novelty bar without changing code or parameters.

**Tasks:**

1. Tabulate, for each pid × ex × region × delta × normalization:
   - ratios for DET, LAM, Lmean, ENTR;
   - R1/R2 Drep;
   - energy / explicit feature exceedance flags;
   - Conv exercise-level ratio if available.
2. Split failures into:
   - fails R1/R2 bar;
   - passes amp-preserving but fails z-score;
   - passes both but redundant with energy/explicit;
   - passes both and non-redundant but was not classified novel due to rule gaps (document only).
3. Region focus check: are the 2 complementary cases driven by arms, trunk, or legs?
4. Metric focus check: would a pre-registered primary of **Lmean (seconds) + LAM** (instead of DET-led) have changed the gate? Report as sensitivity — **do not** change the historical Stage 2 decision retroactively.

**Deliverable:** `reports/STAGE2_REVISIT_EVIDENCE_AUTOPSY.md`  
**Branch:** continue on `exploratory/guided-rqa-stage2` or a new `exploratory/guided-rqa-revisit` from Stage 2 tip.  
**Compute:** tables/figures only; no new longitudinal shopping.

### Workstream B — Amplitude / ceiling protocol options

**Purpose:** Decide whether the novelty bar was scientifically correct or overly DET/amp-hostile for this signal.

**Options to evaluate on paper (then, if approved, on a frozen sensitivity script):**

| Option | Idea | Risk |
|---|---|---|
| B1 | Keep current dual-view rule (amp + z-score); accept LIMITED_PASS | Lowest risk; honest |
| B2 | Pre-register **z-score/target-RR as primary** for longitudinal novelty; amp-preserving for RR only | Changes interpretability; needs new Stage 2 write-up |
| B3 | Raise Lmin=3 (or Lmin=3 primary) to reduce DET ceiling; re-assess dynamic range | May help DET; must not be chosen because it maximizes T1→T3 |
| B4 | Emphasize Lmean (s) and LAM as co-primary; DET secondary when DET > 0.95 | Scientifically motivated by ceiling note already in Stage 1 lock |

**Rule:** Any option that changes the gate requires a **written protocol amendment** and a clearly labeled re-analysis (`STAGE2_REANALYSIS_*`), not an edit of the original gate.

### Workstream C — Narrow complementary-cell deep dive (optional)

**Purpose:** Treat 651–ex13–D12 and 790–ex11–D12 as **case studies**, not as Stage 3 license.

**If approved:**

1. Plot RP summaries / line-length distributions for those cells only (A1).
2. Align with Conv localization and explicit energy/coupling for the same pid×ex×delta.
3. Ask: complementary temporal description, or amplitude echo?

**Stop rule:** If deep dive does not yield a clear intensity-dynamics interpretation beyond energy, classify as descriptive only → prefer `REVISIT_PARK_RQA` or park with case-study appendix.

### Workstream D — B2 mini-protocol (optional, separate)

**Purpose:** B2 showed construct distinctness and some descriptive longitudinal ratios, but used a looser descriptive hit list and is not amplitude-novelty gated like A1.

**Only if Workstreams A–C leave an open scientific question about endpoint displacement:**

1. Write `B2_MINI_PROTOCOL.md` with pre-registered:
   - own rate/τ/m/threshold (already T1-locked for Stage 2 B2: 60 Hz, τ=12, m=3, r=0.30);
   - same amplitude dual-view and median-ratio novelty rule as A1;
   - comparison to A1 arm angular + arm energy + symmetry/coupling.
2. Re-score B2 under **the same novelty bar as A1** (not the looser descriptive hit count).
3. Outcomes: keep as secondary appendix / park / propose a later dedicated study — still **no Stage 3**.

### Workstream E — Decision workshop (required)

Answer explicitly:

1. Is LIMITED_PASS_STOP still the correct historical Stage 2 label? (**Default: yes.**)
2. Is there a justified narrow extension, or should RQA be parked?
3. If extension: what is the single pre-registered question?
4. What would count as success for that extension — written before running?

---

## 5. Recommended default path (if no new scientific urgency)

**Recommended outcome:** `REVISIT_PARK_RQA` with archival documentation.

Meaning:

- Keep Stage 1 freeze and Stage 2 reports as the record.
- State that RQA is **technically feasible** for A1 intensity dynamics but **not promoted** to a full guided-improvisation RQA extension.
- Allow B2/MdRQA/CRQA to remain as secondary appendix, not as Stage 3 drivers.
- Do not spend further compute unless a specific thesis/manuscript need requires Workstream C case studies.

**Rationale:** The go/no-go criteria already map LIMITED PASS → “continue only with a narrowly scoped extension” or stop. With zero z-score novelty cases, parking is the conservative, multiplicity-safe choice.

---

## 6. If a narrow extension is chosen instead

### Hard constraints

- Participants: **651 and 790 only**
- Exercises: **ex11 and ex13 only** (unless autopsy proves a single additional exercise is necessary — still not 252/671)
- No free movement
- No parameter retuning on T2/T3 outcomes
- New branch from Stage 2 tip, e.g. `exploratory/guided-rqa-revisit-narrow`
- New gate document; do not overwrite `STAGE2_GATE_REPORT.md`

### Allowed narrow designs (pick at most one)

**N1 — Ceiling-aware reanalysis (same data, amended metric primacy)**  
Pre-register Lmean (seconds) + LAM as co-primary under z-score/target-RR; DET secondary when median DET > 0.95. Recompute novelty table. Success: ≥2 pid×ex×delta with z-score co-primary median ratios > 1, non-redundant with energy, surrogate OK.

**N2 — Complementary case-study package**  
No new gate claim. Produce manuscript-ready figures for the 2 complementary cells + explicit “not Stage 3 evidence” banner.

**N3 — B2 under A1-equivalent novelty bar**  
Re-evaluate B2 only; success criteria identical to A1 Stage 2 novelty. Failure → park B2 as construct note only.

### Forbidden narrow designs

- Adding 252 or 671 “just to see”
- Scanning all exercises ex09–ex13
- Choosing τ/m/radius because they maximize D13
- Declaring PASS_TO_STAGE3 from B2 alone

---

## 7. Decision tree

```text
Stage 2 = LIMITED_PASS_STOP
        │
        ├─ Workstream A autopsy
        │         │
        │         ├─ Failures mostly amplitude/energy redundancy
        │         │         → prefer REVISIT_PARK_RQA
        │         │            (+ optional N2 case-study appendix)
        │         │
        │         ├─ Failures mostly DET ceiling; Lmean/LAM show coherent z-score signal
        │         │         → consider N1 (protocol amendment + labeled reanalysis)
        │         │
        │         └─ Complementary cells have clear non-energy temporal story
        │                   → N2 deep dive; still no Stage 3
        │
        └─ Optional D: B2 question remains after A1 parked
                  → N3 only; cannot unlock Stage 3
```

---

## 8. Documentation and freeze hygiene

| Artifact | Action |
|---|---|
| `STAGE2_GATE_REPORT.md` | Keep immutable as historical gate |
| `STAGE2_PROTOCOL_REVISIT.md` | This document |
| Future autopsy / reanalysis | New files with `STAGE2_REVISIT_*` or `STAGE2_REANALYSIS_*` prefix |
| Stage 1 tag | Do not move |
| `guided-analysis-freeze-v1` | Do not move |
| External paper archive / caches | Remain gitignored; do not vendor |

---

## 9. Language lock (unchanged)

Use:

- regional angular-velocity-magnitude dynamics
- movement-intensity recurrence / predictability / persistence / laminarity
- root-relative endpoint speed (B2 only)

Do not use:

- posture recurrence; anatomical pose return; stable motifs
- expanded repertoire; evidence of psilocybin effect; causal Gaga effect

---

## 10. Immediate next actions (checklist)

1. **Approve revisit outcome preference:** park (default) vs narrow extension (N1/N2/N3).
2. If park: write a short `STAGE2_FINAL_DISPOSITION.md` stating RQA parked after LIMITED_PASS_STOP; stop.
3. If narrow: write the one-page pre-registered amendment **before** any new compute; open `exploratory/guided-rqa-revisit-narrow`.
4. Run Workstream A autopsy regardless if a manuscript will cite Stage 2 (low cost, read-only).
5. Do **not** start Stage 3; do **not** add 252/671.

---

## 11. Success criteria for the revisit itself

The revisit succeeds when the team can state, in one paragraph:

> Stage 2 found A1 RQA technically valid but not Stage-3-ready. We chose [park / N1 / N2 / N3] because [amplitude redundancy / DET ceiling / case-study value / B2 construct test]. Stage 3 remains closed. Scientific freeze `5062e22` and Stage 1 tag `e3ab3f3` remain untouched.

Until that paragraph is agreed, no further RQA expansion.
