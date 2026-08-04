# Environment

`gaga_shared6d_poc` has its **own** virtual environment at `./.venv`. The
environment of the read-only source project `../gaga_jcvpca` was **not
modified**: no package was installed into it, removed from it or upgraded, and
it shares no site-packages with this project.

Verification that the separation is real: the full S1-S4 pipeline was
reproduced end to end under **both** interpreters, and all 48 pipeline
artifacts came back content-identical in each case. See
`reports/REPRODUCTION_REPORT.md`.

---

## Versions

| Component | Version |
|---|---|
| Python | 3.12.12 (Homebrew `python@3.12`, `3.12.12_1`) |
| NumPy | 2.5.1 |
| SciPy | 1.18.0 |
| pandas | 3.0.3 |
| PyArrow | 24.0.0 |
| Matplotlib | 3.11.0 |
| PyYAML | 6.0.3 |
| openpyxl | 3.1.5 |
| **PyTorch** | **2.13.0** (`torch-2.13.0-cp312-cp312-macosx_14_0_arm64.whl`, 111.2 MB) |

Fully pinned transitive set: `requirements.lock.txt` (27 packages).
Direct dependencies with rationale: `requirements.txt`.

## Hardware and accelerators

| Property | Value |
|---|---|
| Machine | Apple M1 Pro, `arm64` |
| OS | macOS 26.5.2 |
| CPU threads visible to Torch | 8 (smoke test pins 4) |
| CUDA | **not available** - no NVIDIA GPU on this machine |
| Apple MPS | **available and built**, but deliberately unused |

### Why CPU rather than MPS

GPU support is optional for this project and is not used, for two reasons.

1. **Reproducibility outranks speed here.** CPU float32 is deterministic across
   runs given a fixed seed; MPS is not guaranteed to be. The experiment
   promises three fixed seeds per fold and identical results on re-run, and
   that promise is cheaper to keep on CPU.
2. **The workload is tiny.** The model is 31,036 parameters trained on roughly
   400 windows per fold. The smoke test measured **10 ms per optimisation step
   at batch 4** on CPU, so a full training run is a matter of minutes. There is
   nothing for a GPU to save.

If a later stage becomes compute-bound, MPS is present and can be enabled, but
any run used for a reported result must state which device produced it.

## NumPy 2.5 compatibility

Torch 2.13.0 is built against the NumPy 2.x ABI and interoperates cleanly with
NumPy 2.5.1. Verified in the smoke test: `numpy -> torch -> numpy` round trip,
`torch.from_numpy` on float64, and float32 matrix multiplication.

## Setup from scratch

```bash
cd gaga_shared6d_poc
python3.12 -m venv .venv
./.venv/bin/pip install -r requirements.lock.txt   # exact
# or
./.venv/bin/pip install -r requirements.txt        # direct deps only
```

Then verify:

```bash
./.venv/bin/python scripts/torch_smoke_test.py   # 18 checks, ~5 s
./.venv/bin/python scripts/reproduce_clean.py    # full S1-S4 rebuild, ~80 s
```

## Notes for a future machine

* The Torch wheel is macOS arm64. A Linux or CUDA host needs the matching
  wheel; pin the version, not the platform tag.
* `requirements.lock.txt` was produced by `pip freeze` in this venv and
  includes platform-specific builds of `pillow`, `kiwisolver` and `pyarrow`.
* Installing Torch took roughly 22 minutes here, entirely network-bound at
  about 740 KB/s. That is a property of the connection, not of the package.
