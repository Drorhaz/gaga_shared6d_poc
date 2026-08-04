# Guided Analysis — Reproducibility Manifest

**Date of freeze:** 2026-08-04  
**Outcome:** GUIDED RESULTS FROZEN WITH DOCUMENTATION GAPS  
**Project root:** `.`

## Version control

| Field | Value |
|---|---|
| Repository name | `gaga_shared6d_poc` |
| Git repository present | **Yes** (local freeze; GitHub push pending `gh` auth) |
| Branch | `main` |
| Freeze commit | `5062e22bfc6df5107153bb37aa39f363fb303597` |
| Freeze tag | `guided-analysis-freeze-v1` |
| Git freeze date | 2026-08-04 |
| Dependency lock file | `requirements.lock.txt` |
| Scientific freeze status | GUIDED RESULTS FROZEN WITH DOCUMENTATION GAPS (science complete; prior gap was missing VCS) |
| Known documentation limitations | GitHub remote not created in this step (`gh` not installed); absolute local paths sanitized to relative forms for privacy |

### Git freeze notes (appended 2026-08-04)

- **Included:** source (`src/`, `scripts/`), configs, reports (including `GUIDED_ANALYSIS_*`), lightweight final tables under `outputs/`, figures (including thesis-selected), Conv/Transformer checkpoints (≤135 KB each), `requirements.lock.txt`, decision logs, excluded-artifact checksums.
- **Excluded:** `.venv/`, `data/immutable/rotvec_18link/` (~400 MB regenerable), run logs, OS/IDE caches, raw OptiTrack sources (never stored here).
- **LFS:** not used (Git LFS not installed; no artifact required LFS).
- **Path privacy:** absolute `/Users/…` prefixes in provenance/manifest text rewritten to `../gaga_jcvpca` or `.`; checksums and scientific conclusions unchanged.
- Excluded regenerable arrays: `outputs/guided_analysis_finalization/excluded_artifacts_manifest.csv`.

## Environment

| Package | Version |
|---|---|
| Python | 3.12.12 |
| Platform | macOS-26.5.2-arm64-arm-64bit |
| torch | 2.13.0 |
| numpy | 2.5.1 |
| scikit-learn | 1.9.0 |
| scipy | 1.18.0 |
| pandas | 3.0.3 |
| PyYAML | 6.0.3 |

Lockfile: `requirements.lock.txt` (also `requirements.txt`).

## Model / analysis freeze parameters

- **Model:** ConvMaskedPredictor
- **Objective:** masked_angular_velocity
- **Mask ratio:** 0.3 (frozen after S5 sweep)
- **Embedding:** deterministic 32-D mean-pool
- **Seeds:** [0, 1, 2]
- **Folds:** A (train R1 / traj R2), B (train R2 / traj R1)
- **Evaluation exercises:** ex09–ex13
- **Reliability gate:** skill > 0 at relevant endpoints (see `outputs/s7_conv/RELIABILITY_GATE.json`)
- **Drep:** within-session R1/R2 embedding distance reference
- **Standardizer:** training-T1-only balanced; params in `outputs/s7_conv/standardizer_params.json`
- **Skeleton / links:** `configs/canonical_links_18.yaml` + `configs/experiment.yaml`

## Selected checkpoints (velocity Conv)

- `outputs/s5_conv/checkpoints/A_masked_angular_velocity_s0.pt` — `08cc9e9c8a685663…`
- `outputs/s5_conv/checkpoints/A_masked_angular_velocity_s1.pt` — `d210661f8d2b8c2d…`
- `outputs/s5_conv/checkpoints/A_masked_angular_velocity_s2.pt` — `902621853ec9100f…`
- `outputs/s5_conv/checkpoints/B_masked_angular_velocity_s0.pt` — `b301a28b0236c63f…`
- `outputs/s5_conv/checkpoints/B_masked_angular_velocity_s1.pt` — `be067bcf02dbee8b…`
- `outputs/s5_conv/checkpoints/B_masked_angular_velocity_s2.pt` — `2c13f482282374bf…`

(Also retain failed/non-selected `masked_6d` checkpoints for negative-result reproducibility; do not delete.)

## Critical output hashes (SHA-256)

- `configs/experiment.yaml`: `18ada6ffb21cb627278844672e672a0bb07234034902e42b62ef557b8525af2a`
- `configs/canonical_links_18.yaml`: `4ca8be22f2742e3db4019cc2214cff2dc1543d8a474d34571dffe58881643c58`
- `outputs/s7_conv/reliability_t1_t2_t3.csv`: `db18e19b6fc92fbafc969b7efe95640bac86ed30cec01ed8fceb2ba345c17190`
- `outputs/s7_conv/change_magnitudes.csv`: `634963879921e7e9c3b8013bff70d05e8a598ffcd8a15fda9760ef9e58ba7749`
- `outputs/s7_conv/window_embeddings.parquet`: `0e1788c826d4cd692f9a9507e8ff2711206e171407ae87646a6bca1353c5f6e7`
- `outputs/s7_conv/RELIABILITY_GATE.json`: `acb8d3e85f9ce98f9730ab2e141972abe1c16c4cc37da0f476cdeb4a18962233`
- `outputs/s7_conv/standardizer_params.json`: `32d9b410594d949967842392c9549915a0df949ed900aa2fb2fabc87abb5ff60`
- `outputs/s8_direction/S8_GATE.json`: `8926f46eaa287877a3f1d0ceb11322c991201d9fefe4d7f919857279b985f707`
- `outputs/s8_direction/pairwise_cosines.csv`: `4113b94733907156fe9d68f228e65d21a634c0220114c406642945d6ea159e3e`
- `outputs/s8_direction/jackknife.csv`: `dd8997a3d9807976974f2796d4827da3070bdfe1ef4e41ca26fca38d6f74c0c7`
- `outputs/s9_final/GO_NO_GO.json`: `2a348047fa2a5b9e3e7189980bfbf818a5a12cc73591228e0a7bec236dc8a3c5`
- `outputs/stage0b_individual_profiles/individual_profiles.csv`: `f224fca42ae289d7d879bc90d4408d5e04aea5a1150b0abceb5f6f89879a7a64`
- `outputs/stage0b_individual_profiles/recording_feature_changes.csv`: `d15f0da0244a41f7e038e6dcb407899e2b73d017e5c62c79de63a05c7bd7f85b`
- `outputs/stage0b_individual_profiles/exercise_contributions.csv`: `8f69f29d92d922a5b77e1460fe48dd192f9401f1a632c7c4c165c8e8efff7036`
- `outputs/stage0b_guided_closeout/exercise_level_change.csv`: `3d4495b72005a045e7738d35a679ca5d7d1f91962d3fdcd8de3938624e4dc116`
- `outputs/stage0b_guided_closeout/repertoire_summary.json`: `bbd04e2c9c8abcbe2e6a88967cb055f176d9a0fced4c66a8b8e9510a109cdb61`
- `outputs/stage0b_guided_closeout/guided_segmentation.csv`: `fbbff1aac3c0392db2e2dae2f00dd0a8cc20dabbb942692d48d867e570bad541`
- `outputs/stage0b_guided_closeout/temporal_dynamics.csv`: `b048984ad4362896ab81a207f5745fc2a2d07f613462669afa05658f50650db2`

## Inclusion tables

- Reliability cells: `outputs/s7_conv/reliability_t1_t2_t3.csv`
- S8 inclusion: `outputs/s8_direction/inclusion_table.csv`
- Participant synthesis: `outputs/guided_analysis_finalization/participant_synthesis_table.csv`

## Figure- and report-generation scripts

| Stage | Script | Reports |
|---|---|---|
| S5 Conv/PCA/explicit/mask | `scripts/s5_*.py` | `reports/S5_*` |
| S6 Transformer | `scripts/s6_transformer.py` | `reports/S6_*` |
| S7 embeddings/change | `scripts/s7_conv_embeddings_change.py` | `S6B_*`, `S7_*` |
| S8 direction | `scripts/s8_direction_similarity.py` | `S8_*` |
| S9/S10 GO/NO-GO | `scripts/s9_s10_final.py` | `S9_*`, `STAGE0_FINAL_*`, `GO_NO_GO_*` |
| Stage 0B-A | `scripts/stage0b_a_individual_profiles.py` | `STAGE0B_A_*` |
| Stage 0B-A2 | `scripts/stage0b_a2_guided_closeout.py` | `STAGE0B_A2_*` |
| This freeze | packaging run 2026-08-04 | `GUIDED_ANALYSIS_*` |

## Source-data paths

Configured via `configs/experiment.yaml` → `source_project: "../gaga_jcvpca"` (read-only sibling).
Do not modify `gaga_jcvpca` for reproduction of this freeze.

## Known data exceptions

Retain as documented in Stage 0 data validation / decision log (units for 252-T3, unmarked
boundary merge for 790-T1-R1 ex04/ex05, marker/template notes for 651/671, etc.).
See `reports/DATA_VALIDATION_REPORT.md` and `reports/DECISION_LOG.md`.

## Immutability policy

- Do not overwrite files under `outputs/s5_*` … `outputs/stage0b_*` used by this freeze.
- Thesis figure copies under `figures/guided_analysis_thesis_selected/` are snapshots; regenerate
  only into that folder from originals.
- Intermediate outputs required for reproduction must be retained (not deleted).
- Free-movement / transfer analyses are **not authorized** by this freeze.

## Machine-readable freeze summary

`outputs/guided_analysis_finalization/freeze_summary.json`
