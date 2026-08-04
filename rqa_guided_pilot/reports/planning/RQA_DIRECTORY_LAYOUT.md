# RQA Directory Layout (implementation amendment)

All RQA work is confined to:

```text
rqa_guided_pilot/
```

Planning reports previously drafted under repository `reports/RQA_*.md` were moved to:

```text
rqa_guided_pilot/reports/planning/
```

Implementation code, Stage 1 outputs, locks, manifests and figures live only under `rqa_guided_pilot/`.

Frozen guided-analysis artifacts remain read-only via relative paths in `configs/paths.yaml`.
