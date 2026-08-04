# Git Freeze Report — gaga_shared6d_poc

**Date:** 2026-08-04  
**Purpose:** Preserve the completed guided-improvisation analysis for reproducibility.  
**Scientific status:** No analyses were rerun, models retrained, or scientific conclusions altered.

---

## 1. Repository name and visibility

| Field | Value |
|---|---|
| Repository name | `gaga_shared6d_poc` |
| Local branch | `main` |
| Intended GitHub visibility | **private** |
| GitHub remote created in this step | **Yes** — empty repo provided by user; push completed 2026-08-04 |

## 2. Remote URL

https://github.com/Drorhaz/gaga_shared6d_poc.git

**Visibility note:** GitHub currently lists this repository as **Public**. Prefer switching to **Private** if participant-linked research materials should not be world-readable.

## 3. Commit hash

`5062e22bfc6df5107153bb37aa39f363fb303597` (`5062e22`)

## 4. Freeze tag

`guided-analysis-freeze-v1`  
Message: *Frozen guided-improvisation analysis: thesis-ready scientific results with reproducibility manifests. No free-movement analysis included.*

## 5. Included artifact categories

- Source code (`src/`, `scripts/`)
- Configurations (`configs/`)
- Method decisions and README
- All Stage 0 / 0B / guided-analysis reports under `reports/`
- Lightweight final tables and JSON gates under `outputs/` (except ignored logs)
- Conv and Transformer checkpoints (≈60–135 KB each)
- Figures including `figures/guided_analysis_thesis_selected/`
- Provenance manifests and registries under `data/immutable/` (rotvec arrays excluded)
- `requirements.txt` / `requirements.lock.txt`
- Excluded-artifact checksum manifest
- `.gitignore`

## 6. Excluded artifact categories

- `.venv/` (~1.1 GB)
- `data/immutable/rotvec_18link/` (~400 MB regenerable; hashes in `outputs/guided_analysis_finalization/excluded_artifacts_manifest.csv`)
- Raw OptiTrack / skeleton CSV sources (never stored in this project; live under sibling `../gaga_jcvpca`)
- Run logs (`outputs/*_run_log.txt`, `**/run_log.txt`, `outputs/reproduction/logs/`)
- OS/IDE caches, bytecode, `.quarantine/`
- Secrets / env files (none present)

## 7. Large-file and LFS decisions

| Threshold | Finding | Decision |
|---|---|---|
| >10 MB | Only rotvec parquets (~15–16 MB × 24) | **Excluded** (regenerable) |
| >50 MB | None outside `.venv` | n/a |
| >100 MB | None outside `.venv` | n/a |
| Checkpoints | 60–135 KB | **Committed directly** (no LFS) |
| Git LFS | Not installed | **Not configured** (would affect billing/storage); not required |

## 8. Sensitive-data checks

- No participant names, emails, questionnaire/MRI payloads, or credentials found in staged files.
- Study IDs (252, 651, 671, 790) retained where scientifically necessary.
- Absolute local filesystem paths rewritten to relative forms (`../gaga_jcvpca`, `.`) in provenance/manifest text before commit; see `outputs/guided_analysis_finalization/PATH_SANITIZATION.md`.
- No identifying lookup table committed.

## 9. Remaining manual action (GitHub)

Push completed to the user-provided empty repository.

Recommended follow-up if privacy is required:

```bash
# In GitHub UI: Settings → General → Danger Zone → Change repository visibility → Private
# or, if gh is installed:
gh repo edit Drorhaz/gaga_shared6d_poc --visibility private
```

## 10. Confirmation

- Working tree freeze commit represents the completed guided-improvisation scientific state.
- No free-movement, transfer, RQA, clustering, motif, or new training work was started.
- Scientific numerical outputs were not regenerated for this Git freeze.


---

## Verification (local)

```text
git status          # clean after hash-doc commit
git log -1 --oneline
git tag --list
git rev-list -n1 guided-analysis-freeze-v1
# tag target: 5062e22bfc6df5107153bb37aa39f363fb303597
```

GitHub push completed: `main` and `guided-analysis-freeze-v1` on https://github.com/Drorhaz/gaga_shared6d_poc.git
