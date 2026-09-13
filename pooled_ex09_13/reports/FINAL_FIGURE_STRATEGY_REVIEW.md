# Final figure strategy review (committee packaging)

**Status:** strategy only — no plots generated.  
**Sources of truth:** marker-gap pooled JcvPCA (`gaga_jcvpca/.../marker_gap_policy_ex09_13/`); pooled coupling/explicit/Conv under `pooled_ex09_13/`; exercise-resolved synthesis under `synthesis/` (supplementary localization only).  
**Constraint:** ≤2 slides, ≤2 graphs/slide, ≤4 graphs total.

---

## 1. Scientific story in 3 sentences

Across the complete guided block ex09–ex13, JcvPCA shows participant-specific redistribution of body-link contributions that exceeds each participant’s own within-session T1 R1/R2 variability at D12 (252: 3/20; 651: 4/10; 671: 8/18 with S3=4; 790: 7/20). A separate biomechanical layer — pooled regional and trunk–arm coupling — also reorganizes beyond its own R1/R2 floors, but in heterogeneous directions (some relationships strengthen, some weaken). The defensible claim is therefore participant-specific longitudinal coordination reorganization consistent with changes beyond repetition variability — not a shared anatomical trajectory, not proven motor learning, and not A3 as a cohort claim.

---

## 2. What the committee must understand

In under two minutes, a committee member should leave with:

1. Longitudinal change is judged against **each participant’s own R1/R2 floor** (method-specific).
2. **JcvPCA** is the primary result: selected body links redistribute beyond that floor.
3. Anatomical patterns **differ across participants** (671 strongest; 651 incomplete link set).
4. **Pooled coupling** is a second, non-identical construct that also changes, with **mixed ↑/↓** directions.
5. The right language is **heterogeneous participant-specific coordination reorganization**, not “coupling goes up/down with learning.”

---

## 3. Pooled vs exercise-resolved decision

### Decision

**Main committee figures use pooled results only.**

Exercise-resolved findings may appear only as:

- qualitative driver labels / tiny categorical insets;
- spoken narration;
- supplemental slides;

**not** as raw magnitudes plotted on the same quantitative axis as pooled effects.

### Why

Pooled and exercise-resolved answer different questions:

| Estimand | Question |
|---|---|
| Pooled ex09–13 | What changes across the complete guided block? |
| Exercise-resolved | Where within the block is change expressed? |

They differ in sample count, duration, within-block heterogeneity, variance, R1/R2 reference construction, and temporal structure. Equal-weight recording aggregation further means a strong single-exercise cell (e.g. 651–ex13 trunk–arm) is **not** a larger version of the pooled Δ on a shared scale.

### Allowed combined use (non-quantitative)

If space allows a micro-annotation (not a fourth independent quantitative graph):

- **651:** label “ex13-compatible localized driver” next to pooled trunk–arm ↑ — categorical compatibility, no Δ comparison.
- **671:** three tiny categorical chips (ex10 ↓ / ex12 ↑ / ex09 stable) explaining why pooled coupling is mixed — status glyphs only.

**Reject** any main-panel bar/lollipop that places pooled Δ and exercise Δ on one axis.

---

## 4. UMAP / embedding decision

### Decision

**Reject UMAP / MDS / “coordination landscape” embeddings from the main figures.**

### Why (explicit)

| Requirement for an embedding to be main-figure-worthy | Status |
|---|---|
| Clear scientific meaning of axes / neighborhoods | Fail — not an estimand of the validated pipeline |
| Participant identity not dominating | High risk with n=4 × few recordings |
| R1/R2 relationships interpretable in the embedding | Fail — floor logic is not geometric neighborhood |
| Sufficient sample size | Fail for stable stochastic embeddings |
| Stochastic choices do not invent clusters | High risk |
| Adds information beyond JcvPCA body maps | No — anatomy + coupling already carry the story |

A beautiful ambiguous landscape would compete with the one result that is uniquely strong: **anatomical link redistribution**. Decorative dimensionality reduction is worse than an interpretable body map.

*(If ever revisited: only as a supplemental sensitivity figure after a pre-registered embedding protocol — not for these two slides.)*

---

## 5. Critical evaluation of candidates A–E

### Candidate A — R1/R2 evidence scatter (X=NV, Y=D12)

**Verdict: usable as Graph 1 if carefully encoded; not sufficient alone as “proof of A2.”**

Validated fields in `tables_to_show/05_nv_profile_signed_tiers.csv` support a magnitude view:

- X ≈ `|nv_signed_t1|`
- Y ≈ `|long_signed_single|`
- Y=X ≈ magnitude-exceedance boundary

But A2 also requires **direction stability under R1/R2 anchor swap** (`sign_reference_stable`, reverse-signed columns). A naive “points above the diagonal = A2” plot **distorts** the signed / anchor-swap logic.

**If used:** encode A2 with fill/halo; encode sign-stability with shape; caption must say magnitude gate ≠ A2. Prefer matched absolute ratio as an alternate X (`matched_abs_ratio`) only if the diagonal story remains clear — default remains |NV| vs |Δ|.

**Do not invent new signed metrics.**

### Candidate B — JcvPCA anatomical body maps

**Verdict: strongest hero candidate. Prioritize.**

Anatomical interpretability is JcvPCA’s unique advantage. Existing avatar assets / link tables exist under `gaga_jcvpca/docs/slide45_figures/avatar_pooled/` and supervisor figure packs. Must show:

- A2 as k/**n_links** with correct denominators (651 = **4/10**);
- exclusions / missing anatomy gray;
- S3 marks **only on 671**;
- no cross-participant magnitude ranking.

### Candidate C — pooled coupling fingerprint

**Verdict: essential second-layer figure.**

Best form: four participant body/network glyphs or signed dumbbells for `{regional, trunk–arm}` with exceed / limited / within status — not a generic table. Directly communicates mixed ↑/↓ reorganization.

### Candidate D — pooled vs localized exercise explanation

**Verdict: reject as a full quantitative main graph; optional categorical micro-inset only.**

Scientific value for 671 (mixed local drivers) and 651 (ex13 driver) is real, but magnitude comparison risk is high. Prefer narration + chips over a fourth full panel unless Package 3 needs a qualitative-only panel.

### Candidate E — UMAP / MDS / PCA landscape

**Verdict: reject** (see §4).

---

## 6. Three candidate 4-graph packages

### PACKAGE 1 — JcvPCA-first (threshold → anatomy → coupling → roles)

| Slide | Left | Right |
|---|---|---|
| 1 | **G1** R1/R2 evidence scatter (Candidate A, properly encoded) | **G2** Four-participant JcvPCA body maps (Candidate B) |
| 2 | **G3** Pooled coupling fingerprint (Candidate C) | **G4** Role-aware multimethod strip (categorical; pooled D12) |

**Strengths:** proves the floor logic quantitatively; anatomy as hero; coupling mixedness clear; shows 651 convergence vs 252 discordance without magnitude voting.  
**Weaknesses:** G4 can look “dashboard-y” if over-encoded; schematic may be clearer than scatter for some examiners.  
**Risk:** G1 misread as “above diagonal = A2” without shape encoding.

### PACKAGE 2 — Anatomy-first (hero anatomy; soft threshold)

| Slide | Left | Right |
|---|---|---|
| 1 | **G1** Four-participant JcvPCA body maps (large; Candidate B) | **G2** Compact R1/R2 *schematic* + A2 count badges (not a full scatter) |
| 2 | **G3** Pooled coupling fingerprint (Candidate C) | **G4** Qualitative localization chips for 651 & 671 only (Candidate D lite; categorical) |

**Strengths:** maximum anatomical impact; localization explained without pooled≠exercise magnitude trap.  
**Weaknesses:** R1/R2 floor is schematic rather than link-level proof; some examiners want the scatter.  
**Risk:** G2 feels “method poster” rather than result.

### PACKAGE 3 — High-impact / committee version (memorable pair + proof pair)

| Slide | Left | Right |
|---|---|---|
| 1 | **G1** JcvPCA body maps (Candidate B) | **G2** Pooled coupling fingerprint (Candidate C) |
| 2 | **G3** R1/R2 evidence scatter (Candidate A) | **G4** Role-aware multimethod strip (pooled categorical) |

**Strengths:** Slide 1 is immediately memorable (anatomy + mixed coupling); Slide 2 supplies defensibility.  
**Weaknesses:** Floor logic appears after the hero — slightly violates the “understand R1/R2 first” sequence unless the speaker opens with one spoken sentence before Slide 1.  
**Risk:** committee fixates on coupling colors before understanding JcvPCA primacy.

---

## 7. Recommended final package

### Choice: **PACKAGE 1 — JcvPCA-first**

**Why this one**

1. Matches the required cognitive sequence: floor → anatomical redistribution → mixed coupling → heterogeneous reorganization.
2. Keeps JcvPCA primary and anatomically legible (G2 hero).
3. Uses pooled estimands only on all quantitative panels.
4. Avoids UMAP and avoids pooled-vs-exercise magnitude axes.
5. G4 handles 651 multimethod convergence and 252 discordance without counting votes.
6. Candidate A is retained but **constrained** so it does not misrepresent A2.

**Relative to prior thesis packaging (`THESIS_FINAL_FIGURE_SPECIFICATIONS.md`):** replace the old exercise-tilted coupling matrix language with **pooled** coupling; keep anatomy + R1/R2 logic; keep role-aware (not magnitude) multimethod summary.

Exercise-resolved material stays out of the four main graphs except optional one-line labels inside G3/G4 (“ex13-compatible” / “mixed local drivers”) — no fourth quantitative localization panel.

---

## 8. Detailed specification of the chosen 3–4 graphs

### Graph G1 — R1/R2 magnitude gate with A2 encoding

| # | Spec |
|---|---|
| 1. Scientific question | Do D12 link-contribution changes exceed each participant’s own T1 signed NV magnitude, and which links also satisfy A2? |
| 2. Exact conclusion | Many links sit near the NV floor; A2-passing links (filled) exceed NV **and** pass direction stability — supporting beyond-repetition change without claiming a shared anatomy. |
| 3. Data source | `gaga_jcvpca/.../tables_to_show/05_nv_profile_signed_tiers.csv` (D12 / T1_vs_T2 only); headline denominators from `09_headline_a2_summary.csv` |
| 4. Pooled vs exercise-resolved | **Pooled** marker-gap ex09–13 JcvPCA only |
| 5. Exact variables | X=`|nv_signed_t1|`; Y=`|long_signed_single|`; flags: `a2_pass`, `sign_reference_stable`, `nv_profile_tier` (S3), `coverage` via facet badge |
| 6. Visual form | Four small-multiple scatter panels + Y=X reference line |
| 7. Axes | X: within-session \|NV\| (T1 R1–R2); Y: \|D12 signed longitudinal change\|; identical scales within participant (do **not** force one global axis across participants) |
| 8. Encoding | Fill = A2 pass; hollow = not A2; shape = sign-stable vs not; star/outline = S3 (671 only); gray low-alpha = excluded/unavailable links not plotted or plotted as NA ticks; 651 facet subtitle “n_links=10 (marker-gap)” |
| 9. Participant organization | Facets: 252 \| 651 \| 671 \| 790 |
| 10. R1/R2 visible? | **Yes** (X-axis and Y=X) |
| 11. Magnitude comparisons valid? | Within-participant link comparison only; **no** cross-participant ranking of \|Δ\| |
| 12. Main limitation | Y=X shows magnitude gate only; A2 needs shape/fill legend or the plot underclaims/overclaims |
| 13. Title | “Longitudinal link change vs within-session repetition variability (D12)” |
| 14. Caption takeaway | “A2 links exceed each participant’s own T1 R1–R2 signed NV and remain direction-stable under anchor swap; anatomical identity of those links differs across participants.” |

**New computation?** No — visualization of validated columns only.

---

### Graph G2 — JcvPCA anatomical redistribution maps (hero)

| # | Spec |
|---|---|
| 1. Scientific question | Which body links redistribute contribution beyond R1/R2, and how do patterns differ across participants? |
| 2. Exact conclusion | All four show nonzero A2 at D12; 671 is strongest (8/18, S3=4); 651 must be read as 4/**10**; patterns are participant-specific. |
| 3. Data source | `09_headline_a2_summary.csv`; A2/S3 link lists from `05_nv_profile_signed_tiers.csv` / `pooled_ex09_13/outputs/jcvpca_reference.csv`; exclusions `02_comparison_link_exclusions.csv`; geometry from `docs/slide45_figures/avatar_pooled/` or verified avatar packs |
| 4. Pooled vs exercise-resolved | **Pooled** |
| 5. Exact variables | Per-link A2 pass; signed direction of `long_signed_single` for A2 links; S3 flag; exclusion mask; A2 count k/n |
| 6. Visual form | Four body/link small multiples (same pose, same legend) |
| 7. Axes | N/A (spatial anatomy) |
| 8. Encoding | Link color = signed redistribution direction (diverging, muted); intensity only within participant; halo/outline = A2; diamond/star = S3 (671); gray dashed = excluded/unsupported; badge “A2 = k/n”, coverage band |
| 9. Participant organization | 2×2 grid: 671 (strongest) top-left or visually primary; 651 with incomplete skeleton clearly broken/gray |
| 10. R1/R2 visible? | Indirectly via A2 definition in legend (floor proven in G1) |
| 11. Magnitude comparisons valid? | Intensity comparable **within** a map only; never rank participants by color intensity |
| 12. Main limitation | Signed contribution change ≠ “better coordination”; S3 ≠ approved A3 |
| 13. Title | “Participant-specific JcvPCA link redistribution beyond R1/R2 (pooled ex09–13, D12)” |
| 14. Caption takeaway | “Selected links change beyond each participant’s own repetition variability; the anatomical pattern is not shared, and 651’s denominator reflects marker-gap exclusions (4/10).” |

**New computation?** No — reuse validated A2 maps / link tables.

---

### Graph G3 — Pooled coupling reorganization fingerprint

| # | Spec |
|---|---|
| 1. Scientific question | Do regional and trunk–arm coupling relationships reorganize beyond their own R1/R2 floors at the pooled-block level, and in which directions? |
| 2. Exact conclusion | Reorganization is heterogeneous: 651 trunk–arm ↑ (cleanest); 671 mixed ↓regional/↑trunk–arm; 252 regional ↓; 790 mixed — not “learning = less coupling.” |
| 3. Data source | `pooled_ex09_13/outputs/coupling/pooled_coupling_longitudinal.csv` (D12 rows) |
| 4. Pooled vs exercise-resolved | **Pooled** equal-weight ex09–13; optional categorical footnote only for 651/671 local drivers |
| 5. Exact variables | `regional_coupling`, `trunk_arm_lagged_coupling`: `Delta_mean`, `Drep_T1`, `category`, `direction` |
| 6. Visual form | Four participant fingerprints: body schematic with two edges (regional mesh + trunk–arm link) **or** paired signed dumbbells (preferred if anatomy crowded) |
| 7. Axes | If dumbbell: X = signed Δ; reference band ±Drep; no shared axis across metrics unless z-scored **within metric** for display only (prefer raw with per-metric panels) |
| 8. Encoding | Arrow/color: ↑ warm / ↓ cool; stroke weight or solid fill = EXCEEDS; dashed = LIMITED; ghost = WITHIN; small JcvPCA badge (STRONG/PRESENT) as context, not a second magnitude |
| 9. Participant organization | Same order as G2 |
| 10. R1/R2 visible? | **Yes** (±Drep band or “exceeds own Drep” solid vs dashed) |
| 11. Magnitude comparisons valid? | Compare Δ to **own** Drep within metric; do **not** compare regional Δ to trunk–arm Δ as “larger effect,” and do **not** compare to JcvPCA \|Δ\| |
| 12. Main limitation | Speed-magnitude coupling ≠ Chang joint-phase; construct ≠ JcvPCA; tiny Drep flagged unstable in CSV |
| 13. Title | “Pooled coupling reorganization relative to each participant’s own R1/R2 floor” |
| 14. Caption takeaway | “Coordination relationships strengthen and weaken in a participant-specific pattern; mixed directions are the result, not a failure of the analysis.” |

**Optional micro-labels (not a new graph):** 651 “ex13-compatible”; 671 “local drivers mixed (ex10↓/ex12↑/ex09 stable)” — categorical only.

**New computation?** No.

---

### Graph G4 — Role-aware multimethod strip (pooled D12)

| # | Spec |
|---|---|
| 1. Scientific question | How do independent representations relate to the JcvPCA primary result at the pooled-block level? |
| 2. Exact conclusion | 651 shows pooled multimethod convergence; 671 is JcvPCA-dominant with limited Conv; 252 is discordant (JcvPCA/coupling present, Conv ≤ Drep); methods are roles, not votes. |
| 3. Data source | `pooled_ex09_13/outputs/POOLED_CROSS_METHOD_MATRIX.csv`; Conv ratios from `outputs/conv/pooled_conv_longitudinal.csv`; JcvPCA reference CSV; **omit** Transformer/PCA/RQA as primary cells or mark N/A |
| 4. Pooled vs exercise-resolved | **Pooled** categories only |
| 5. Exact variables | Categorical cells: JcvPCA, Coupling (with ↑/↓/mixed glyph), Conv, Explicit (optional). No raw cross-method magnitudes |
| 6. Visual form | Compact 4×N categorical matrix / icon strip (not heatmap of continuous values) |
| 7. Axes | Rows = participants; columns = method roles |
| 8. Encoding | Category colorblind-safe ordinal (STRONG / PRESENT / LIMITED / ABSENT / N/A); coupling glyph separate; 651 row subtle highlight as convergence case; 252 as discordance case |
| 9. Participant organization | 671, 651, 790, 252 (narrative order) or match G2 |
| 10. R1/R2 visible? | Implicit in categories (exceed/within already computed) |
| 11. Magnitude comparisons valid? | **None across methods** — categorical only |
| 12. Main limitation | Can look like a scoreboard; mitigate with “roles, not votes” header |
| 13. Title | “Pooled D12 roles: convergent, complementary, and discordant evidence” |
| 14. Caption takeaway | “Independent methods do not vote; they show that redistribution (JcvPCA) and mixed coupling can co-occur with or without Conv exceeding its own Drep.” |

**New computation?** No — matrix already built.

---

## 9. Data-validity checks required before plotting

Before any figure generation:

1. **JcvPCA denominators:** 252=20, 651=**10**, 671=18, 790=20 for D12; never display 651 as /18 or /20.
2. **A2 link lists** match `jcvpca_reference.csv` / `05_nv_profile_signed_tiers.csv` (`a2_pass=True`).
3. **S3 marks only on 671 D12** (four links); no A3 wording on figures.
4. **Exclusions visible** for 651 (and any grayed links) from `02_comparison_link_exclusions.csv`.
5. **G1 encoding:** every A2 point must also be `sign_reference_stable` consistent; document any A2 vs diagonal mismatch in a QA table before freeze.
6. **Coupling D12 categories** match `pooled_coupling_longitudinal.csv` (EXCEEDS/LIMITED/WITHIN + direction).
7. **No pooled vs exercise Δ** on shared axes; any ex13/ex10/ex12 notes are categorical.
8. **Conv cells** use pooled recording-level categories (651 EXCEEDS, 790 EXCEEDS, 671 LIMITED, 252 WITHIN) — not exercise-level bars.
9. **D12 only** on main slides; D13 not in the four graphs (supplemental if needed).
10. **Colorblind-safe** diverging maps; print-safe grays for exclusions.
11. **Reuse** avatar geometry provenance from `slide45_figures` rather than inventing new skeletons.
12. **Caption language** locked to: redistribution / reorganization / beyond R1/R2; forbid learning / DOF unfreezing / Gaga / psilocybin / “better coupling.”

---

## 10. What NOT to show

- UMAP / MDS / PCA “landscape” as a main result  
- Chang-style joint-angle xcorr / Cardan panels  
- A3 as a cohort claim; “51 organization” as A3  
- Cross-participant ranking bars of JcvPCA effect size  
- Pooled vs single-exercise raw magnitude comparison  
- “Reduced coupling = learning” or “increased coupling = learning” slogans  
- Transformer bakeoff; PCA identity probe as adaptation evidence  
- RQA as a primary pooled panel (full-block not computable in freeze)  
- Method vote tallies / stacked “3 of 4 methods agree” pies  
- Free-movement / fun-null as main D12 story  
- Radar charts, Sankey, chord diagrams, 3D graphics  

---

## 11. Final two-slide storyboard

### Slide 1 — Beyond repetition variability: participant-specific link redistribution

**Title:** Longitudinal JcvPCA change exceeds each participant’s own R1/R2 variability (pooled ex09–ex13, D12)

- **Graph left (G1):** R1/R2 evidence scatter with A2 / sign-stability encoding  
- **Graph right (G2):** Four anatomical body/link maps (hero), A2 = k/n with honest denominators; S3 only on 671  

**One-line slide conclusion:** Selected body links redistribute contribution beyond within-session repetition variability, and the anatomical pattern is participant-specific — not a single shared trajectory.

---

### Slide 2 — A second layer: mixed coordination reorganization (not a universal coupling direction)

**Title:** Pooled coupling reorganizes heterogeneously — and methods play different roles

- **Graph left (G3):** Pooled regional + trunk–arm fingerprint (↑/↓/exceeds own Drep)  
- **Graph right (G4):** Role-aware pooled multimethod strip (JcvPCA / Coupling / Conv; roles ≠ votes)  

**One-line slide conclusion:** Coordination relationships strengthen and weaken in participant-specific ways; the result is heterogeneous reorganization consistent with changes beyond R1/R2 — with 651 as pooled multimethod convergence and 671 as JcvPCA-dominant.

---

## Appendix — Key decisions (explicit answers)

### Should main figures use only pooled results, or combine pooled + exercise-resolved?

**Only pooled for quantitative main panels.** Exercise-resolved evidence may appear as categorical driver labels (651 ex13-compatible; 671 mixed local drivers) without shared magnitude axes.

### Is UMAP scientifically justified?

**No.** It would be decorative and potentially misleading relative to validated JcvPCA anatomy and pooled coupling fingerprints.

### Recommended package

**PACKAGE 1 — JcvPCA-first** (G1 scatter → G2 anatomy → G3 coupling → G4 roles).

---

**STOP.** No plots generated. No new scientific analysis. Awaiting approval before figure production.
