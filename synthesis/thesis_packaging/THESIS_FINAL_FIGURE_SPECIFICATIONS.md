# Thesis final figure specifications

**Exactly three primary figures.** Packaging specs only — do not require new scientific computation. Reuse existing slide/avatar assets where possible (`gaga_jcvpca/docs/slide45_figures/`, supervisor figure packs).

---

## Figure 1 — JcvPCA + R1/R2 framework

| Item | Specification |
|---|---|
| Scientific question | How is a longitudinal link-contribution change interpreted relative to within-session repetition variability? |
| Exact source files | `gaga_jcvpca/.../CLAIMS.md`; `SIGNED_NV` / NV tier rules in `CLAIMS.md` + `NV_PROFILE.csv` column definitions; schematic only (no new numbers required) |
| Exact data fields | Conceptual: `nv_signed`, `long_signed`, `long_signed_rev`, tiers S0–S2 (A2); mention S3/A3 as gated, not headline |
| Scope | All participants conceptually; method logic, not results |
| Plot type | Process / flow diagram (not a results heatmap) |
| Visual encoding | Boxes: T1 reference subspace → R1 vs R2 (NV floor) → T1→T2 matched contrast → A2 = exceed + direction-stable; small footnote that Conv/RQA/coupling use **method-specific** repetition floors |
| Required labels | “Within-session repetition variability (T1 R1–R2)”; “Longitudinal contrast (D12 primary)”; “A2 (S2)”; “A3/S3 supervisor-gated” |
| Headline result | A longitudinal link change is interpreted relative to the participant’s own within-session repetition variability |
| Limitation | Single-rep NV pair; footing asymmetry with Step-5 organization |
| Caption language | “Schematic of the reference-anchored JcvPCA analysis. Longitudinal change in link contribution is compared with the same participant’s T1 R1–R2 signed natural variability. A2 requires magnitude exceedance and direction stability under R1/R2 anchor swap. A3 remains supervisor-gated and is not implied by Step-5 organization counts.” |
| Status | **Main Figure 1** |

---

## Figure 2 — Main JcvPCA D12 result (four participants)

| Item | Specification |
|---|---|
| Scientific question | Where did participant-specific link redistribution exceed R1/R2 at T1→T2? |
| Exact source files | `09_headline_a2_summary.csv`; `NV_PROFILE.csv` (A2/S3 links); coverage from same; exclusions `comparison_link_exclusions.csv` / tables_to_show `02_*`; avatar/link maps `docs/slide45_figures/avatar_pooled/` or `docs/supervisor_meeting_figures_marker_gap_policy_ex09_13/` |
| Exact data fields | `A2_S2_pass`, `n_links`, `S3`, `coverage_band`, `rep_pass`; per-link A2 list from `nv_profile_tier ∈ {S2,S3}` |
| Scope | **D12 / T1→T2 only** for shared display; pids 252, 651, 671, 790 |
| Plot type | Four body/link small multiples (or avatar maps) with identical encoding |
| Visual encoding | Highlight A2 links; annotate A2 count as **k / n_links** (651 must read **4/10**, not 4/18); coverage band badge; S3 mark **only on 671**; exclusions greyed; **no cross-participant bar ranking of effect size** |
| Required labels | Participant ID; “D12”; “A2 = k/n”; “coverage: adequate/limited”; 671: “S3 candidates = 4”; 651: “marker-gap exclusions — incomplete link set” |
| Headline result | Longitudinal redistribution is detectable in all four participants at D12, but anatomical pattern is participant-specific |
| Limitation | Marker-gap exclusions; rep_pass only 671; A3 not approved; D13 not shown here |
| Caption language | “Participant-specific JcvPCA T1→T2 (D12) link-contribution changes exceeding each participant’s T1 R1–R2 signed natural variability (A2). Link sets and denominators reflect marker-gap policy. Coverage was adequate for all four D12 comparisons. Only participant 671 met the full S3 candidate stack (four links); A3 remains supervisor-gated. Magnitudes are not compared across participants.” |
| Status | **Main Figure 2** |

**Per-participant callouts (on-figure or legend):**

| Pid | Must show |
|---|---|
| 671 | Strongest stack: A2=8/18, S3=4, rep_pass=True, adequate coverage |
| 651 | A2=4/**10**, exclusions visible |
| 790 | A2=7/20, adequate coverage, S3=0 |
| 252 | A2=3/20, adequate coverage, modest D12 localization |

---

## Figure 3 — Cross-method coordination synthesis (incl. coupling)

| Item | Specification |
|---|---|
| Scientific question | Do independent movement representations provide convergent, complementary, or discordant evidence of participant-specific longitudinal change at D12? |
| Exact source files | `CROSS_METHOD_PARTICIPANT_MATRIX.md` / `.csv`; `COUPLING_INTERPRETATION_SUMMARY.md`; `EXISTING_COUPLING_LONGITUDINAL_RESULTS.csv` (robust D12 rows only); `individual_profiles.csv`; `STAGE2_GATE.json` |
| Exact data fields | Categorical role cells — not raw \|Δ\| magnitudes across methods |
| Scope | D12 primary; four participants; methods as **roles** |
| Plot type | Categorical matrix / heatmap with annotations (not a quantitative multi-axis plot) |
| Visual encoding | Rows = participants; columns = JcvPCA \| Coupling \| Conv \| Explicit features \| RQA. Cell values: STRONG / PRESENT / COMPLEMENTARY / LIMITED / UNRELIABLE / NOT_APPLICABLE. Optional glyphs: `↑` `↓` `mixed` `stable` for coupling only where audit supports |
| Required labels | Evidence **roles** in column headers (DETECTION+ANATOMY / INTERPRETATION / DETECTION+EXERCISE / INTERPRETATION / TEMPORAL); footnote: “not votes”; “coupling = regional speed metrics, not Chang joint phase” |
| Headline result | Independent representations reveal complementary rather than identical aspects of participant-specific longitudinal change |
| Limitation | Constructs non-equivalent; many coupling cells R1/R2-inconsistent; RQA not primary; Transformer/PCA omitted or footnote-only |
| Caption language | “Role-aware D12 synthesis. JcvPCA provides link-level redistribution relative to signed NV. Existing regional coupling (speed-magnitude) shows mixed strengthening and weakening beyond its own R1/R2 floor in selected exercises. Conv and explicit features contribute detection/exercise localization and descriptive biomechanics; RQA contributes limited temporal complementarity (651–ex13; 790–ex11). Methods are not counted as votes.” |
| Status | **Main Figure 3** |

### Suggested cell content (D12)

| Pid | JcvPCA | Coupling | Conv | Explicit | RQA |
|---|---|---|---|---|---|
| **651** | PRESENT (A2 4/10) | PRESENT ↑ trunk–arm @ ex13 | STRONG (>Drep) | PRESENT (entropy/dim) | COMPLEMENTARY (ex13) |
| **671** | STRONG (A2 8/18, S3=4) | PRESENT mixed ↑/↓ (ex12/ex10); stable @ ex09 | LIMITED (3/6 cells) | LIMITED | NOT_APPLICABLE |
| **790** | PRESENT (A2 7/20) | LIMITED (↓ regional @ ex13); ex11 UNRELIABLE | PRESENT (>Drep) | PRESENT (entropy/dim) | COMPLEMENTARY (ex11) |
| **252** | PRESENT limited (A2 3/20) | PRESENT mixed ↑/↓ | ABSENT/≤Drep pooled | PRESENT (symmetry/coupling) | NOT_APPLICABLE |

---

## Explicit non-figures (main text)

- Chang-style joint xcorr panel  
- “51 organization” as A3 headline  
- Transformer vs Conv bakeoff as main result  
- PCA identity probe as adaptation evidence  
- Method vote tallies / cross-method magnitude bars  

Backup/supplemental allowed: S3 caveat slide; persistence for 671; D13 coverage-limited maps; Conv exercise bars.
