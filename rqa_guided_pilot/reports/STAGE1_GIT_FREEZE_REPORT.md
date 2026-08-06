# Stage 1 Git Freeze Report

**Date:** 2026-08-06  
**Branch:** `exploratory/guided-rqa-plan`  
**Primary feature:** A1 regional angular-velocity magnitude  
**Stage 2:** not included in this freeze

## Commit and tag

| Item | Value |
|---|---|
| Annotated tag tip | `dd345bac487d72e8d1c6ef6c19a170d9c2e3e145` (`dd345ba`) |
| Content freeze commit | `09951ada359efd1c7b9f543313a0a9bce082afe5` (`09951ad`) |
| Annotated tag | `rqa-stage1-feasibility-pass-v1` → tip `dd345ba` |
| Tag message | RQA Stage 1 technical feasibility pass; A1 validated; parameters locked; Stage 2 not included |

**Note:** An earlier technical freeze existed at `4ed2305`. This freeze supersedes that tag object to include required paper-code and source/feature audits completed after the initial parameter lock. Scientific Stage 1 metrics and locks are unchanged.

## Scientific freeze (must remain unchanged)

| Item | Value |
|---|---|
| Tag | `guided-analysis-freeze-v1` |
| Commit | `5062e22bfc6df5107153bb37aa39f363fb303597` |
| Verified | **Still `5062e22`** — not moved or retagged |

## Pre-freeze verification checklist

| # | Check | Status |
|---|---|---|
| 1 | Stage 1 approved for freeze | `STAGE1_FREEZE_APPROVED_WITH_DOCUMENTATION_FIXES` |
| 2 | A1 validated primary | `CURRENT_FEATURE_VALID_ADD_SECONDARY_LATER` |
| 3 | No T2/T3 parameter shopping | Confirmed in pre-freeze audit |
| 4 | Paper code not vendored | `Pose-Dynamics-main/` gitignored; not committed |
| 5 | Backend commit + license documented | `30fddb9…` Apache-2.0 in paper-code manifest |
| 6 | Frozen inputs read-only | `io_readonly` + paths.yaml |
| 7 | No raw OptiTrack / rotvec copies added | Yes |
| 8 | Cache / heavy artifacts ignored | `rqa_guided_pilot/cache/` ignored |
| 9 | Unit tests pass | 5/5 |
| 10 | Working tree explained | Only approved freeze files staged |
| 11 | `guided-analysis-freeze-v1` → `5062e22` | Verified |

## Included

- `rqa_guided_pilot/` Stage 1 source, configs, tests
- Stage 1 / T1 metric tables and `outputs/locks/parameter_lock_stage1.json`
- Planning reports under `reports/planning/`
- `STAGE1_GATE_REPORT.md`, `STAGE1_IMPLEMENTATION_SUMMARY.md`, `STAGE1_PRE_FREEZE_AUDIT.md`
- `PAPER_CODE_REFERENCE_AUDIT.md`, `SOURCE_DATA_AND_FEATURE_AUDIT.md`, `FEATURE_REPRESENTATION_DECISION.md`
- Manifests: run, input hashes, environment, EXTERNAL_TOUCHES, paper-code, source-data/feature
- Lightweight audit outputs: `outputs/paper_reference/`, `outputs/feature_audit/`
- Audit scripts: `paper_code_parity_suite.py`, `feature_representation_audit.py`
- Root `.gitignore` updates (cache, Pose-Dynamics archive, PDFs)

## Excluded

- `rqa_guided_pilot/cache/` (incl. isolated venvs, backend clone, position caches)
- `rqa_guided_pilot/Pose-Dynamics-main/`
- Full pairwise distance / RP matrices
- Raw OptiTrack / `data/immutable/rotvec_18link/`
- Conv / Transformer / unrelated scientific outputs
- Stage 2 code, outputs, and reports

## Locked A1 parameters

- 120 Hz; τ=18 (0.15 s); m=4; radius 0.35×mean; block shuffle 0.30 s

## Remote verification

Pending push of branch + annotated tag in this session.

## Confirmation

- Stage 2 was **not** included in this freeze.
- Original guided-analysis freeze `guided-analysis-freeze-v1` @ `5062e22` was **untouched**.
