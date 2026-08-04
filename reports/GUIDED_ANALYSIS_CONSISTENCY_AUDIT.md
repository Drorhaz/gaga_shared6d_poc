# Guided Analysis — Consistency Audit

**Policy:** Historical reports are **not** silently rewritten. Issues are recorded here;
the consolidated freeze reports (`GUIDED_ANALYSIS_*`) carry the corrected wording.

---

## Checklist

| # | Forbidden / risky claim | Audit result | Action |
|---|---|---|---|
| 1 | Transformer described as primary model | **Clear** in final/S6 readiness (“not primary; sensitivity only”). S6B/S7 correctly name Conv as primary for downstream gated work. | None on historical files |
| 2 | Stable shared direction suggested | **Clear** — S8/S9/GO/NO-GO/`shared_direction_evidence=False` | None |
| 3 | Clustering described as successful | **Clear** — A2 `clustering_justified=False` | None |
| 4 | P1–P5 progressive segmentation claimed | **Clear** — A2 segmentation report rejects; explains Task Part 1 | None |
| 5 | All participant cells treated as reliable | **Mostly clear** in S7/0B-A (cell counts). Risk if prose says “participants” without gates. | Freeze docs always state cell fractions |
| 6 | R1/R2 called complete noise floor | **Clear** in `DATA_VALIDATION_REPORT.md` warning; freeze Limitations §5 | None |
| 7 | Amp-controlled and raw results interchangeable | **Watch** — 0B-A lists both; freeze requires residual mention when claiming non-amplitude | Corrected in freeze synthesis statements |
| 8 | Exploratory presented as confirmatory | **Watch** — thirds/path/occlusion must stay exploratory | Enforced in thesis outline §4.5 |
| 9 | Group-level learning effects | **Clear** as decision; wording risk in casual “participants show…” | Freeze uses participant-specific language |
| 10 | Strongest-change ranking vs reliability ranking | **Documented tension** (see Amendment A) | Clarified below; GO_NO_GO not rewritten |

---

## Amendment A — Participant emphasis (GO_NO_GO vs Stage 0B-A)

**Historical text** (`reports/GO_NO_GO_DECISION.md` Q2):  
“252 and 651 are most consistently reliable; 671 and 790 fail more often…”

**Later Stage 0B-A / accepted conclusions:**  
Strongest *interpretable change* profiles: **651 and 790**; **252** mainly T1→T3; **671** limited.

**Resolution (not a silent rewrite):** Both statements can be true under different metrics:
- **Endpoint skill reliability:** 252 (6/6/6) and 651 (5/6/6) are strongest; 790 (4/4/5) intermediate; 671 (3/6/2) weakest.
- **Change magnitude + feature interpretability after gating:** 651/790 lead; 252’s D12 is ≤Drep despite perfect gates; 671 remains limited.

**Canonical freeze wording:** report both dimensions; do not equate “most reliable endpoints” with “strongest adaptation narrative.”

---

## Amendment B — Filename expectations vs on-disk artifacts

| Expected in brief | Actual artifact |
|---|---|
| `feature_change_summary.csv` | `outputs/stage0b_individual_profiles/recording_feature_changes.csv` (+ `exercise_feature_changes.csv`) |
| `segmentation_map.json` | `outputs/stage0b_guided_closeout/guided_segmentation.csv` |

No scientific contradiction; inventory updated accordingly.

---

## Amendment C — “Primary representation” phrase

S6B/S7 say Conv is the primary *downstream latent* representation for gated change detection.
Accepted freeze hierarchy: **explicit features are primary for scientific interpretation**;
Conv is primary as **detector/localizer**. Freeze synthesis uses this hierarchical hybrid wording
to avoid implying Conv alone is the scientific outcome.

---

## Corrections applied in freeze package (only)

- Created consolidated `GUIDED_ANALYSIS_*` reports with hierarchical hybrid framing.
- Participant synthesis table separates reliability vs change>Drep vs feature support.
- Thesis outline marks temporal/region analyses exploratory.
- Reproducibility manifest records missing git commit as documentation gap.

**No historical `reports/S*` or `reports/STAGE0B_*` files were modified in this freeze stage.**
