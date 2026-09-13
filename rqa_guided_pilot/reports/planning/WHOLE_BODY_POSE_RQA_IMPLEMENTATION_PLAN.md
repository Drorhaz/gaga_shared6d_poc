# Whole-body configuration-space RQA — implementation plan

**Status:** plan finalized; Stage A0 is the only authorized implementation step. A1–B remain unauthorized.  
**Date:** 2026-08-13  
**Path:** `rqa_guided_pilot/reports/planning/WHOLE_BODY_POSE_RQA_IMPLEMENTATION_PLAN.md`  
**Does not overwrite:** Stage 1/2 reports, `parameter_lock_stage1.json`, or other `RQA_*.md` planning files.

This plan is the product of a critical re-review of the intended construct, canonical data, Sale et al. (arXiv:2604.01453), and the existing RQA engine. Earlier draft choices are retained only where they remain the most defensible option.

---

## 0. Independent conclusions (read first)

| Draft choice | Verdict after review | Why |
|---|---|---|
| Call the estimand “whole-body posture recurrence” | **Reject as primary wording** | Canonical state excludes laboratory root orientation and translation. The measurable object is **internal articulated configuration**, not unrestricted posture. |
| Add pelvis/global orientation to the primary state | **Reject for primary; optional later sensitivity** | Facing/turning is a different construct; it is not in `rotvec_18link`; adding it requires a new Motive-quat path and would confound turning with joint configuration. |
| 18 endpoint-relative rotations as state | **Retain** | Smallest state that is actually a whole-body joint configuration in this project. |
| Mean link-wise SO(3) geodesic | **Retain as distance kernel** | Correct geometry; Euclidean flatten is a pilot concordance check only. |
| Equal-link weighting as primary | **Reverse** | Arms are 8/18 links (44%). That is a skeleton-density artifact, not a whole-body coordination prior. **Region-balanced is primary.** |
| No extra delay embedding | **Retain** | The observation is already the multivariate configuration. Diagonals carry trajectory recurrence. |
| RR + DET/Lmean as connected outcomes | **Retain, with stricter mixed-result language** | RR ≠ trajectory organization. Do not score “stereotypy.” |
| Mean-rescaled fixed radius, RR as DV | **Retain** | Sale §2.5.2 Strategy A; required if RR must be able to vary. Do not copy `0.35`. |
| Smallest `radius_frac` in the 2–5% band | **Reject** | Systematically prefers sparse plots. Select the grid value **closest to a pre-declared T1 median RR target of 0.03**. |
| RR failure at 0.10 and saturation at 0.20 | **Unify** | One usable band: T1 cells must lie in **[0.01, 0.10]**. Saturation = RR > 0.10. |
| T1→T2 smoke before lock | **Reject** | Unnecessary (T1 max N = 1920 vs grid max 2160) and contaminates locking. Stage B must be unable to read T2/T3 until the lock exists. |
| Copy Theiler = 0.15 s from speed Auto-RQA | **Reject automatic copy** | That τ came from AMI on regional **speed**. Pose MdRQA needs a T1 physical-time diagnostic (0.15 s vs 0.30 s). |
| Interpolation for gaps | **Forbid** | Sale: RR is gap-sensitive. Layer 2 / this project: no short-gap interpolation. |
| Build Stage B during A0–A1 | **Reject** | Pilot may invalidate the method. |
| Call primary RR “absolute recurrence” | **Reject** | Mean-rescaled ε makes primary RR **scale-relative**, not a fixed-radian neighborhood. |
| Start-crop as the duration match (existing `truncate_to_length`) | **Reject as primary** | Start-crop prefers task onset and known segmentation edges. **Centre-crop** is the required matched-duration sensitivity. |
| Absolute shuffle DET drop ≥ 0.5 as A2 gate | **Reject** | Inherited from near-ceiling regional-speed DET (~0.98). Not portable if pose DET is moderate. |
| Theiler switch if DET falls by ≥ 0.02; Lmean_s floor 0.05 s | **Reject as paper law** | Engineering tolerances, not Sale. Replaced by a coarser T1 rule (see §6). |

---

## 1. Scientific estimand and claim boundary

### Estimand

For each of four participants, during guided improvisation exercises ex09–ex13 (not concatenated), whether **scale-relative recurrence density of internal whole-body articulated configurations** and/or **organization of revisits along trajectories in that relative-orientation space** changes from T1 to T2 and from T1 to T3 (T3−T2 secondary).

Primary RR is **not** the fraction of pairs inside a common absolute angular neighborhood. It is the fraction of pairs closer than a fixed fraction of **that trial’s** mean pairwise geodesic distance.

### Precise construct

> Recurrence of **internal whole-body articulated configurations** (the 18 canonical endpoint-relative link orientations) and of **recurring trajectories through that relative-orientation space**.

This is **not**:
- unrestricted whole-body posture in the laboratory (facing, location, and root orientation are absent);
- recurrence of regional movement intensity;
- a discrete vocabulary of named motifs.

### Terminology (locked)

| Term | Meaning in this analysis |
|---|---|
| **Endpoint-relative rotation** | `q_rel = inv(q_parent_global) * q_child_global` between two named bones. For 252/790, `Ab_to_Chest` and `Neck_to_Head` span intermediate bones; the chain telescopes. |
| **Parent-relative (native)** | Adjacent bones in a participant’s native hierarchy. **Not** identical to the canonical 18-link set for all participants. |
| **Global / laboratory orientation** | Motive root/pelvis orientation in the capture volume. **Not in the 18-link state.** |
| **Internal articulated configuration** | The 18-link relative-orientation vector at one frame. Independent of facing and of where the dancer stands. |

### Root / global-orientation decision

**Primary: omit laboratory root orientation.**

Evidence:
- [`configs/canonical_links_18.yaml`](../../configs/canonical_links_18.yaml): pelvis is the **parent** of three links (`pelvis_to_Ab`, `pelvis_to_LThigh`, `pelvis_to_RThigh`), not a 19th orientation channel.
- [`src/gaga_shared6d/rotations.py`](../../src/gaga_shared6d/rotations.py): relative quaternion removes parent global pose.
- The scientific question is coordination of the body, not compass heading. Including yaw would treat a turn-in-place as a large configuration change even if joint angles were unchanged.

**Loss:** recurring **facing/turning** patterns are invisible. That is acceptable for the primary claim and must be stated.

**Not in Stage A–B.** A later optional sensitivity would require Motive global pelvis quaternions (not in `rotvec_18link`). Do not add that path unless a separate, written question about facing is authorized after B.

### Permitted claim

> **Scale-relative** recurrence density and/or deterministic organization of revisits in **internal endpoint-relative joint-configuration space** changed across T1, T2, and T3 in these four dancers (descriptive).

Do not write “absolute recurrence” or “recurrence within a shared angular radius” for the primary RR. A later T1-frozen absolute-ε analysis would answer a different question (fixed-radian neighborhood density) and is **out of A–B scope**.

The phrase “recurrence of whole-body coordination patterns” is allowed **only** as a gloss of RR and diagonal measures in that space, and only after that definition is stated.

### Forbidden claims

- discrete motif vocabulary or named motor programs;
- causal effect of Gaga training;
- cohort-level confirmation from N = 4;
- posture/facing/location recurrence;
- absolute (fixed-ε) recurrence from the primary mean-rescaled RR;
- any claim from regional speed RQA that is worded as configuration recurrence.

### Statistical unit

**Participant.** Frames, exercises, repetitions, and metrics are not independent participants. No cohort p-values are required or licensed by this plan.

---

## 2. Canonical representation (A0 re-verifies T1 only)

A0 must re-emit these facts from **T1 movement data** plus YAML/code. Planning-time scans of T2/T3 rotvec content are **not** A0 evidence and must not be repeated in A0 reports.

| Fact | Source A0 must use |
|---|---|
| 18 links, YAML order | `canonical_links_18.yaml` vs `load_link_config()` |
| Endpoint-relative, not uniformly native parent–child | YAML `spans`; `rotations.py`; T1 `skeleton_variant` in `recording_registry.csv` (T1 rows only) |
| Global translation and root orientation removed | relative quaternion; pelvis is parent, not a 19th channel |
| Stored as filtered rotvec radians `(T, 18, 3)` | parquet columns; `load_rotvec` |
| Six regions | YAML `regions` + per-link `region` |
| Historical regional Auto-RQA uses five regions | `pilot.yaml` omits `head_neck` |
| Filter / rate | `experiment.yaml`: 10 Hz, order 4, 120 Hz |
| T1 missingness, runs, near-π, jumps, durations | **T1 slices only** |

**T1 template note (metadata, not a T2/T3 movement result):** registry T1 rows list 651/671 as `51bone_basic` and 252/790 as `55bone_extended`. Canonical 18-link IDs are shared; spanning composition of `Ab_to_Chest` / `Neck_to_Head` differs by template. A0 reports T1 variants only. Longitudinal template change after T1 is a **Stage B caveat** already documented in the feature audit; A0 must not load T2/T3 rotvecs to re-demonstrate it.

**Additional issue (raised here):** existing `truncate_to_length` is a **start crop**. Stage B must not reuse it as the matched-duration primary. A new centre-crop helper belongs in B, not A0.

---

## 3. Data flow

```text
rotvec_18link parquet  →  slice one exercise  →  (T, 18, 3) state
        →  region-balanced mean SO(3) geodesic distance matrix
        →  Theiler (physical time)  →  ε = radius_frac × mean finite distance
        →  RP  →  quantify_rp  →  per-cell metrics
        →  (after lock + Stage B) equal-weight pool ex09–13 at metric level
        →  mean(R1, R2)  →  signed ΔT vs Drep
```

Hard boundaries: no concatenation of exercises, repetitions, or time points; no delay embedding; no pooling of frames.

---

## 4. Chosen state, distance, weighting, embedding

### State (retain)

Canonical 18-link endpoint-relative orientations at each frame. No positions, no angular-velocity augmentation, no PCA, no extra 54×m delay embedding.

**Why not pose+velocity:** that mixes configuration with intensity and recreates the construct we are leaving. Defer unless A1 shows configuration-only diagonals cannot detect repeated trajectories (unexpected).

### Distance kernel (retain)

\[
d_{\ell}(i,j)=\operatorname{angle}\big(R_{\ell,i}^{-1} R_{\ell,j}\big)
\]

Primary aggregator is **not** the unweighted mean over 18 links (see next subsection).

Flattened Euclidean and sum of `‖Δrotvec‖` are **A1 concordance tools only**. They must not be the Stage B primary distance.

### Anatomical weighting (changed)

Equal-link mean gives arms 8/18 = **44%** of the distance, trunk 2/18 ≈ 11%, head 2/18 ≈ 11%, each leg 3/18 ≈ 17%. That is an artifact of how many bones Motive tracks, not a statement that whole-body coordination is 44% arms.

**Primary distance (region-balanced):**

\[
d(i,j)=\frac{1}{6}\sum_{r=1}^{6}
\left(\frac{1}{|L_r|}\sum_{\ell\in L_r} d_{\ell}(i,j)\right)
\]

using all **six** canonical regions, including `head_neck`.

**Sensitivity:** equal-link mean \(d=\frac{1}{18}\sum_{\ell} d_{\ell}\).

**Interpretation rule if signs reverse:** the pooled whole-body direction is **anatomically unresolved** (`PARTIAL`). Report both. Do not pick the weighting that matches a preferred T2/T3 story.

No other project-supported biomechanical weights (e.g. inertia, segment length) exist in the frozen rotation pipeline. Do not invent them.

### Delay embedding (retain none)

Sale MdRQA: \(\mathbf{W}_t=[y_{1,t},\ldots,y_{N,t}]\); lagged coordinates are optional. The 18-link vector already is the configuration. Trajectory recurrence is read from **diagonal lines** (DET, Lmean), not from embedding past poses into the state.

Do not add delayed 54-D embeddings or snippet-windows unless A1 **fails** the exact-repeat vs shuffle tests — that would be a construct failure of pose-state MdRQA, not a license to complicate the state.

### Outcomes

| Role | Metrics | Notes |
|---|---|---|
| Primary density | `RR` | **Scale-relative** (mean-rescaled radius). Label outputs `RR_scale_relative` in reports. |
| Primary trajectory | `Lmean_s` (= Lmean frames / fps), supported by `DET` | Report both; do not average them into one score. |
| Required duration diagnostics | `Lmax_s`, `Lmax_over_N`, `duration_s`, `N` | Raw `Lmax` in frames is not a longitudinal DV. |
| Secondary | `LAM`, `TT`, `ENTR` | ENTR ≠ movement entropy. |

`lmin = 2` default. If **T1** median DET > 0.95, lock `lmin = 3` for **structure** metrics only (RR does not depend on `lmin`). Decision is T1-only.

---

## 5. Threshold calibration (T1 only)

Sale §2.5.2: constant ε as a fraction of mean pairwise distance; RR as DV; heuristic RR ~2–5%; mean rescaling \(d'_{ij}=d_{ij}/\bar{d}\) unless absolute scale is the target. Case studies sometimes keep a constant radius even if RR leaves that band, and require robustness across a small grid.

**Do not transfer `radius_frac = 0.35`.** That value was locked for regional **speed** Auto-RQA.

### Pre-declared target

- **Target:** median T1 RR = **0.03** (centre of 2–5%; matches this project’s existing `target_rr` convention without using target-RR as the primary DV).
- **Usable cell band:** every T1 calibration cell must have RR ∈ **[0.01, 0.10]** and finite DET (at least one diagonal line ≥ `lmin`).
- **Sparse:** RR < 0.01 or DET undefined → candidate **fails**.
- **Saturated:** RR > 0.10 → candidate **fails**. (The previous 0.20 cap is dropped; 0.10 is already above the paper heuristic.)

### Selection rule (not “smallest frac”)

Pre-specified grid: `{0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40}`.

1. Discard any `radius_frac` that fails the usable-band rule on **any** T1 calibration cell (4 participants × R1/R2 × ex09–13 = 40 cells), under the **primary** (region-balanced geodesic) distance and the candidate Theiler.
2. Among remaining values, choose the frac whose **median T1 RR is closest to 0.03**.
3. If two are equally close, choose the one with the **larger share of cells inside [0.02, 0.05]**, not the smaller frac.
4. Start with **one common** frac for all ex09–13.
5. Exercise-specific fracs are allowed **only if the common frac fails step 1**. Each exercise is then calibrated on its own 8 T1 cells with the same target/band.
6. Lock before any T2/T3 metric is computed.

Complementary **target-RR = 0.03** (ε as DV) is secondary for structure under matched density.

**T1-frozen absolute ε** would measure recurrence inside a **fixed-radian** neighborhood calibrated at T1. That is a different construct from primary scale-relative RR. It is **not in A–B**. If ever added after B, it must be labeled `RR_fixed_epsilon` and interpreted only with ROM/energy controls.

### What mean-rescaling does and does not invariant

Sale: \(d'_{ij}=d_{ij}/\bar{d}\); \(\epsilon = r \times \bar{d}\) is equivalent to thresholding rescaled distances at \(r\).

**Invariant (exactly):** any transformation that multiplies **all pairwise distances in that trial** by a positive constant (the mean cancels). Uniform Euclidean gain of an embedding is the textbook case.

**Not exactly invariant:** global ROM change in SO(3) (geodesics do not all scale by one factor except in the small-angle limit). Trial-to-trial changes in **shape** of the distance distribution. Therefore primary RR is **scale-relative density**, not “ROM-proof recurrence.”

**Not measured:** occupancy of a common absolute angular ball across time points.

Sensitivity after lock: locked frac ± one grid step, T1-locked, applied blindly to T2/T3.

---

## 6. Theiler selection (T1 only)

Do not copy speed-series AMI τ.

**Why Theiler is still required:** Sale §2.5.2: trivial temporal neighbours inflate auto-recurrence. The 10 Hz filter makes adjacent pose frames similar even without delay embedding. Candidates remain **0.15 s** and **0.30 s** at 120 Hz (18 vs 36 frames): 0.15 s is ~1.5 / cutoff; 0.30 s is more conservative. Neither is a paper-mandated number for this representation.

### Source of former numeric gates (not paper laws)

| Number | Source | Keep? |
|---|---|---|
| Median DET ≥ 0.95 as ceiling | Sale: \(l_{\min}=2\) can yield DET 95–100% and obscure variation. Also Stage 2 DET ~0.98. | **Keep as T1 trigger to raise `lmin` for structure metrics**, not as A2 FAIL by itself. |
| Shuffle DET drop ≥ 0.5 | Stage 2 `STAGE2_GATE.json` (`surrogate_ok` if median drop > 0.5), written when identity DET was ~0.98. **Not in Sale.** | **Reject as A2 absolute gate.** If pose DET is 0.4, a 0.5 drop is impossible even for a valid signal. |
| Theiler DET reduction ≥ 0.02 | Engineering. Not in Sale. | **Reject.** Too fine; would overfit T1 noise. |
| `Lmean_s` ≥ 0.05 s | Engineering (6 frames @ 120 Hz). Not in Sale. | **Reject as gate.** Replace with countable-line floor: median `Lmean_s` > `lmin / fps`. |

**Do not add** a large multi-surrogate null distribution for A2. One full time-shuffle per T1 cell is enough to test that identity DET exceeds shuffle DET. Extra shuffles would multiply cost without changing the A2 decision class.

### T1 decision rule (operational, documented)

1. For each Theiler candidate, apply §5 radius selection on T1 cells.
2. On identity vs **one** full time-shuffle per T1 cell: require median \(\mathrm{DET}_{id} > \mathrm{DET}_{shuf}\) and median relative drop \((\mathrm{DET}_{id}-\mathrm{DET}_{shuf})/\mathrm{DET}_{id} \ge 0.20\). Purpose: structure is not pure temporal adjacency. Limitation: 0.20 is operational, not a universal law; it is portable when DET is not near 1, unlike 0.5.
3. Prefer **0.15 s** if step 2 passes and median identity DET < 0.95.
4. Choose **0.30 s** only if median identity DET ≥ 0.95 at 0.15 s **and** 0.30 s has strictly lower median DET **and** median `Lmean_s` > `lmin/fps`.
5. If neither candidate passes step 2, **FAIL A2**. Do not inspect T2/T3.

A1 synthetic tests remain **directional** (exact-repeat vs shuffle), not these numeric bars.

---

## 7. Duration policy and matched-duration sensitivity

Pooling metrics across exercises **does not** remove duration bias. T1 already shows unequal lengths (A0 must report T1 duration range). Existing [`duration.truncate_to_length`](../../src/rqa_pilot/duration.py) keeps the **first** `n` samples — that is a start crop and is **not** the primary sensitivity.

| Metric | Duration sensitivity | Role |
|---|---|---|
| RR, DET, LAM | Proportions; relatively robust, not immune (longer trials sample more of the attractor) | Primary density / support |
| Lmean (frames) | **Not comparable** across unequal N | Do not use as DV |
| **Lmean_s** | Physical time; still slightly N-dependent | **Primary trajectory DV** |
| Lmax (frames) | Strongly N-dependent | Diagnostic only |
| **Lmax_over_N**, **Lmax_s** | Required diagnostics | Secondary |
| ENTR | Histogram of line lengths; N-sensitive | Exploratory |

### Required matched-duration rule (Stage B; not run in A0)

**Why centre crop, not start/end/multi-window as primary**

- Guided segments are short (about 6–18 s). Start and end are where cue onset, offset, and **segmentation-boundary error** concentrate (`experiment.yaml` notes exclusive-end convention at 1-frame ambiguity).
- Start-crop (Stage 1 default) systematically prefers the beginning of the exercise.
- End-crop systematically prefers the close.
- Multiple interior windows would better probe nonstationarity but triples compute and creates a new multiple-comparisons object. **Deferred** unless centre-crop reverses a reported contrast.

**Specification**

| Item | Rule |
|---|---|
| Grouping | `participant × exercise_id`, all available time points and repetitions in that group (up to 6 series: T1–T3 × R1–R2) |
| Common length | `n_keep = min_i n_frames_i` in the group (integer frames, no extra rounding) |
| Physical duration | `n_keep / 120` seconds — **the same frame count** at every T and R in the group |
| Location | **Centre crop:** `offset = (n_i - n_keep) // 2` (remainder of leftover frames on the end); slice `[offset : offset + n_keep]` |
| Recording | `crop_mode=centre`, `n_original`, `n_keep`, `offset`, original `start_frame`/`end_frame` |
| Start/end crops | Run **only if** a reported signed contrast reverses under centre crop, or if A0 shows T1 boundary invalid frames (`trimmed=True` at edges) |
| Claim rule | If centre-matched RR or `Lmean_s` **sign-reverses** a pooled contrast, the untruncated direction is **not reportable** for that contrast |

If sampling rate ever changes, convert Theiler, `Lmean_s`, and `Lmax_s` in **seconds**, not frames.

---

## 8. Missing-data and invalid-segment policy

Decided from T1/full-grid diagnostics **without using longitudinal RQA**. Interpolation is **not permitted** (Sale RR gap-sensitivity; project Layer-2 policy).

| Rule | Value |
|---|---|
| Interpolation | **Forbidden** |
| Frame validity | A frame is valid iff all 18 links are finite |
| Internal vs boundary gaps | Keep the **longest contiguous valid run**; if it is not the full slice, record `trimmed=True` |
| Maximum missingness | If valid-frame fraction < **0.95**, segment is `NOT_COMPUTABLE` |
| Minimum duration | Longest valid run ≥ **5.0 s** and ≥ **600** samples @ 120 Hz |
| Near-π / jumps | Do not drop; geodesic handles them. Flag cells with any angle > 0.95π or step > 1 rad |
| Primary vs sensitivity exclusions | **Same rule.** No post-hoc extra drops on T2/T3 |
| A0 claim | **T1 cells only.** Do not assert full-grid missingness from A0. |

---

## 9. Mixed-result interpretation (conservative)

Do **not** collapse RR, DET, and `Lmean_s` into a stereotypy score. DET and `Lmean_s` can disagree; report them separately.

| Pattern | Mathematical reading | Permitted wording | Too strong |
|---|---|---|---|
| RR↓, DET↑, Lmean_s↑ | Fewer recurrent pairs; a larger fraction of those pairs lie on longer diagonals | Fewer configuration revisits; remaining revisits form longer / more organized trajectories | “More stereotyped,” “more skilled,” “less creative,” “reduced repertoire” |
| RR↑, DET↓, Lmean_s↓ | More recurrent pairs; less diagonal organization | More configuration revisits without longer organized trajectories | “More random,” “more exploratory” as a value judgment |
| RR↓, DET↓, Lmean_s↓ | Fewer and less organized revisits | Reduced configuration recurrence and reduced trajectory organization | “Improved flexibility” |
| RR↑, DET↑, Lmean_s↑ | More and more organized revisits | Increased configuration recurrence and increased trajectory organization | “Better coordination” |
| RR↓, DET↑, Lmean_s↓ (or DET↓, Lmean_s↑) | Density and line statistics disagree | **Indeterminate trajectory organization**; report numbers, no directional trajectory claim | Any single narrative |
| R1-only vs R2-only ΔT disagree in sign | Repetition inconsistency | **Inconsistent across repetitions**; no pooled direction | Averaging away the disagreement |
| Exercises opposite signs | Heterogeneous tasks | Pooled Group4 direction **not interpretable**; use exercise-resolved | “Overall decrease/increase” |
| Weighting schemes opposite signs | Anatomical aggregator disagreement | **Anatomically unresolved** | Choosing one weighting after seeing T2/T3 |

---

## 10. Authorization gates

Stage A is **not** one implementation block. Each gate writes evidence + verdict; the next stage is unauthorized until PASS (PARTIAL only if the report names a non-blocking exception).

```text
A0 representation  →  A1 synthetic  →  A2 T1 calibrate  →  A3 lock hash
                                                              ↓
                                                    B T2/T3 full grid
```

**Structural (not honor-system) T2/T3 firewall:**
- A0–A3 scripts **must filter `timepoint == 1`** in code. They must not accept a timepoint CLI flag that includes 2 or 3.
- A3 writes `outputs/locks/parameter_lock_whole_body_pose.json` plus `sha256`.
- Stage B scripts **refuse to load T2/T3** unless that lock file exists and matches a committed schema (required keys listed in §16). No lock → exit nonzero.
- Do not implement B loaders in the A0–A1 commit set.

### A0 — representation and data integrity

**In:** T1-only `rotvec_18link` slices, `canonical_links_18.yaml`, `build_segment_index` filtered to `timepoint==1`, T1 rows of `recording_registry.csv`.  
**Out:** `outputs/whole_body/A0_representation_facts.json`, `reports/whole_body/A0_GATE.md`, `outputs/whole_body/A0_manifest.json`.  
**Forbidden:** RQA metrics; geodesic pairwise engine; T2/T3 rotvec loads; CLI flags that select timepoint 2 or 3.  
**File availability (no movement content):** existence of T1 parquet files is required. Existence of other recording parquet **paths** may be listed without opening arrays and without duration/angle summaries.  
**PASS:** YAML vs loader agreement; T1 40-cell grid present; T1 validity policy pass; representation matches §2.  
**FAIL:** link-order mismatch; unexpected endpoint-relative definitions; root not removed as assumed; T1 near-π or jumps judged unsafe for the intended geodesic (e.g. widespread wrapping); T1 missingness fragments segments; T1 cells absent or too short; six-region map ambiguous.  
**Stop:** no A1 until PASS.

### A1 — synthetic construct validity

**In:** geodesic + region-balanced implementation; existing `quantify_rp`.  
**Out:** `outputs/whole_body/A1_synthetic.json`, `reports/whole_body/A1_GATE.md`.  
**PASS:** all rows in §12 hold directionally; geodesic vs sum-link rotvec concordance high (median relative |Δd|/d < 0.05 and RR/DET rank correlation > 0.95 on synthetic + 2 real **T1** segments). Flatten Euclidean may fail; that is not an A1 FAIL.  
**PARTIAL:** concordance borderline but directions hold — A2 allowed only with geodesic frozen (no flatten).  
**FAIL:** shuffle does not drop DET/`Lmean_s`; exact-repeat does not raise them; region-only repeat looks like full-body repeat. **Do not start A2.**

### A2 — T1-only empirical compatibility and calibration

**In:** T1 R1/R2 only; start with 651 & 790 × ex11 & ex13 for runtime, then **all 40 T1 cells** for the actual radius/Theiler decision.  
**Out:** `outputs/whole_body/A2_t1_radius_theiler.csv`, runtime/memory log, `reports/whole_body/A2_GATE.md`. **No T2/T3 columns anywhere.**  
**PASS:** common (or justified exercise-specific) frac exists under §5; Theiler chosen under §6; peak RAM per cell < 0.5 GB; T1-grid runtime implies full 120-cell geodesic < 30 min without extra optimization.  
**FAIL:** no grid value satisfies §5; DET ceiling unfixable by Theiler/`lmin`; runtime > 2 h projected for 120 cells **and** simple vectorized geodesic already used. Optimizations (float32 cache, 60 Hz) only if this FAIL is runtime, and only after a written A2 addendum.  
**Stop:** no A3 lock until PASS.

### A3 — parameter lock

**In:** A2 tables only.  
**Out:** `outputs/locks/parameter_lock_whole_body_pose.json` (hashed).  
**PASS:** lock contains every required key (§16); no T2/T3 inputs.  
**Stop:** Stage B unauthorized until A3 PASS.

### B — longitudinal computation

**In:** lock + all 120 segments.  
**Out:** cell metrics, pooling, LOO, weighting sensitivity, truncation, reports.  
Unauthorized if lock missing.

---

## 11. Minimal files and code changes

Build only what the current gate needs. Do **not** add a parallel RQA engine.

### Reuse unchanged

- [`rqa_core.py`](../../src/rqa_pilot/rqa_core.py): `apply_theiler`, `threshold_from_mean_distance`, `threshold_for_target_rr`, `recurrence_matrix`, `quantify_rp`
- [`io_readonly.py`](../../src/rqa_pilot/io_readonly.py): `load_rotvec`, `load_link_config`, `build_segment_index`
- [`paths.py`](../../src/rqa_pilot/paths.py), [`duration.py`](../../src/rqa_pilot/duration.py)
- [`tests/test_rqa_core.py`](../../tests/test_rqa_core.py) as regression

### Do not reuse as primary

- `auto_rqa` / `delay_embed`
- `mdrqa_metrics` (Euclidean + target-RR only) — wrap or replace, do not call as-is
- `parameter_lock_stage1.json` numeric threshold/Theiler
- `make_surrogate` as-is (1-D). Add a **small** time-axis shuffle for `(T, 18, 3)` in the new module, not a second surrogate framework.

### New in A0 only (this implementation step)

| Path | Role |
|---|---|
| `scripts/20_wb_a0_verify.py` | T1-only representation/QC |
| `configs/whole_body_rqa.yaml` | A0 constants (timepoint 1, validity policy). **No numeric RQA lock.** |
| `tests/test_a0_t1_firewall.py` | Hard-coded T1; no T2/T3 CLI |

### New only after A0 PASS and A1 authorization

| Path | Role |
|---|---|
| `src/rqa_pilot/pose_distance.py` | Geodesic distance (not in A0) |
| `src/rqa_pilot/pose_mdrqa.py` | Pose MdRQA wrapper (not in A0) |
| `scripts/21_wb_a1_synthetic.py` | A1 |
| `tests/test_pose_distance.py` | Geometry / weighting |
| `tests/test_pose_mdrqa.py` | RR modes |

### New only after A1 PASS (A2–A3)

| Path | Role |
|---|---|
| `scripts/22_wb_a2_t1_calibrate.py` | Hard-coded `timepoint == 1` |
| `scripts/23_wb_a3_lock.py` | Writes lock from A2 outputs |

### New only after A3 PASS (B)

| Path | Role |
|---|---|
| `scripts/24_wb_b_full_grid.py` | Requires lock; then 120 cells |
| `scripts/25_wb_b_analyze.py` | R1/R2, ΔT, pool, LOO, truncation, weighting |
| `scripts/26_wb_b_reports.py` | Figures/tables/claim audit |

**Deferred / not built unless A2 runtime FAIL:** distance-matrix cache, float32, downsampling, chunking, sparse RP.

**Not in this project phase:** HMM/HSMM, CRQA(R1,R2), ex14–15, global-pelvis sensitivity, full regional Auto-RQA resweep.

Outputs live only under `outputs/whole_body/`, `reports/whole_body/`, and the new lock path. Do not modify Stage 1/2 CSVs.

---

## 12. Synthetic and empirical validation matrix

| Test | RR | DET | Lmean_s |
|---|---|---|---|
| Exact repeated whole-body trajectory | high | high | long |
| Same + small noise | high, mild drop | high, mild drop | long, mild drop |
| Same poses, time shuffled | can stay high | **collapse** | **collapse** |
| Same relative trajectory, scaled ROM (mean-rescaled ε) | relatively stable | relatively stable | relatively stable |
| Same, frozen absolute ε (A1 only, not a DV) | moves with scale | may move | may move |
| Only one region repeats | much lower than full-body control | much lower | shorter |
| Full-body pattern repeats | high | high | long |
| Geodesic vs sum-link rotvec | ranks agree | ranks agree | ranks agree |
| Flatten Euclidean vs geodesic | may disagree near π | — | — |
| Unstructured / time shuffle of real T1 | — | identity DET > shuffle and relative drop ≥ 0.20 (A2 operational) | Lmean_s drops |

Also: `test_rqa_core.py` still passes; no recurrence across exercise boundaries (distance uses one slice); pooling is metric-level only (unit test on a tiny fake table). Paper C++ backend parity is **not** required for geodesic (no equivalent). Optional flatten-Euclidean parity with the backend is A1-optional, not a gate.

---

## 13. Longitudinal and pooling logic (Stage B only)

Per cell: participant × T × R × exercise → metrics (region-balanced geodesic, locked params).

1. `R2 − R1` and `|R2 − R1|` at each T (repetition effect / Drep).
2. Equal-weight mean of ex09–13 **only if all five exercises are computable**; else pooled row = `NOT_COMPUTABLE`.
3. \(A_{p,t}=(P_{R1}+P_{R2})/2\).
4. Signed `T2−T1`, `T3−T1`, `T3−T2`.
5. Keep R1-only and R2-only ΔT.
6. Compare |ΔT| to Drep descriptively (exceed / within / inconsistent). Not a p-value license.
7. Exercise-resolved table always accompanies the pool.
8. Leave-one-exercise-out: if dropping one exercise flips the pooled sign, the pool is **driven by that exercise**.

ex14–ex15 remain excluded.

---

## 14. Sensitivity analyses (Stage B)

Required: equal-link vs region-balanced; locked radius ± one grid step; alternate Theiler; truncation; LOO; ROM / mean link speed / duration covariates reported beside RR (do not residualize post hoc to chase significance).

Companion regional Auto-RQA: **reuse existing cells** for intensity localization. Do not block B on a full regional resweep. Do not merge regional and whole-body scores.

Existing five-region **speed** MdRQA: historical secondary only.

HMM/HSMM: **later exploratory**, required only for a discrete-motif claim. Not a prerequisite for this RQA claim.

---

## 15. Reporting requirements

- Method schematic (internal configuration, geodesic, RP, metric-level pooling)
- T1 RR vs `radius_frac` (lock justification)
- Example identity vs shuffled RPs
- Per-participant pooled RR and `Lmean_s` at T1/T2/T3 with R1/R2
- Exercise-resolved signed-Δ heatmap
- LOO and weighting comparison
- Duration/truncation table
- Claim-boundary / mixed-result audit

Language in reports must use **internal articulated configuration** and **scale-relative RR**, not “posture recurrence” or “absolute recurrence.”

---

## 16. Computational benchmarks

Previous “~1 min full grid” is a **hypothesis**, not a fact. Rechecked sizes (2026-08-13):

- N = 720–2160 (not 2280); max float64 matrix ≈ **37 MB**
- Sum of N² × 8 bytes ≈ **1.5 GB** if all matrices were stored at once (they will not be)
- T1 max N = **1920** — sufficient for A2 runtime smoke

A2 must time geodesic + quantify on T1 cells at N ≈ 720, 1200, 1920 and extrapolate \(\sum N_i^2\).

**Optimization threshold:** add cache/float32/60 Hz **only if** projected 120-cell runtime > 30 min after vectorized geodesic. Do not pre-build them.

Keep 120 Hz unless A2 shows Theiler-uncontrolled oversampling **and** 60 Hz preserves `Lmean_s` ranks on T1.

---

## 17. Reproducibility

- Writes only under `rqa_guided_pilot/`
- Lock keys (minimum): `state`, `distance`, `weighting_primary`, `radius_frac` or `radius_frac_by_exercise`, `theiler_seconds`, `theiler_frames`, `lmin_rr`, `lmin_structure`, `rate_hz`, `target_median_rr`, `usable_rr_band`, `calibration_cells`, `no_delay_embedding`, `interpretation`, `forbid`, `lock_sha256_inputs`
- Manifest: git commit, script paths, input parquet hashes, lock hash
- Do not edit `parameter_lock_stage1.json`

---

## 18. Final PASS / PARTIAL / FAIL (scientific question)

**PASS:** A0–A3 passed; 120-cell geodesic grid complete; pooled + exercise-resolved + R1/R2; truncation does not reverse reported signs; weighting does not reverse reported signs; mixed-result language respected; claim inside §1.

**PARTIAL:** technically valid but inconsistent across repetitions, exercises, or weighting; or RR change tracks ROM/duration only; or incomplete grid.

**FAIL:** A-gate failure; concatenation; T2/T3 used in lock; interpolation; claims of motifs, causality, posture, or cohort confirmation.

---

## 19. What is ready now

| Stage | Ready to implement after this plan is accepted? |
|---|---|
| **A0** | Authorized — representation verification only (this step) |
| A1 | Only after A0 PASS **and** separate authorization |
| A2–A3 | Only after A1 PASS |
| B | Only after A3 lock |

A0 does **not** implement `pose_distance.py` / `pose_mdrqa.py`. Those wait for A1.

**Scientific blockers for B (not for writing A0):** none in the data (complete 120 finite segments). Remaining locks (`radius_frac`, Theiler, `lmin`) are **T1 empirical**, which is why they are A2–A3, not guessed here.

**Complexity:** A0 small; A1 small–moderate (distance + synthetic tests); A2–A3 moderate; B moderate given engine reuse, not a new RQA stack.
