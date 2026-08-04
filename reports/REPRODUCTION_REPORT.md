# Clean reproduction report (S1-S4)

Produced by `scripts/reproduce_clean.py`. Machine-readable result in
`outputs/reproduction/reproduction_result.json`; per-stage logs in
`outputs/reproduction/logs/`.

**Result: PASSED. The pipeline is scientifically validated and operationally
reproducible.**

Latest verified run (this session): `2026-08-03T16:02:04+00:00`, under
`./.venv` (Python 3.12.12, NumPy 2.5.1, Torch 2.13.0). Machine-readable
result: `outputs/reproduction/reproduction_result.json`.

---

## 1. What was done

1. Every derived artifact was fingerprinted by content: `data/immutable/`,
   `outputs/`, `figures/` - 48 artifacts.
2. All three directories were **moved out of the workspace** into
   `.quarantine/<timestamp>/`, and the workspace was verified to contain no
   derived artifact of any kind. Non-pipeline outputs (`outputs/smoke_test`,
   `outputs/reproduction`) are parked and restored so the wipe does not destroy
   the Torch smoke-test result.
3. S1 to S4 were re-run as fresh subprocesses against nothing but the read-only
   source project `../gaga_jcvpca`. No intermediate from the previous run was
   reachable.
4. The fresh artifacts were fingerprinted and compared against step 1.
5. Ten scientific gates were evaluated on the fresh artifacts.

| Stage | Runtime (latest) |
|---|---|
| `s1_ingest.py` | 4.5 s (includes SHA-256 over 5.51 GB) |
| `s2_extract.py` | 60.2 s |
| `s3_validate_repr.py` | 19.5 s |
| `s4_window.py` | 3.1 s |

---

## 2. Content comparison

| Outcome | Count |
|---|---|
| Identical | **48** |
| Changed | 0 |
| Missing after rerun | 0 |
| New after rerun | 0 |

### Reproduced under two independent interpreters

The wipe-and-rebuild was run twice, once under the source project's
interpreter and once under this project's own `./.venv` after PyTorch was
installed. **All 48 artifacts were content-identical in both runs**, and all
ten gates passed in both.

This is the evidence that the project is genuinely standalone: it does not
depend on anything installed in `../gaga_jcvpca`, which is read for raw data
only.

One difference surfaced on the cross-environment run and was a defect in the
checker rather than in the pipeline: `outputs/smoke_test/torch_smoke_test.json`
was counted as a pipeline artifact and reported missing, because S1-S4
correctly do not regenerate it. Non-pipeline outputs under `outputs/` are now
excluded by name.

### Why content hashes and not file bytes

File-byte comparison would have failed for reasons that have nothing to do with
correctness. Parquet embeds writer version and schema metadata; the provenance
JSON records a UTC run stamp; `extraction_summary.csv` records per-recording
wall-clock runtime; PNG encoders may vary. Each artifact class is therefore
hashed by its content:

| Artifact | Hashed as |
|---|---|
| `.parquet` | numeric columns as raw IEEE-754 bytes, text as values, column order normalised |
| `.csv` | parsed table content, excluding the volatile `seconds` column |
| `.json` | normalised tree with the `utc` key removed |
| `.png` | **decoded pixel array**, so encoder metadata is irrelevant |

Both the 24 rotation Parquet files (390 MB of float64) and all six figures came
back pixel-for-pixel and bit-for-bit identical in content.

---

## 3. Gate results

| # | Gate | Result |
|---|---|---|
| 1 | 24 recordings ordered by embedded `Capture Start Time` | **PASS** - 24 recordings; monotonic T1<T2<T3 for 4/4 participants; 2 filename/capture-date mismatches correctly overridden |
| 2 | Units correct, including the 252-T3 meter/millimetre case | **PASS** - `252_T3_P1_R1` and `252_T3_P1_R2` recorded as Meters, other 22 Millimetres; those two recordings' orientation extraction is still bit-identical to the reference across 32 link-comparisons |
| 3 | The same canonical 18-link space | **PASS** - 18 links configured; every one of 24 recordings yields exactly 18, across both the 51-bone and 55-bone templates |
| 4 | Zero unexplained extraction mismatches | **PASS** - 378 bit-identical, 6 alias-explained, **0 unexplained**, of 384 comparable link-recordings |
| 5 | Telescoping validation result unchanged | **PASS** - 36 checks on 18 recordings, worst 3.735e-14 deg |
| 6 | Exactly 1,657 windows | **PASS** - 842 training, 211 early-stop, 604 evaluation |
| 7 | Zero exercise-boundary crossings | **PASS** - 0 |
| 8 | Zero blocks split across roles | **PASS** - 0 |
| 9 | Zero missing values | **PASS** - 0 windows with non-finite data; minimum per-window finite fraction 1.000 |
| 10 | Identical training and evaluation inventories | **PASS** - `window_index.csv` content hash matches; 23-28 evaluation windows per recording (median 25); fold A 403 train / 120 early-stop, fold B 439 / 91 |

Gate 2 is worth spelling out, because "correct units" means something specific
here. The pipeline operates entirely on bone **orientations**, which are
unitless, so the Meters export cannot affect any rotation. The gate therefore
checks two things jointly: that the deviation is detected and recorded per
recording, and that the orientation extraction for those two recordings is
nonetheless bit-identical to the independent reference. Both hold. The unit
correction matters only for a future positional, bone-length or amplitude
analysis, where it must be applied before use.

---

## 4. Status statement

The project may now be described as:

> **Scientifically validated and operationally reproducible.**

The earlier qualifier - *scientifically validated, but not yet operationally
reproducible* - no longer applies, and was accurate until this run: the previous
artifacts had been built incrementally, with some stages re-run under `--force`
against pre-existing outputs, so nothing had demonstrated that a cold start from
the raw recordings alone lands in the same place.

## 5. Re-running this check

```bash
python scripts/reproduce_clean.py                    # removes quarantine on pass
python scripts/reproduce_clean.py --keep-quarantine  # retains it for inspection
```

Exit code is 0 only if content is identical **and** all ten gates pass. On
failure the quarantined previous artifacts are always retained.
