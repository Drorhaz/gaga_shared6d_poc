# Guided Improvisation RQA Pilot

Dedicated, freeze-safe package for the Recurrence Quantification Analysis feasibility pilot.

## Isolation rules

- All RQA code, configs, tests, reports, outputs, figures, manifests and caches live under `rqa_guided_pilot/`.
- Frozen guided-analysis inputs are read through documented relative paths in `configs/paths.yaml`.
- This package must **not** copy, move, overwrite or modify frozen scientific files outside this directory.
- Tag `guided-analysis-freeze-v1` / commit `5062e22` remain untouched.

## Layout

```text
rqa_guided_pilot/
  src/rqa_pilot/     # library
  configs/           # paths + pilot design
  scripts/           # stage runners
  tests/
  reports/           # planning/ + stage decision reports
  outputs/           # metric tables, locks
  figures/           # selected diagnostics
  manifests/         # run manifests
  cache/             # regenerable distance matrices (gitignored)
```

## Planning documents

See `reports/planning/` for the approved design package.

## Stage 1 entrypoint

```bash
# from repository root
.venv/bin/python rqa_guided_pilot/scripts/run_stage1.py
```

Stage 1 status: see `reports/STAGE1_GATE_REPORT.md` and `reports/STAGE1_IMPLEMENTATION_SUMMARY.md`.

Unit tests:

```bash
.venv/bin/python rqa_guided_pilot/tests/test_rqa_core.py
```

## Interpretation language

Regional Auto-RQA measures recurrence of **regional angular-velocity-magnitude dynamics**, not posture or anatomical pose recurrence.
