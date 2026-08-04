# External touches outside `rqa_guided_pilot/`

This package is required to confine RQA artifacts under `rqa_guided_pilot/`.

## Approved external edit

| Path | Change | Why | Adapter alternative? | Affects frozen results? |
|---|---|---|---|---|
| `.gitignore` | Ignore `rqa_guided_pilot/cache/` and local Python caches | Explicitly requested so large regenerable intermediates are not versioned | Could use a nested gitignore only inside `rqa_guided_pilot/`; root update keeps one project ignore list | **No** — not a scientific output |

## Planning-report relocation

| Action | Detail |
|---|---|
| Moved | `reports/RQA_*.md` → `rqa_guided_pilot/reports/planning/` |
| Why | Prevent RQA planning docs from living in the shared `reports/` tree |
| Affects frozen results? | **No** — these files were new planning docs, not freeze artifacts |

## Not modified

- Tag `guided-analysis-freeze-v1` / commit `5062e22`
- `data/immutable/`, `outputs/s7_conv/`, `outputs/s4_windows/`, Conv checkpoints, explicit-feature outputs
- `src/gaga_shared6d/`, `configs/experiment.yaml`, `configs/canonical_links_18.yaml` (read-only)

No other external scientific file modifications were required. Read-only adapters live in `src/rqa_pilot/io_readonly.py`.
