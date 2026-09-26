# PRD: Thesis movement-analysis system

**Audience:** Agent building a **new** repo (`gaga_thesis_movement`). Old projects = reference only.  
**N:** not locked. Complete-case **per cell**. New Takes fill cells; they do not change the questions.  
**Contribution:** not a new algorithm. A **validation + analysis framework**: (1) what data are comparable; (2) where person-specific kinematics are more classifiable as constraints relax; (3) whether organisation in those windows changes over T1–T2–T3 beyond that person’s same-day repeat; (4) *what* changed, with a method that fits the task.

**Thesis vs PhD:** this thesis is the **movement-measurement layer**. The PhD later adds imaging, questionnaires, creativity, MDI/MSE, larger N, and arm inference. This thesis does **not** claim plasticity, REBUS, a drug effect, learning, or creativity.

**Reference-only:** `gaga_jcvpca`, `gaga_shared6d_poc`, `3Layers_project` (Property=Rotation), `Lab_Optitrack_protocol`, `Gaga_task`. Do not inherit 4-ID lists, Group4-as-only-window, Conv/transformer-as-engine.

---

## Core thesis logic

**Who is this person → is that signature more detectable when the task is less constrained → did organisation in those windows change over time (vs own R1/R2; shared or person-specific) → what changed (links vs recurrence).**

Q0 is **not** longitudinal change and **not** validation of JcvPCA/RQA. Q1a/Q1b **are** the change tests. Do **not** insert a third primary method whose features are the same time-mean rotvecs as Q0: that quantity is already known to make day gaps look larger than R1/R2 because **mean configuration** moves. “Did it change?” is answered by Q1a exceed-vs-repeat and Q1b Δ-vs-repeat, not by a new timepoint classifier.

**Scientific completeness (lock):** coverage/QC + **segmented** Q0 + Q1a + Q1b, with R1/R2 where the cell exists. Missing DID, cloud, Q2, energy, dimensionality, or entropy does **not** make the thesis incomplete.

---

## Scope

| Layer | Analyses | Required for thesis success? |
|---|---|---|
| **CORE** | Coverage matrix (`pid × T × P × R`); export/QC/missingness; **segmentation contract**; **Q0** matched, **equal-duration** ladder (nearest centroid); **Q1a** JcvPCA on segmented `P1_guided_open`; **Q1b** one frozen RQA on a **pre-registered P2 usable interval**; R1/R2 as person-level uncertainty; four CORE figures | **Yes** |
| **HIGH-VALUE SECONDARY** | Energy (time-normalised mean \|ω\|) as amplitude **covariate** for Q1; Q0 resample-range if longer bands were subsampled | No, but run in week 1 if CORE is on track |
| **SECONDARY (cheap; not this week unless leftover)** | DID_guided; descriptive cloud; template sensitivity; Q1a on prescribed **only** as DID input | No |
| **FUTURE** | Q2; P2-vs-P1 two-column DID; coupling; extra RQA; entropy/MSE; participation ratio / effective dimensionality; SVM/RF/XGBoost ID models; HMM; transformers; motifs; facing/travel; P3; coarse T-classifier on time-mean features | No |
| **Out / REJECT** | JcvPCA on P2; RQA on guided-open as a second CORE; ordinary PCA as a second primary; treating Q0 as change; duration or window-count as a feature; windows that cross exercises or include pre-task stance; mixing Measurement/Entertainment exports; drug/plasticity/creativity claims | Never |

---

## 1. What the data are

| Token | In the room | Construct |
|---|---|---|
| **P1** | Cued video ~4 min, `ex01`–`ex17` | Instruction. Constraint **loosens** inside the video. **Not** homogeneous movement from file start to file end. |
| **P2** | Free dance, audio, ~2 min | Room to be oneself. **Not** a P1 exercise. No exercise grid. |
| **P3** | Undefined in lab protocol | Out of scope. |
| **T1 T2 T3** | Visits | T1 baseline; T2 ~48 h post dose; T3 later. Store **days**. |
| **R1 R2** | Same-day repeats | Same task again. **Not** a new timepoint. |
| **Arms** | Everyone does Gaga | Psilocybin vs active placebo. Control ≠ no training. |

**Constraint ladder (never one pile called “open”):**

| Band | Content | Constraint |
|---|---|---|
| `P1_prescribed` | Valid **ex01–ex12** segments only | Tight cues |
| `P1_guided_open` | Valid **ex13–ex17** (fallback **ex13–ex15**) segments only | Looser cues, still instructed |
| `P2_free` | Pre-registered **usable interval** of the P2 take | Free dance |

Bands are **unequal in duration** by design. Duration is **not** a scientific feature. Legacy Group4 is not primary.

**Key:** `{pid}_T{t}_P{part}_R{rep}` from **Take Name + headers**. Clock = `Capture Start Time`. Pid may be **3 or 4 digits**.

---

## 2. Segmentation and observation budget (mandatory)

Analyses run on **task performance**, not on the raw CSV span.

### P1

- Use the validated exercise segmentation workbook (exported Frame, exclusive-end convention documented).  
- **No window may cross an exercise boundary.**  
- Band concatenations use **only** frames inside the listed exercises. Drop wait / transition / post-hold **outside** those segments.  
- **Never** treat the full P1 take as one homogeneous series.  
- Do **not** segment Takes that fail the export gate or that cannot enter Q0/Q1a.

### P2

- No exercise grid. **Before any T1/T2/T3 comparison**, freeze one usable-interval rule (write it in `PRE_REGISTER_P2_INTERVAL.md`).  
- Default: identical edge trim for **all** pid/T/R (e.g. drop first and last 5 s), or keep a fixed interior duration if the take is long enough.  
- If a static/low-motion detector is used, freeze its threshold on **T1 only** (or on duration metadata only). **Do not** retune trim on T2/T3 to enlarge an effect.  
- Inspect (once) whether P2 starts/ends in stance; that inspection may justify the frozen trim; it may not become per-visit art.

### Windows

- Start and end inside a valid segment / P2 interval.  
- Record `source_frames` for every window.  
- Same sampling rate everywhere (120 Hz after ingest).  

### Equal observation budget (cross-band and, where claimed, cross-T)

Primary **Q0** ladder:

1. **Matched cohort:** same participants in all three bands.  
2. **Equal duration per person × band** in the analysed set (same total seconds, hence same window *n* after a locked hop).  
3. Longer bands: **repeated subsample** of contiguous or randomly placed blocks of that duration (pre-register count, e.g. 20). Headline = median accuracy across resamples; report IQR. Do not pick the resample that looks nicest.  
4. Do **not** compare accuracy, covariance eigenspectra, entropy, RR/DET, or “number of states” across bands on unequal seconds.

Q1a uses only guided-open segments (already a matched task). Q1b uses the frozen P2 interval; if intervals differ in length across T, **truncate to the minimum usable length for that person** (or a global cap) **before** RQA; do not let longer T3 inflate recurrence statistics.

---

## 3. Usable data × method

| Analysis | Needs | Hard reject |
|---|---|---|
| Any kinematics | Global + Quaternion + 120=120, Bone columns, ≥60 s **file**; Property=Rotation | Euler; marker-only; Local export; downsample; Entertainment mixed with Measurement |
| Coverage | Manifest cell even if missing | Imputing a cell |
| Q0 primary | Segmented bands; matched pids; **equal duration**; LORO | Mixing bands; same-recording train/test; unmatched N; duration as a feature |
| Q1a | Segmented `P1_guided_open` + T1 + later T | P2; no T1; windows across exercises |
| Q1b | Frozen P2 interval + T1 + later T | JcvPCA on P2; trim tuned on later T |
| Markers | Gap QC → drop **links** | Gaps as bone truth |
| Energy (secondary) | Same rotvec stream, time-normalised | Substituting energy for Q1 |

**Kinematics:** global quat → `q_rel = inv(q_parent)*q_child` on 18 links → rotvec → Butterworth 10 Hz, order 4, fs=120. NaN kept. Parse **Property=Rotation**. 6D is wrapping after this.

**Export lock:** World ON / Global, **one** Axis Convention for the whole analysis corpus (this project’s golden is Measurement / pelvis height on **Z** — do not mix with older Y-up CSVs), Quaternion, 120=120, mm, labelled markers on, unlabeled off, Rotation then Position, Frame from 0, no Motive filter, no Local relative export.

**Cells:** `(participant, timepoint, repetition, band [, link])`. No impute. No T1 → no Q1. Missing R2 → no “exceed own repeat.” N **per contrast**.

**Template:** log bone count (25 without fingers / 51 / 55). Flag `Ab_to_Chest`, `Neck_to_Head` when the chain set changes within person. Sensitivity reruns are secondary.

---

## 4. Stage 1 — Coverage (CORE, first deliverable)

`outputs/qc/coverage_matrix.csv` at `pid × T × P × R`:

file exists; export gate pass/fail; duration; bone count; 18 links; marker-gap summary; P1 segmentation available/incomplete/missing; P2 usable interval (s); R1/R2; T coverage; usable_Q0; usable_Q1a; usable_Q1b; exclude_reason.

**N is this table.** Do not quote “N=11.” Only segment P1 files that can enter CORE. Figure 1 = this matrix.

---

## 5. Analyses

### Q0 — Individuality × constraint (CORE)

**Question:** Is out-of-sample **person identification** stronger as the task is less constrained?  
**Expect:** `P1_prescribed` < `P1_guided_open` < `P2_free` (or report a failure of that order).

**Features:** 2 s, hop 1 s, time-mean 54-D rotvec, **inside segmented band**, equal-duration primary set as §2.

| Protocol | Role |
|---|---|
| **Primary model:** nearest centroid + standardise | Interpretable; one model |
| **Primary split:** leave-one-**recording**-out within band | Not window i.i.d. |
| **Control:** same-day R1↔R2 | Upper bound (shared suit) |
| **Not CORE:** SVM, RF, XGBoost, nested model search | RDF; “highest accuracy” is not the question |

If a linear logistic regression is implemented in leftover hours, it is a **robustness check**, same splits as centroid, not a hunt. If only a tree model shows the ladder, **do not** treat that as the scientific result.

**Means:** person-specific kinematic information is **more classifiable** when the task is less constrained, under a **matched observation budget**.  
**Does not mean:** more individual coordination dynamics; JcvPCA/RQA work; improvement; creativity; longitudinal change. Time-mean features may be **mean posture** — say so.

Figure 2: three-band accuracy (median ± resample IQR) vs chance/permutation; optional confusion for the matched set.

### Q1 — Change (CORE; this is the “did it change / shared or not / what”)

No separate timepoint-classifier stage.

For **each** of Q1a and Q1b:

1. **Within person** vs own R1/R2 (when R2 exists).  
2. **Across people:** shared direction vs person-specific. No group-mean pose.  
3. **T2 vs T3 not collapsed.**

**Q1a — `P1_guided_open` only.** Reference-anchored JcvPCA. T1 R2 primary reference (R1 sensitivity). Signed exceed vs own T1 R1↔R2 (S2-style, direction-stable). **Hard-error on P2.** Link maps = the look. Ordinary PCA is **not** a second primary. RQA on guided-open is **not** CORE (short cued phrases; would duplicate Q1b’s construct).

**Q1b — `P2_free` only.** One RQA on one pre-registered scalar from the **same 18-link stream** (default: whole-body mean \|ω\|). Params frozen on T1 / T1 R2. **One or two** metrics (RR, DET) with one-sentence English. Equal-length series per person across T as §2. No radius search.

**Energy (HIGH-VALUE SECONDARY):** time-normalised mean \|ω\| (and optionally mean \|ω\|²) on the **same** segmented interval as Q1. Covariate: “was it only faster?” Not a third primary.

### DID / cloud / Q2 / Q3

Unchanged in status: DID_guided and cloud = secondary; Q2 = future/gated on a **CORE** score; Q3 = captions of Q1a maps + one RQA sentence. No entropy family. No HMM/transformers/motifs.

---

## 6. Results / Discussion order

1. Coverage + QC + segmentation gaps (N per cell).  
2. Q0 equal-duration matched ladder + posture limitation.  
3. Q1a within → across → T2 vs T3 → maps → vs R1/R2.  
4. Q1b same; energy if run.  
5. Limits: two repeats; T1 familiarisation; incomplete cells; ID ≠ organisation; JcvPCA ≠ RQA; duration matching assumptions; axis-convention lock; no causal drug/Gaga.  
6. One paragraph: this layer is what the PhD extends.

**Forbidden:** caused by Gaga/psilocybin; control = no Gaga; 13–17 = free dance; ID = change; **mean-posture day gap > R1/R2 ⇒ change**; N without cell table; flexion from rotvecs; p-values while blinded; JcvPCA(P2); unmatched Q0; **unequal-duration band comparison**; windows across exercises; P2 trim fit on later T; mixing export axis conventions.

---

## 7. Figures (acceptance)

| # | CORE figure | Message |
|---|---|---|
| 1 | Coverage matrix | Who is in which cell |
| 2 | Q0 three-band ID | Constraint ladder, equal budget |
| 3 | Q1a link/body map + vs-repeat | What coordination shifted |
| 4 | Q1b RR/DET (or locked pair) vs T, vs R1/R2 | Free-dance timing organisation |

Optional if actually run: energy; cloud. Do **not** require a timepoint-classifier figure.

---

## 8. One-week implementation (CORE only)

| Day | Work |
|---|---|
| **1** | Ingest + header gate + coverage matrix. List P1 files that need segmentation for Q0/Q1a. Freeze P2 interval rule. Do not segment unused Takes. |
| **2** | 18-link extract on eligible files; Q0 equal-duration matched LORO + R1↔R2. |
| **3** | Q0 resample IQR; Figure 2; energy on the Q0/Q1 intervals if extract is done. **Not** a new T-classifier. |
| **4** | Q1a JcvPCA cohort (guided-open, segmented). |
| **5** | Q1a vs R1/R2 + maps (Figure 3). |
| **6** | Q1b one RQA (Figure 4). |
| **7** | Freeze numbers; regenerate 1–4; Methods notes; captions. No new families. |

If Day 1 shows missing P1 segmentation for most Q1a cells, **stop and segment those cells** before Q0 cosmetic polish. If time slips, drop order: energy → Q0 resamples beyond one subsample → never drop coverage, segmentation, Q0 centroid ladder, Q1a, or Q1b.

**Tests:** header gate; Local rejected; JcvPCA(P2) errors; bands from segments not raw P1; Q0 matched pids **and** equal seconds; 3–4 digit pid; golden rotvec vs `s2_extract`.  
**Layout:** `outputs/{qc,q0,q1a,q1b}/`.

---

## 9. Acceptance (CORE lock)

- [ ] Coverage matrix exists; every exclusion has a reason.  
- [ ] P1 CORE uses exercise segments; no cross-exercise windows; P2 uses the frozen interval.  
- [ ] Q0 headline is matched cohort **and** equal duration (resample IQR if subsampled).  
- [ ] Q0 model is nearest centroid (no model leaderboard as the result).  
- [ ] Q1a + Q1b run; JcvPCA(P2) hard-errors.  
- [ ] Figures 1–4 exist and match the captions.  
- [ ] Unrun SECONDARY/FUTURE items omitted, not holes.

New data fills cells. It does not add a new scientific plot.

**PRD status:** locked for CORE implementation. No further analysis families this week.
