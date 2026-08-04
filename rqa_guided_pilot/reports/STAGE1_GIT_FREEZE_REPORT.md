# Stage 1 Git Freeze Report

**Date:** 2026-08-04  
**Local branch at freeze:** `exploratory/guided-rqa-plan`  
**Stage 2 branch (created after freeze):** `exploratory/guided-rqa-stage2`

## Commit and tag

| Item | Value |
|---|---|
| Stage 1 freeze commit | `4ed2305cdf8b1c7eb0f73be722470d92317288f4` (`4ed2305`) |
| Annotated tag | `rqa-stage1-feasibility-pass-v1` |
| Tag points to commit | `4ed2305` |
| Message | RQA Stage 1 technical feasibility pass; parameters locked; Stage 2 not included |

## Scientific freeze (must remain unchanged)

| Item | Value |
|---|---|
| Tag | `guided-analysis-freeze-v1` |
| Commit | `5062e22bfc6df5107153bb37aa39f363fb303597` |
| Verified after RQA tag | **Still `5062e22`** |

## Remote verification

Pushed:

- branch `origin/exploratory/guided-rqa-plan`
- tag `origin/rqa-stage1-feasibility-pass-v1`

`git rev-list -n1 guided-analysis-freeze-v1` → `5062e22…`  
`git rev-list -n1 rqa-stage1-feasibility-pass-v1` → `4ed2305…`

## Included

- `rqa_guided_pilot/` source, configs, tests
- Stage 1 metric tables, locks, T1 diagnostics
- Planning reports, Stage 1 gate/summary/pre-freeze audit
- Manifests (run, input hashes, environment, EXTERNAL_TOUCHES)
- Root `.gitignore` cache ignore entry

## Excluded

- `rqa_guided_pilot/cache/` (empty / gitignored)
- Full recurrence / distance matrices
- Raw OptiTrack / rotvec copies
- PDF paper (untracked)
- Stage 2 code/outputs (**not included** in this freeze)

## Confirmation

Stage 2 was **not** included in `rqa-stage1-feasibility-pass-v1`.
