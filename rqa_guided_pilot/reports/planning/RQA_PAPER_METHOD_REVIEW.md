# RQA Paper Method Review

**Source:** Sale et al., *Nonlinear Methods for Analyzing Pose in Behavioral Research*  
**Pilot context:** Guided improvisation OptiTrack RQA feasibility (ex09–ex13)  
**Freeze:** `guided-analysis-freeze-v1` @ `5062e22` (untouched)  
**Branch:** `exploratory/guided-rqa-plan`

This review separates (A) paper-supported recommendations, (B) OptiTrack/dataset adaptations, and (C) pilot-specific methodological suggestions.

---

## 1. Scope of the paper relevant to this study

The paper provides a general pose → preprocessing → linear kinematics / PCA → recurrence pipeline for markerless and marker-based movement data. Relevant elements for this OptiTrack rotation study:

- feature selection and dimensionality;
- missing-data / interpolation limits for RQA;
- normalization and detrending;
- filtering and downsampling (case studies);
- Auto-RQA, CRQA, MdRQA;
- AMI for delay \(\tau\); FNN for embedding dimension \(m\);
- recurrence threshold (fixed radius vs target RR), distance rescaling, Theiler window, minimum line length;
- window length (~1000-sample heuristic) and overlap;
- interpretation of RR, DET, L / Lmax, ENTR, LAM, TT;
- warnings: parameter selection reshapes recurrence; PCA before RQA can distort geometry; high-D MdRQA is costly; interpret alongside amplitude metrics; verify stability across a parameter range.

---

## 2. Paper-supported recommendations

### Feature selection and dimensionality

- Prefer the **lowest-dimensional representation that preserves the behavior of interest**.
- High-dimensional pose MdRQA may require feature selection; system-level MdRQA is not reducible to all pairwise CRQA.
- PCA can summarize spatial modes but **should not be treated as a neutral RQA input**: linear projection can distort the geometry on which recurrence depends.

### Preprocessing

- Handle missing data carefully. Interpolation fabricates dynamics when gaps exceed \(g_{\max}=(m-1)\tau\). RR is more sensitive to gap filling than DET.
- Spatial alignment (Procrustes) matters for absolute position data; less relevant for relative joint rotations.
- Normalization: z-score when amplitude is nuisance; unit-interval scaling when relative fluctuation shape matters. Prefer **trial-level** normalization over local window z-scoring when comparing across time.
- Detrend only when drift is artifactual.

### Filtering / sampling (case-study practice)

- Case studies use zero-phase Butterworth low-pass (commonly ~10 Hz) and often downsample (e.g., to 30 Hz) for long recordings.
- AMI for pose at 30–60 Hz often yields \(\tau \approx 10\)–30 frames; FNN often \(m \approx 3\)–5 (case studies often \(m=4\)).
- AMI curves may show clear minima, plateaus, oscillatory minima, or slow decay — **select a plausible band and test robustness**, not a single attractive minimum.

### RQA variants

| Variant | Paper role |
|---|---|
| Auto-RQA | Temporal organization of one signal |
| CRQA | Pairwise coupling / shared state visitation |
| MdRQA | Collective multivariate state recurrence |

Choose by scientific question, not availability.

### Threshold and safeguards

- Fixed mean-rescaled radius: RR is a dependent measure; common heuristic RR ~2–5% as diagnostic.
- Target RR: equalize density when scales differ; then \(\varepsilon\) becomes informative; RR is **not** an outcome.
- Distance rescaling by mean pairwise distance preferred for interpretability.
- Theiler window ≈ \(\tau\) (or more conservative ACF zero-crossing) to remove trivial temporal adjacency (Auto-RQA).
- \(L_{\min}=2\) default; raise if DET near ceiling (95–100%).

### Windowing

- For long (>1–2 min), nonstationary recordings: sliding windows with ~**1000 samples** heuristic and ~50% overlap.
- This is a **stability heuristic**, not a hard law.

### Metric interpretation (paper)

| Metric | Meaning |
|---|---|
| RR | How often states recur (density); no temporal organization alone |
| DET | Fraction of recurrent points on diagonals → predictability |
| L / Lmax | Duration of predictable episodes; Lmax = longest |
| ENTR | Diversity of diagonal-line lengths → complexity of recurrent timescales |
| LAM | Vertical-line prevalence → dwelling / laminar phases |
| TT | Mean vertical length → average dwell time |

Interpret **jointly**. High RR + low DET ≈ unstructured revisits; low RR + high DET ≈ rare structured sequences; high DET + high ENTR ≈ deterministic but multi-timescale; high DET + low ENTR ≈ uniform/periodic structure. Do **not** equate higher DET with better learning, higher ENTR with creativity, or lower RR with flexibility without context.

### Sensitivity

- Verify substantive conclusions across a **small grid** of \(\tau\), \(m\), and radius / RR settings.
- Interpret RQA alongside linear amplitude metrics.

---

## 3. OptiTrack / guided-improvisation adaptations

| Topic | Adaptation | Rationale |
|---|---|---|
| Representation | Regional **angular-velocity magnitudes** from 18-link rotvec, not absolute marker XYZ | Matches frozen rotation pipeline; paper’s Procrustes/position path is for landmarks |
| Filter | Keep validated **10 Hz order-4 zero-phase Butterworth**; no new cutoffs | Freeze + Layer2 parity; smoothness assessed via rate/Theiler/surrogates |
| Gaps | Respect Layer2 **no short-gap interpolation** / NaN-segment policy; if any fill used, enforce \(g_{\max}=(m-1)\tau\) | Avoid fabricated recurrence |
| Segment length | Guided exercises ≈ **6–18 s** (median 10 s) | Too short for paper’s 30–120 s sliding windows → **full-exercise RQA** |
| ~1000 samples | Heuristic only | At 120 Hz many segments reach N≈1000, but after 10 Hz filtering samples are temporally redundant |
| Sampling rate | Stage 1 compares **120 / 60 / 30 Hz** (30 diagnostic); primary rate **not pre-declared** | Lock from T1 AMI, autocorrelation, RR, R1/R2, DET/LAM sensitivity, surrogates, compute |
| PCA before RQA | **Not used** as primary RQA input | Paper warning + existing PCA is identity-dominated reference |
| MdRQA dim | Compact **4–6** regional channels, not 18 links | Cost + interpretability |
| Normalization | Parallel amplitude-preserving and trial-level z-score | Separate amplitude from temporal structure |

---

## 4. Pilot-specific suggestions (not paper prescriptions)

1. **Balanced T1-only AMI/FNN** across all four participants (not only 651/790), all primary regions, ex09–ex13, R1/R2.
2. **Duration control:** same-exercise claims; report duration / \(N_{\mathrm{embed}}\); primary line metric **Lmean**; secondary **Lmax/\(N_{\mathrm{embed}}\)**; truncation sensitivity.
3. **Temporal surrogates:** full shuffle + block shuffle as Stage-1 negative controls (paper stresses structure can be artifactual; surrogates operationalize that check).
4. **R1/R2 multi-indicator repeatability** continuous with Conv Drep language, without ad hoc 15%/70% gates.
5. **Hardened PASS/FAIL** requiring surrogate disruption, duration robustness, and non-redundancy vs explicit/Conv features.
6. Conv window embeddings are **not** a suitable primary RQA series (median ~5 windows/exercise).

---

## 5. Implications for the pilot design

- Scientifically justified: Auto-RQA on regional intensity dynamics; compact MdRQA; optional CRQA for one pairwise question.
- Not justified at start: full 18-link MdRQA; PCA→RQA primary path; sliding-window RQA; posture-recurrence claims from speed magnitudes.
- Parameter selection must be **T1-only**, broad, and band-based.
- Primary sampling rate is an **empirical Stage-1 freeze**, not a sample-count default.

---

## 6. Distinctions checklist

| Claim type | Examples |
|---|---|
| Paper-supported | AMI/FNN; Theiler≈τ; \(L_{\min}=2\); fixed vs target threshold; ~1000 heuristic; PCA caution; joint metric interpretation |
| Dataset adaptation | Full-exercise unit; angular-velocity magnitudes; keep 10 Hz filter; rate bake-off; compact MdRQA |
| Our suggestion | Surrogates; duration normalization of Lmax; multi-indicator R1/R2; hardened novelty PASS gate |
