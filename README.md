# gaga_shared6d_poc

Stage 0 feasibility experiment: **can a compact shared motion model, operating
on local 6D rotations derived from the original quaternion data, identify
within-participant differences between T1, T2 and T3, and are the magnitude and
direction of those changes similar across participants?**

This is an exploratory feasibility study with N = 4, intended to inform a
planned N = 50 study. It is **not** designed to demonstrate an intervention
effect or to estimate a population-level effect, and no result from it should
be read that way.

## Standalone by design

This project is self-contained. `../gaga_jcvpca` is treated as **read only**: it
is a source of raw recordings, segmentation workbooks and a trusted cache used
for validation. Nothing in it is modified. Every input is checksummed into
`data/immutable/INPUT_MANIFEST.json` before use.

## Status

| Stage | What it does | Status |
|---|---|---|
| S1 | Ingest, provenance, units, segmentation normalisation | done |
| S2 | 18-link endpoint-relative extraction, validated | done |
| S3 | 6D representation validation | done |
| S4 | Leakage-aware windowing and inventory | done |
| **repro** | **Clean wipe-and-rebuild, content-verified** | **PASSED** (operationally reproducible) |
| **torch** | **Standalone venv, PyTorch 2.13.0, 18/18 smoke checks** | **PASSED** |
| **gate** | **Ready for S5 after review of this status** | **cleared (passed)** |
| S5 | Baselines: PCA, explicit features, conv matched-task | **done — review gate** |
| S6 | Compact transformer, both objectives, 2 folds x 3 seeds | **done — review gate** |
| S7 | Embeddings and within-participant change | **done — review gate** |
| S8 | Direction similarity across participants | **done — review gate** |
| S9 | Controls and interpretability | **done** |
| S10 | Go / no-go decision | **LIMITED GO** |

Read `reports/S5_BASELINE_READINESS_RECOMMENDATION.md` before starting S6.

## Reports

* `reports/GO_NO_GO_DECISION.md` / `STAGE0_FINAL_REPORT.md` - **Stage 0 decision: LIMITED GO**
* `reports/STAGE0B_A2_FINAL_RECOMMENDATION.md` - **guided improvisation closeout**
* `reports/STAGE0B_A2_EVIDENCE_MAP.md` / `STAGE0B_A2_METHOD_COMPARISON.md` / `STAGE0B_A2_PARTICIPANT_SYNTHESIS.md`
* `reports/STAGE0B_A_READINESS_RECOMMENDATION.md` - prior 0B-A gate
* `reports/STAGE0B_A_INDIVIDUAL_PROFILES.md` / `STAGE0B_A_EXERCISE_CONTRIBUTIONS.md` / `STAGE0B_A_FEATURE_INTERPRETATION.md`
* `reports/S9_CONTROLS_AND_COMPARISON.md`
* `reports/S8_READINESS_RECOMMENDATION.md` - prior S8 gate
* `reports/S8_DIRECTION_SIMILARITY_REPORT.md` / `S8_SIGN_FLIP_REFERENCE.md` / `S8_PARTICIPANT_INFLUENCE.md` / `S8_INTERPRETABILITY_REPORT.md`
* `reports/S7_READINESS_RECOMMENDATION.md` - prior S7 gate
* `reports/S6B_CONV_RELIABILITY_GATE.md` / `S7_EMBEDDING_CHANGE_REPORT.md`
* `reports/S6_READINESS_RECOMMENDATION.md` - prior S6 gate
* `reports/S6_TRANSFORMER_TRAINING_REPORT.md` / `S6_OBJECTIVE_SELECTION.md` / `S6_TRANSFORMER_VS_CONV.md` / `S6_RELIABILITY_GATE.md`
* `reports/S5_BASELINE_READINESS_RECOMMENDATION.md` - prior S5 gate
* `reports/S5_PCA_BASELINE_REPORT.md` / `S5_EXPLICIT_FEATURE_REPORT.md` / `S5_MASK_RATIO_SWEEP.md` / `S5_CONV_BASELINE_REPORT.md`
* `reports/S4_READINESS_RECOMMENDATION.md` - prior S4 gate
* `reports/REPRESENTATION_PATH.md` - what the model consumes and where it comes from
* `reports/FILTER_SENSITIVITY_REPORT.md` - direct unfiltered 6D path vs primary (KEEP_PRIMARY)
* `reports/DATA_VALIDATION_REPORT.md` - ingest and extraction (S1-S2)
* `reports/REPRESENTATION_VALIDATION_REPORT.md` - the 6D representation (S3)
* `reports/WINDOW_INVENTORY_REPORT.md` - windowing and leakage controls (S4)
* `reports/REPRODUCTION_REPORT.md` - clean wipe-and-rebuild verification
* `reports/CACHE_INVALIDATION_NOTICE.md` - **binding**: source caches barred from S5-S10
* `reports/ENVIRONMENT.md` - versions, hardware, why CPU not MPS
* `FINAL_METHOD_DECISIONS.md` - methodological decisions fixed before implementation

## Layout

```
configs/
  experiment.yaml          all fixed parameters, pre-registered
  canonical_links_18.yaml  the 18 canonical links, regions, mirror pairs
src/gaga_shared6d/
  motive_io.py             lean bone-only Motive CSV reader
  rotations.py             relative rotations, filtering, 6D, geodesic error
  segmentation.py          workbook normalisation
  provenance.py            checksums, environment, run stamps
scripts/                   s1_ingest, s2_extract, s3_validate_repr, s4_window
data/immutable/            registry, segmentation, INPUT_MANIFEST, extracted rotations
outputs/                   per-stage validation tables and provenance
figures/                   per-stage figures
reports/                   the deliverable reports
```

## Reproducing

Requires the read-only source project at `../gaga_jcvpca`. This project uses
its own environment; `gaga_jcvpca`'s is never modified.

```bash
python3.12 -m venv .venv
./.venv/bin/pip install -r requirements.lock.txt

./.venv/bin/python scripts/s1_ingest.py         # ~5 s, checksums 5.5 GB
./.venv/bin/python scripts/s2_extract.py        # ~50 s, 24 recordings
./.venv/bin/python scripts/s3_validate_repr.py  # ~15 s
./.venv/bin/python scripts/s4_window.py         # ~2 s
```

Each script prints a `PASS` / `BLOCKED` summary and exits non-zero if a gate
fails. To verify the whole thing from a cold start, which wipes every derived
artifact and rebuilds from the raw recordings alone:

```bash
./.venv/bin/python scripts/reproduce_clean.py   # ~80 s
./.venv/bin/python scripts/torch_smoke_test.py  # ~5 s, 18 checks
```

`reproduce_clean.py` compares by **content hash** (numeric arrays, parsed
tables, normalised JSON, decoded pixels), never by file bytes, because Parquet
metadata, JSON run stamps and PNG encoder fields differ legitimately between
two correct runs.

## The representation path

```text
Raw OptiTrack global quaternions          <- source representation
  -> canonical parent-relative quaternions
  -> rotvec                                  <- INTERMEDIATE ONLY: filtering + QC
  -> rotation matrix
  -> 6D                                      <- model input
```

The model input derives from the original quaternion data. The rotation vector
is never the source and never the model input; it exists only so the validated
Butterworth filter can run in tangent space, which is what makes the
bit-identical agreement with the reference implementation possible. Full detail
in `reports/REPRESENTATION_PATH.md`.

## Key design decisions

**Endpoint-relative extraction.** The 18 canonical links are defined by
anatomical endpoints and resolved per recording, so all 24 recordings produce
the same 18 rotations. This reconciles the 51-bone and 55-bone Motive templates
without composing chains, because a parent-relative chain telescopes. Verified
on real data to 3.7e-14 degrees.

This matters more than expected: the skeleton template is **not constant within
a participant**. 651 switches template between T1 and T2, and 671 between T2
and T3. A fixed per-participant link map would change meaning at exactly the
contrast being measured.

**Capture Start Time, never filenames.** `252_T2` is named 2026-04-26 but was
captured 2026-05-19. On filenames its T2 would appear to precede its T1.

**6D as the model I/O representation.** Lossless to float64 (1.2e-15 Frobenius
round trip) and continuous by construction. Stated in balance: **6D did not fix
an observed continuity failure here.** Zero spurious discontinuities were found
in *either* representation, including across all 426 near-pi frames, because at
120 Hz behind a 10 Hz low pass the rotation vector never gets the chance to
wrap. 6D provides a continuous neural-network representation by construction at
negligible cost, which is worth having for a representation meant to outlive
this sampling regime. It is not a repair.

**Source caches are barred from S5-S10.** See
`reports/CACHE_INVALIDATION_NOTICE.md`. They may be read as a validation
reference only.

**Blocks, not windows, are the unit of assignment.** Windows within an exercise
block are correlated, so all splits are at block level.
