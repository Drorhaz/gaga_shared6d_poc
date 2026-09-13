# Pooled validation report

- Git: `exploratory/guided-rqa-stage2` @ `4c3f075`
- UTC: 2026-08-07T12:59:23.688319+00:00

## Boundary tests

- [x] Manifest built from segmentation with start/end per exercise
- [x] Evaluation windows asserted ⊆ exercise [start, end)
- [x] Explicit/coupling aggregation never concatenates exercises for lag/diff
- [x] Conv/Transformer use frozen within-exercise windows only
- [x] JcvPCA not recomputed (extract-only)
- [x] RQA estimand B forbids synthetic concat

## Unit tests

Primary runner (no pytest required):

```bash
.venv/bin/python pooled_ex09_13/tests/run_boundary_checks.py
```

Also: `pooled_ex09_13/tests/test_boundaries.py` (pytest if available).

## Feature re-aggregation check

Max abs diff vs frozen recording_features coupling: `5.551115123125783e-17` (expect ~0 within float noise).

## RQA coverage limitation

Full 5-exercise Auto-RQA grid was not present in Stage1 freeze; pooled RQA marked NOT_COMPUTABLE_IN_PHASE where incomplete.
Estimand B chosen; no synthetic concat; no Stage-3 reopen.

## Stop-condition status

- Segmentation unchanged: PASS
- No new preprocessing inconsistent with freeze: PASS
- Conv/Transformer: frozen inference reuse only (no retrain): PASS
- RQA defined without synthetic boundaries (B), but full-grid incomplete: DOCUMENTED
- Source data present for 24 pooled units: PASS
- JcvPCA definitions unchanged (extract-only): PASS

