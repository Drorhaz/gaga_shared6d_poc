<!-- ARCHIVE: first PRD as written 2026-09-25, before the CORE-cut and later restore. Working spec is PRD_THESIS_MOVEMENT_ANALYSIS.md. -->

# PRD: Thesis movement-analysis system (full cohort)

**Document type:** Product requirements + analysis-chapter specification  
**Audience:** An implementing agent that will create a **new standalone project**, using existing repos only as reference.  
**Success:** A documented pipeline whose outputs can be written, almost in order, as the thesis **Methods → Results → Discussion**, without inventing missing Takes or claiming a drug effect.  
**Status:** Locked scientific logic as of 2026-09-25. N is **not** locked. Data will grow (target on the order of 11 participants; analyse whoever is usable per cell).  
**Related reviews (read, do not copy as the product):**  
`docs/THESIS_ROADMAP_SHORT.md`, `docs/ASTRA_FABLE_11P_ROADMAP_ARCHIVE.md`, Motive export audit in prior chat, frozen 4-person JcvPCA in `gaga_jcvpca`.

---

## 0. What this product is

A **new analysis codebase + data layer + thesis-facing reports** that:

1. Ingests Motive solved-skeleton CSVs for **all available participants**, including incomplete people.
2. Applies **one** QC and feature pipeline.
3. Runs a **fixed sequence of analyses** that match a single scientific story.
4. Emits tables/figures whose captions are already the Results sentences.

It is **not** a continuation of `gaga_jcvpca` V1 (P1 Group4, 4 IDs hard-coded), **not** the Conv/transformer POC as the thesis engine, and **not** a kitchen sink of every method in the old repos.

**Reference-only projects** (read for parsers, JcvPCA math, RQA pilots, gap policy; re-implement cleanly):

| Path | Steal from | Do not inherit |
|---|---|---|
| `projects/gaga_jcvpca` | `parse_motive_take`, relative rotvec + Butterworth, JcvPCA, S2 vs R1/R2, marker gap policy, P1 segmentation | P1-only scope, 4-ID assumption, Group4 as the only window, causal-forbidden language is KEEP |
| `projects/gaga_shared6d_poc` | `motive_io`, `canonical_links_18.yaml`, `s2_extract.py`, header inventory, P2 probe | 6D/Conv/S6 transformer as primary results; hard-coded `participants: [252,651,671,790]` |
| `projects/3Layers_project` | Layer2 Global/Quaternion gates, Property=Rotation parser (safer than first-XYZW) | Dashboard / legacy naming |
| `Lab_Optitrack_protocol/` + `Gaga_task/` | What P1 vs P2 **mean** | — |

**New project name (suggested):** `gaga_thesis_movement` (sibling under `projects/`). One repo, one config, one `docs/METHODS.md` generated from this PRD.

---

## 1. Scientific story (this is also the Results/Discussion spine)

### 1.1 What the data *are*

Each visit, the dancer does **two different movement tasks** (usually twice: R1, R2):

| Token | Meaning in the room | What it measures |
|---|---|---|
| **P1** | One **cued video**: 17 spoken prompts (`ex01`–`ex17`), ~4 min | Behaviour **under instruction**. Inside P1 the brief **loosens**. |
| **P2** | **Free dance**, audio only, ~2 min (“take a track on your own…”) | Behaviour **with room to be oneself**. Not a phrase from the video. |
| **P3** | Rare, short, undocumented in the lab protocol | Out of scope until defined. Do not analyse as “more open.” |
| **T1, T2, T3** | Lab visits | T1 ≈ baseline; T2 ≈ **48 h after blinded dose** (and ~4 Gaga classes); T3 ≈ later (~10 classes). Calendar gaps differ by person — store **days**, do not pretend equal spacing. |
| **R1, R2** | Two takes **the same day** | Repeat of the **same task**, not a new timepoint. |

**Arms:** everyone does Gaga. Difference is **psilocybin vs active placebo** at one dosing visit. Control ≠ no training. Labels may arrive **after** movement analysis is frozen.

**P1 internal ladder (still one video):**

| Band ID | Exercises | Concept | Not |
|---|---|---|---|
| `P1_prescribed` | `ex01`–`ex12` | Tight cues (bend, arch, arms, waves, twist, rotations, distal curves…) | Free dance |
| `P1_guided_open` | `ex13`–`ex17` | Looser cues inside the class (whole-body curves, one-leg curves, shake, “keep dancing”) | P2 |
| `P2_free` | whole P2 take | Protocol free dance | A P1 exercise |

If `ex16`/`ex17` have unmarked ends, **`P1_guided_open` = `ex13`–`ex15`** until those rows exist. Never silently treat 13–17 as complete.

Old JcvPCA **Group4 (`ex09`–`ex13`)** is a *legacy committee window*. It is **not** the thesis primary. Optional appendix: robustness vs that frozen 4-person result.

### 1.2 What we want to know (order is mandatory)

**Q0 — Ladder (justifies where we look).**  
Does personal “handwriting” become more readable as the task opens?  
**Expect:** identity / separability  `P1_prescribed` < `P1_guided_open` < `P2_free`.  
This is **not** evidence of longitudinal change.

**Q1 — What changed in the open-ish behaviour?**  
After Q0, analyse **`P1_guided_open` and `P2_free` separately** (never one pile called “open”):

- **Within person:** T1 vs T2 vs T3 vs own same-day repeat.
- **Across people:** same direction vs each their own way.
- **Across time:** T2 (dose-proximal) vs T3 (training-proximal) **not collapsed**.

**Q2 — Did the two study arms differ?**  
Only on **person-level change scores already computed in Q1**, and only after labels. Honest sentence: Gaga+psilocybin vs Gaga+placebo.

**Q3 — What did the change look like?**  
Anatomy/coupling/recurrence **only** for people × windows that moved in Q1.

### 1.3 Method constraint that must not be violated

**JcvPCA requires comparable movement structure** (same kind of cued phrase).  
**Do not run JcvPCA on P2.** Free dance would collapse the shared subspace: “they danced a different dance” ≠ “coordination reweighted.”

| Window | Change / structure methods | Forbidden |
|---|---|---|
| `P1_prescribed` | Signature (Q0); optional control Δ; **not** the place we hunt “expressiveness change” | Treating it as free |
| `P1_guided_open` | **JcvPCA** (primary change), coupling, energy as covariate, phrase shape optional | Calling it P2 |
| `P2_free` | **RQA** (primary), energy/speed, coupling, optional facing/travel; transformer **only** as a labelled appendix | **JcvPCA**, Conv-6D as a finding |

---

## 2. Data contract (usable vs drop)

### 2.1 Session identity

Canonical key:

```text
{pid}_T{t}_P{part}_R{rep}
```

Example: `671_T2_P2_R1` = participant 671, visit 2, **free dance**, first take that day.

Discovery **must not** rely on globbing filenames alone. Build a **header-keyed manifest**. Parse pid/T/P/R from filename **and** Motive `Take Name`. Record original path and `Capture Start Time` (never filename date).

### 2.2 Motive CSV — required header (gate)

Include as a **skeleton analysis take** only if **all** hold:

| Field | Required | Else |
|---|---|---|
| Format | record (expect 1.25) | warn, do not fail unless unreadable |
| `Rotation Type` | `Quaternion` | **drop** (Euler/XYZ marker dumps) |
| `Coordinate Space` | `Global` | **drop** |
| `Capture Frame Rate` = `Export Frame Rate` | `120` | **drop** (do not analyse downsampled) |
| `Length Units` | `Millimeters` preferred | **Meters allowed for rotations**; flag; convert positions in code; re-export mm when possible |
| Type row | has `Bone` columns | **drop** marker-only / `Rotation Type=XYZ` siblings |
| Layout | Rotation XYZW **before** Position per bone **or** parse by `Property=Rotation` | Prefer Property-row parser (Layer2). First-XYZW heuristic is unsafe |
| Data `Frame` | starts at 0, contiguous | segmentation uses **this** index, not `Capture Start Frame` |
| Length | ≥ 60 s of exported frames | **drop** aborted 5–7 frame files; log collision with the real take |

**Export recipe for all future Takes (do not vary):** Global, Quaternion, 120=120, Millimetres, bones + **labelled** markers, unlabelled **off**, Rotation then Position, Frame from 0, **no** Motive extra filter/downsample, **no** local/relative export (relative is computed in Python).

Keep CSV as **raw source**. Do not treat 6D or rotvec parquet as raw.

### 2.3 Derived kinematics (single core object)

```text
Motive global bone quaternions
  → q_rel = inv(q_parent) * q_child   on 18 canonical endpoint links
  → sign continuity
  → rotvec (radians)
  → Butterworth 10 Hz, order 4, zero-phase, fs = 120
  → NaN if quat invalid or run too short to filter
```

18 links: copy `gaga_shared6d_poc/configs/canonical_links_18.yaml` (pelvis–Ab/thighs, Ab–Chest, neck–head, both arms, both legs).  
51- vs 55-bone templates: same 18 **labels**; `Ab_to_Chest` and `Neck_to_Head` **span different solver bones** when the template changes **within person** (seen: 651 T1→T2, 671 T1/T2→T3). **Flag those two links**; every longitudinal table has a with/without column.

**6D** = first two columns of the rotation matrix **after** the above. Implementation detail for any optional model. **Not a second scientific representation.**

**Facing/travel (P2 only, separate namespace):** root yaw rate, horizontal speed, floor area — from root position/orientation; convert mm vs m from **header**. Never mix into JcvPCA features.

**Markers:** QC / gap policy only. Not JcvPCA/RQA state.

### 2.4 Segmentation

- **P1:** workbook `{pid}_ex_segmentatios_frames.xlsx` (or successor). `exercise_id` 1–17 → `ex01`–`ex17`. Frames = exported Frame. Exclusive end-frame convention: document and normalise.
- **P2:** **no exercise cuts.** One span = whole take after dropping T-pose seconds if logged; otherwise full exported length minus a documented edge trim (e.g. first/last 1 s) applied to **all** P2 equally.
- Missing P1 sheet → that person cannot enter `P1_*` bands. They **can** still enter `P2_free` if the CSV exists.

### 2.5 Complete-case **per cell**

A **cell** = `(participant, timepoint, repetition, band, link?)`.

- Missing visit → no row. Do not impute.
- Missing R2 → no same-day spread; either exclude from “exceeds own repeat” or mark **single-take descriptive**.
- No T1 → **cannot** enter longitudinal change (inventory only).
- Dirty link → drop **that link**, keep others.
- N is reported **per contrast**, never a fake “N = 11.”

When new CSVs arrive: re-run manifest → QC → features → only later stages for **new cells**. Do not wait for a perfect roster.

### 2.6 Eligibility matrix (agent must implement as a table)

| Analysis | Needs | Typical blockers |
|---|---|---|
| Manifest / QC | Any quaternion skeleton CSV ≥ 60 s | Marker-only copy, aborted take |
| Q0 signature `P1_prescribed` | P1 CSV + segmentation ex01–12 | No P1 sheet |
| Q0 signature `P1_guided_open` | P1 + segs for 13–15 (16–17 if present) | Unmarked 16–17 → use 13–15 |
| Q0 signature `P2_free` | P2 CSV | 790 historically P1-only until exported |
| Q1 JcvPCA change | `P1_guided_open` at T1 and Tk, preferably R1 and R2 at T1 | Template change on two links |
| Q1 RQA change | `P2_free` at T1 and Tk, finite windows | No P2; too short |
| Q2 arm test | Person-level Q1 scores + **arm label** + pre-registered contrast | Labels missing → freeze plan only |
| Facing/travel | P2 + root position in CSV | Positions in mixed units — convert |

---

## 3. QC (drop noise; keep missingness visible)

Run in this order. Every exclusion writes one line to `qc_exclusions.csv` (`cell`, `reason`, `rule_id`).

1. **File/header gate** (§2.2).  
2. **Duplicate md5 / identical `.tak` across pids** (known issue: 505 vs 621 T2 byte-identical on disk historically) → **block both T2 until resolved**; do not analyse a shared take as two people.  
3. **Frame-count gate** ≥ 60 s.  
4. **Skeleton:** bone tokens for 18 links resolvable; else fail that take.  
5. **Units:** millimetres vs metres recorded; rotations used as-is; positions converted.  
6. **Marker gap policy** (re-port from `gaga_jcvpca`): high gap % on a region → exclude those **links** from JcvPCA, not the whole person if other links are clean.  
7. **Finite rotvec:** 2 s windows (240 frames @ 120 Hz) require all-finite samples; incomplete windows dropped, not interpolated.  
8. **No Motive-spline interpretation:** if bones look continuous and markers gap, **trust markers for QC**; do not treat filled bones as observed.  
9. **Forbidden operations:** interpolate missing visits; copy R1→R2; zeros for empty; mix Euler export into quat parser.

QC is part of Methods. The exclusion table is a Results appendix.

---

## 4. Analysis roadmap (implement as stages; each stage has inputs, outputs, pass/fail)

Do not skip Q0 to “get to change.” Do not unblind before Stage Q2 plan freeze.

### Stage 0 — Ingest

**In:** folder of CSVs + segmentation xlsx + optional arm file (sealed).  
**Out:** `manifest.csv`, `timing.csv` (capture clock, days since T1, days since dose **when known**), `template.csv` (n bones, root name).  
**Pass:** every file classified include/drop with reason.

### Stage Q0 — Signature ladder

**Question:** is the person more readable as the task opens?  
**Data:** 2 s hop-1 s **time-mean** 54-D rotvec windows, **within band** (do not pool 01–12 with P2).  
**Method:** nearest centroid or equivalent, leave-one-recording-out **and** same-day R1↔R2. Chance = 1/n people in that fold.  
**Metric:** accuracy or balanced accuracy per band.  
**Expect:** `P1_prescribed` < `P1_guided_open` < `P2_free`.  
**Thesis use:** Methods + early Results. **Discussion:** supports looking at 13–17 and P2 for *change*.  
**Not:** proof of T1–T3 change; not an arm test.  
**Note:** first-visit P2 may be weak (lab familiarisation). Report T1 vs later ID separately.

### Stage Q1a — Guided-open change (`P1_guided_open` only)

**Question:** did coordination **contribution structure** reorganise in the looser cued phrases?  
**Method:** reference-anchored **JcvPCA** as in `gaga_jcvpca` (T1 reference; prefer **T1 R2** as primary, T1 R1 sensitivity). Compare T2/T3. Same-day T1 R1↔R2 = **uncertainty / S2-style exceed**, not a universal noise floor for between-day mean posture.  
**Units of result:** per person × contrast × link signed contribution change; count of links exceeding own repeat **with direction stability**.  
**Across people:** side-by-side; **no** pooled t-test on links.  
**Template sensitivity:** drop `Ab_to_Chest`, `Neck_to_Head` and repeat for people whose bone count changed.

### Stage Q1b — Free-dance change (`P2_free` only)

**Question:** did the **temporal organisation** of free dancing change (more/less recurrent, stuck, fluid)?  
**Method:** **RQA** (or MdRQA) on a **pre-registered scalar or low-dim state** derived from the 18-link rotvecs (e.g. whole-body mean \|ω\| or a locked regional mean). Parameters (embedding, delay, threshold rule) **frozen on T1** (or T1 R2), applied blindly to T2/T3.  
**Same-day R1/R2:** spread of RQA metrics = uncertainty.  
**Optional same cells:** energy (mean speed), coupling (link–link correlation distance), facing/travel.  
**Optional appendix:** sequence model / transformer — only if documented as **non-interpretable check**, trained with leakage rules (no T2/T3 in representation search). Not required for a passable thesis.

### Stage Q1c — Within-day extra-openness (DID)

**Question:** did they change **more** in the freer window than in the tight script?  
Two DID scalars, **never mixed**:

- `DID_guided = Δ(P1_guided_open) − Δ(P1_prescribed)` using JcvPCA (or the same scalar family on both P1 bands).  
- `DID_free` is **not** JcvPCA(P2)−JcvPCA(P1). P2 Δ comes from **RQA/energy family**. If scales differ, report **standardised-within-person** z vs own R1/R2 spread, then subtract. If that still apples-to-oranges, report **two columns** (guided Δ, free Δ) and do not force one DID.

**Discussion line:** extra change where there is more room to interpret, after a same-day script control.

### Stage Q1d — Cloud (descriptive)

At each T, pairwise distances **within band** in the Q0 feature space **or** in JcvPCA/RQA summary space. Ask: closer or farther? **No p-value.** Shared Gaga can shrink a cloud.

### Stage Q2 — Arms (gated)

**In:** person-level table from Q1 (one primary pre-registered number).  
**Primary (lock before labels):** e.g. `DID_guided` T1→T2 **or** P2 RQA Δ T1→T2 — **choose one** in a one-page freeze file. Recommended default: **P2 RQA Δ T1→T2** if most people have P2; else **JcvPCA S2 count on guided-open T1→T2**.  
**Test:** exact permutation of arm labels on person scores. Also: k-of-n per arm exceeding own repeat spread.  
**If n/arm < 3** on that cell: table only.  
**Language:** see §7.

### Stage Q3 — Look (gated)

Only cells with Q1 movement:

- JcvPCA **body maps** (guided-open).  
- Coupling pairs on P2 **or** guided-open (pre-specify).  
- RQA metric named in plain language (more recurrent / less).  
- Energy as covariate (amplitude vs organisation).  
**Pick RQA *or* motifs, not both plus Conv plus entropy as co-primaries.**

---

## 5. What each result *means* (for Discussion)

| Finding | Allowed interpretation | Forbidden |
|---|---|---|
| ID ladder holds | Person is more in the kinematics when the brief is looser / free | They “improved”; they “became more creative”; they changed over weeks |
| JcvPCA S2 on 13–17 | That person’s **cued coordination contribution** reweighted beyond a second take of T1 | Gaga caused it; DOF “unlocked”; anatomical flexion |
| RQA Δ on P2 | Free-dance **temporal structure** (recurrence/stickiness) differed across visits | Same as JcvPCA; “they improvised better” |
| DID_guided > 0 | More reorganisation in looser cues than tight cues **same person** | P2 result |
| Arms differ on frozen score | Two Gaga groups differed on that score after dosing window | Psilocybin caused dancing change; control was untreated |
| Cloud shrinks | People more similar in that space that day | Learning or drug |
| ID high, JcvPCA/RQA flat | Still the same person; coordination not reweighted / recurrence not shifted | Contradiction of Q0 |

T1 P2 may be a **familiarisation** take. Prefer T1 R2; discuss first free dance in the lab as a limitation.

---

## 6. Thesis chapter mapping (agent: generate report stubs with these headings)

**Methods**

1. Participants and missingness (N per cell, not N=11).  
2. Tasks: P1 ladder, P2 free dance.  
3. Capture and export.  
4. Representation (parent-relative rotvec; why not global; why not JcvPCA on P2).  
5. QC.  
6. Q0–Q3 analyses and pre-registration of Q2.

**Results** (same order)

1. Coverage and QC.  
2. Q0 ladder.  
3. Q1a guided-open JcvPCA (within person, then across).  
4. Q1b P2 RQA (within, across).  
5. Q1c DID / two-column change.  
6. Q1d cloud (short).  
7. Q2 arms **or** “plan frozen, labels not in this chapter.”  
8. Q3 maps for movers.

**Discussion**

1. Handwriting vs change.  
2. Script vs free: two estimands.  
3. Person-specific vs common direction.  
4. T2 vs T3 timing (dose-proximal vs training).  
5. Arms: modest, shared Gaga.  
6. Limits: 2 repeats, template change, incomplete cells, T1 familiarisation, no JcvPCA on P2.

---

## 7. Forbidden claims (encode as lint in report generator)

- Psilocybin or Gaga **caused** the kinematics.  
- Control = no Gaga.  
- P1 `ex13`–`ex17` = free dance.  
- JcvPCA on P2.  
- 6D = raw Motive.  
- R2 is a timepoint.  
- Person-ID = longitudinal change.  
- Mean-posture day distance > R1/R2 ⇒ “real change.”  
- Group-mean pose, imputed visits, p-values while blinded.  
- Anatomical flexion/abduction from relative rotvecs.  
- “N = 11” without a cell table.

---

## 8. Implementation requirements for the new project

### 8.1 Layout (suggested)

```text
gaga_thesis_movement/
  README.md                 # points at this PRD
  docs/
    METHODS.md              # generated from stages
    PRE_REGISTER_Q2.md      # one page, dated, before labels
  configs/
    export_gate.yaml
    canonical_links_18.yaml
    bands.yaml              # prescribed / guided_open / p2
    rqa.yaml                # frozen params
    jcvpca.yaml
  src/...                   # ingest, qc, features, q0, q1a, q1b, q2, q3
  data/
    raw_csv/                # immutable CSVs
    segmentation/
    manifest/               # generated
  outputs/
    qc/
    q0_signature/
    q1_guided_jcvpca/
    q1_p2_rqa/
    q2_arms/                # empty until unblind
    thesis_figures/
  tests/                    # header gate, no JcvPCA-on-P2, band definitions
```

### 8.2 Agent build rules

- Discover participants from the **manifest**, not a 4-ID list.  
- Parse bones by **Property=Rotation** (or equivalent), not “first XYZW.”  
- Config-driven bands; default `guided_open: [13,14,15,16,17]` with auto-fallback to `[13,14,15]` if 16/17 missing.  
- Every method writes `n_included` / `n_excluded`.  
- Re-use math from old repos via **copied, cited functions**, not by importing `gaga_jcvpca` as a silent dependency (optional: git submodule only if versions pinned).  
- Do not implement Motive export. Do not train transformers unless `configs/extras.yaml` enables the appendix.  
- Golden test: one known take (e.g. `790_T1_P1_R1`) quaternion path matches `s2_extract` bit-close on rotvec.

### 8.3 First-week build order

1. Manifest + header QC + 18-link extract (P1 and P2).  
2. Q0 signature three bands.  
3. JcvPCA on `P1_guided_open` only.  
4. RQA on `P2_free` only.  
5. Thesis figure templates and METHODS stubs.  
6. Q2 freeze file (empty results).  
7. Plug in new CSVs as they arrive.

---

## 9. Open items (do not block Stages 0–Q1)

- Arm labels and unblinding SOP.  
- Dosing dates / class attendance (timing covariates).  
- 505/621 shared T2 takes — resolve before those cells enter Q1.  
- What P3 is.  
- Whether 008/050 ever get movement files.  
- Re-export 252 T3 to millimetres (rotations already usable).

---

## 10. Acceptance (product is done when)

- [ ] An agent can clone the new repo, point it at a CSV folder, and produce Q0 + Q1a + Q1b without editing participant lists.  
- [ ] JcvPCA cannot be pointed at P2 without an explicit hard error.  
- [ ] `P1_guided_open` and `P2_free` never share an output table without a `band` column.  
- [ ] QC exclusions are complete for every dropped cell.  
- [ ] METHODS.md matches this story; Results folders map to §6.  
- [ ] Discussion-forbidden strings are listed in `docs/FORBIDDEN.md` and used in caption checks.

This PRD **is** the analysis chapter’s logic. Code implements it. New data only **fills cells**; it does not change the questions.
