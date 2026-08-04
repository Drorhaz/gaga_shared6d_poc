# RQA Existing Project Audit

**Freeze:** `guided-analysis-freeze-v1` @ `5062e22`  
**Branch:** `exploratory/guided-rqa-plan`  
**Projects:** A = `../gaga_jcvpca` (+ Motive stack in `3Layers_project`); B = `gaga_shared6d_poc`

No RQA implementation exists in either project. Freeze explicitly deferred RQA.

---

## 1. Concise evidence map

| Category | Status | Location / notes |
|---|---|---|
| Raw OptiTrack / skeleton CSV | Exists (Project A) | `gaga_jcvpca/data/raw_skeleton/` |
| 18-link rotvec (filtered) | Exists (regenerable) | `data/immutable/rotvec_18link/` (excluded from freeze git; hashed) |
| Segmentation ex09–ex13 | Exists | Workbooks via Project A; `outputs/s4_windows/window_index.csv` |
| Explicit coordination features | Exists / passed descriptive | `src/gaga_shared6d/explicit_features.py`; Stage 0B-A reports |
| Conv embeddings + change vs Drep | Exists / framework PASS | `outputs/s7_conv/`; S7 reports |
| Transformer | Exists / sensitivity only | `outputs/s6_transformer/`; did not outperform Conv |
| PCA reference | Exists | Identity-heavy (~0.84); reference only |
| Reliability gates | Exists | Skill>0 cells; 671 limited |
| Shared direction | Failed / closed | `S8_GATE`; do not reopen |
| Clustering / motifs | Not justified | `STAGE0B_A2_REPERTOIRE_FEASIBILITY.md` |
| Temporal path/spread | Exploratory only | Stage 0B-A2 temporal dynamics |
| RQA | **Not started** | This planning package only |

---

## 2. Project A — movement pipeline (read-only)

Immediate dependency: `/Users/drorhazan/Desktop/gaga_psilo/projects/gaga_jcvpca`  
Deeper Motive stack: `3Layers_project/Layer2_Motive_Kinematics`, `Layer2.5_Segmentation`.

| Component | Key facts |
|---|---|
| Sampling | **120 Hz** |
| Filter | Butterworth LP **10 Hz**, order **4**, zero-phase (`sosfiltfilt`) in rotvec tangent space |
| Gap policy | Short-gap interpolation **off** for analysis; NaNs preserved outside contiguous finite segments |
| Skeleton | Endpoint-relative links; common 18-link space in Project B |
| Segmentation | Exercise IDs from workbooks; Group4 = ex09–ex13 (“Curvilinear exploration”) |
| R1/R2 | Two within-session repetitions of Task Part 1 |
| Explicit features | Pack lives in Project B (`explicit_features.py`), not Layer2 |
| RQA code | None (deferred in Project A master plans) |

---

## 3. Project B — shared learned representation

### Freeze and framework

- Tag: `guided-analysis-freeze-v1` / commit `5062e22`
- Outcome: LIMITED GO; guided results frozen with documentation gaps later addressed by git freeze
- Primary framework: explicit coordination features + reliability-gated Conv `|Δ|` vs Drep
- Unit: within-participant, exercise-resolved (ex09–ex13)
- Shared direction: **closed** (`shared_direction_evidence=False`)

### Participants and findings

| Participant | Conv reliability / change | Notes for RQA |
|---|---|---|
| 651 | Strong T1→T2 and T1→T3 > Drep | First longitudinal feasibility case |
| 790 | Strong T1→T2 and T1→T3 > Drep | First longitudinal feasibility case |
| 252 | Reliable endpoints; mainly T1→T3 > Drep | Stage 3 |
| 671 | Limited endpoint skill | Stage 3; expect sparse interpretable cells |

Exercise emphasis often includes **ex11 / ex13** for 651/790 (participant-specific; no shared pattern).

### Representations already available

| Representation | Dim / form | RQA suitability |
|---|---|---|
| Rotvec 18-link | (T, 18, 3) @ 120 Hz | Source for regional speed series |
| 6D model I/O | (T, 18, 6) windows | Training representation; not primary RQA input |
| Conv embedding | 32-D, ~3–9 windows/exercise | **Insufficient N for RQA** |
| Explicit features | Window/recording scalars | Comparison targets, not RQA series (except derived time series if rebuilt) |
| PCA scores | d=32 | Reference only; **do not** feed into primary RQA |

### What passed / failed

**Passed (retained):** preprocessing validation; mask 30%; masked angular velocity; Conv reliability gate (framework); many gated Conv changes > Drep; explicit features + amp residuals; exercise localization.

**Failed / unsupported:** masked 6D; Transformer > Conv; shared direction; clustering/motifs; P1–P5 progressive stages; uniform cell reliability; group-level claims.

---

## 4. Data facts for RQA feasibility

| Fact | Value |
|---|---|
| Recordings | 24 (4 pid × 3 TP × 2 rep) |
| Guided eval segments | 120 (× ex09–ex13) |
| Duration | median 10 s; range 6–18 s |
| Within-exercise duration spread | ex13 up to 8 s across segments; within pid×ex13 up to 6 s |
| Samples @ 120 Hz | median 1200; 66.7% ≥1000 |
| Samples @ 60 Hz | median 600 |
| Samples @ 30 Hz | median 300; 0% ≥1000 |
| Conv windows / segment | median 5 (range 3–9) |

Implication: ~1000-sample guidance is a **heuristic**; after 10 Hz filtering, 120 Hz samples are temporally redundant. Primary rate must be locked empirically (see parameter plan).

---

## 5. What RQA could add vs duplicate

### Potentially novel

- Predictability (DET, Lmean) of regional **intensity dynamics** beyond mean energy / entropy.
- Persistence / dwelling (LAM, optional TT) not measured by Conv mean-pool embeddings.
- Complexity of recurrent timescales (ENTR) distinct from participation entropy (energy-share entropy).
- Whether Conv-localized exercise changes coincide with temporal reorganization of intensity dynamics.

### Likely redundant / artifactual if uncontrolled

- RR tracking amplitude/energy under fixed radius.
- Line metrics tracking **segment duration** (especially raw Lmax on ex13).
- DET/LAM inflated by filter smoothness without surrogate/Theiler checks.
- Latent path/spread restated without temporal-structure interpretation.
- Motif-like language reopening unsupported clustering claims.

---

## 6. Existing R1/R2 framework to preserve

From S7 / guided freeze:

- \(D_{\mathrm{rep}}\): within-session R1 vs R2 distance / difference at a timepoint.
- Longitudinal change compared descriptively to Drep; ratio > 1 means change exceeds within-session repetition variability.
- R1/R2 is **not** a complete across-session noise floor (`GUIDED_ANALYSIS_LIMITATIONS.md`).

RQA pilot uses the same conceptual role with multi-indicator reporting (no new hard 15%/70% cutoffs).

---

## 7. Key report references

- `GUIDED_ANALYSIS_FINAL_SYNTHESIS.md`
- `GUIDED_ANALYSIS_PARTICIPANT_SUMMARY.md`
- `GUIDED_ANALYSIS_REPRODUCIBILITY_MANIFEST.md`
- `GUIDED_ANALYSIS_FREEZE_DECISION.md`
- `STAGE0B_A2_FINAL_RECOMMENDATION.md`
- `STAGE0B_A2_METHOD_COMPARISON.md`
- `STAGE0B_A2_TEMPORAL_DYNAMICS.md`
- `STAGE0B_A2_REPERTOIRE_FEASIBILITY.md`
- `S7_EMBEDDING_CHANGE_REPORT.md`
- `S8_DIRECTION_SIMILARITY_REPORT.md`
- `S9_CONTROLS_AND_COMPARISON.md`
- `GIT_FREEZE_REPORT.md`

---

## 8. Audit conclusion for RQA planning

Existing projects supply cleaned rotational kinematics, segmentation, R1/R2 logic, Conv localization, and explicit-feature interpretation. They do **not** supply recurrence/temporal-organization metrics. A short staged RQA pilot is warranted as an exploratory extension, with strict novelty and artifact controls, without modifying the freeze.
