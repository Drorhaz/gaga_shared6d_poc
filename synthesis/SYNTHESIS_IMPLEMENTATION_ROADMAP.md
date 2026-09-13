# Synthesis implementation roadmap (post-audit)

**Phase completed:** scientific synthesis documents under `gaga_shared6d_poc/synthesis/`  
**Locked decisions:** `XCORR_OPTIONAL_BACKUP_ONLY`; A3 not formally supported; D12 primary; no new compute in this phase  
**Literature:** `CHANG_PAPER_IMPACT_REVIEW.md` → `ROADMAP_MINOR_UPDATE`

---

## Deliverables checklist

| File | Status |
|---|---|
| `CHANG_PAPER_IMPACT_REVIEW.md` | Done |
| `JCVPCA_EVIDENCE_HIERARCHY_AUDIT.md` | Done |
| `EXISTING_ANALYSIS_AUDIT.md` | Done |
| `R1_R2_COMMON_FRAMEWORK.md` | Done |
| `CROSS_CORRELATION_EXISTING_WORK_AUDIT.md` | Done |
| `CROSS_CORRELATION_FEASIBILITY.md` | Done |
| `CROSS_METHOD_CONSTRUCT_MAP.md` | Done |
| `CROSS_METHOD_PARTICIPANT_MATRIX.md` | Done (populated) |
| `CROSS_METHOD_PARTICIPANT_MATRIX.csv` | Done (populated) |
| `SCIENTIFIC_CLAIM_LADDER.md` | Done |
| `PRESENTATION_RECOMMENDATION.md` | Done |
| `SYNTHESIS_IMPLEMENTATION_ROADMAP.md` | Done (this file) |

---

## Remaining work classification

### ALREADY_AVAILABLE

No new scientific computation required for thesis-result packaging of the core story:

- Marker-gap JcvPCA A2/S3/coverage/persistence/Step-5 results
- Conv reliability + D12/D13 change vs Drep + exercise localization
- Explicit feature exceedances + amp residuals
- RQA Stage 2 gate + two complementary cells
- Transformer vs Conv architecture decision
- PCA identity reference
- Populated cross-method matrix and claim ladder

### MISSING_BUT_NECESSARY

Only packaging / governance items — **not new analyses**:

1. **Supervisor sign-off** on NV wording / A3 scope (`SUPERVISOR_NV_DECISION.md` still pending) before any A3 sentence in the thesis.
2. **Figure assembly** from existing slide45 / supervisor figure packs into final thesis layouts (Figure 1–3 specs in `PRESENTATION_RECOMMENDATION.md`).
3. **Stale-document hygiene** (optional but recommended): mark July-18 supervisor packs / `METRICS_DIGEST` S3 table as superseded — documentation only, not recompute.

### OPTIONAL

Useful but not required for core conclusions:

- Approved minimal cross-correlation (`XCORR_OPTIONAL_BACKUP_ONLY`) **if** a safe signal representation is later specified — currently **not** necessary.
- Expanded D13 supplemental figure pack with coverage banners.
- Per-exercise Layer-2 JcvPCA displays (firewalled from A2 gate).
- Deeper feature×exercise heatmaps for 651/790.

### NOT_RECOMMENDED

- RQA Stage 3 / reopen novelty gate
- Retrain Conv or Transformer
- Anatomical Cardan reconstruction from current rotvecs for Chang claims
- Free-movement analysis, clustering, motifs
- Treating methods as votes or equating Drep numerics across methods
- Causal Gaga / psilocybin claims
- Merging exploratory branches to `main` as part of this synthesis

---

## Final cross-correlation class

`XCORR_OPTIONAL_BACKUP_ONLY` — unchanged after literature review and evidence matrix population.

---

## Stop

Synthesis phase complete. Await separate approval before any new computation.
