# Paper code reference audit (Pose-Dynamics)

**Classification:** `NO_MATERIAL_DISCREPANCY_RETAIN_PRIMARY`  
**Primary implementation remains:** `rqa_guided_pilot/src/rqa_pilot`  
**Stage 1 locks:** unchanged (do not retune to match paper defaults)

---

## 1. Execution status

| Question | Answer |
|---|---|
| External code only inspected? | **No — inspected and partially executed** |
| Pose-Dynamics archive wrappers executed end-to-end? | **No** (`rqa/` and `rqa_submodule/` empty) |
| Paper AMI/FNN Python executed? | **Yes** (`state_space_recon.py`) |
| RQA C++ backend fetched, built, pinned, verified? | **Yes** (isolated venv only) |
| Main project environment modified? | **No** |
| Backend vendored/committed into `gaga_shared6d_poc`? | **No** (gitignored cache only) |

Artifacts:

- `rqa_guided_pilot/scripts/paper_code_parity_suite.py`
- `rqa_guided_pilot/outputs/paper_reference/synthetic_parity.json`
- `rqa_guided_pilot/outputs/paper_reference/t1_parity.json`
- `rqa_guided_pilot/manifests/pose_dynamics_reference_manifest.json`

---

## 2. RQA backend presence

In the local archive `rqa_guided_pilot/Pose-Dynamics-main`:

- `src/pose_dynamics/rqa/` — **empty**
- `src/pose_dynamics/rqa_submodule/` — **empty**
- `.gitmodules` points both paths at `https://github.com/xkiwilabs/Recurrence-Quantification-Analysis`

Therefore the paper wrappers in `nonlinear/rqa_utils.py` **cannot run from the archive as shipped**.

Backend was fetched separately into a **gitignored isolated environment**:

| Field | Value |
|---|---|
| URL | `https://github.com/xkiwilabs/Recurrence-Quantification-Analysis.git` |
| Exact commit | `30fddb9a00e6e84837852992df57f244266f5228` |
| Package | `rqa-analysis==1.0.1` |
| License | **Apache-2.0** |
| Install | `rqa_guided_pilot/cache/pose_dynamics_iso_venv` |
| Source clone | `rqa_guided_pilot/cache/pose_dynamics_rqa_backend_ref` |

Claim of “paper RQA executed” applies only to this pinned backend, not to the empty archive submodules.

---

## 3. License status

| Component | License |
|---|---|
| Recurrence-Quantification-Analysis backend | **Apache-2.0** (clear; `LICENSE` present) |
| Pose-Dynamics archive | **Unclear** — no `LICENSE` / `COPYING`; `pyproject.toml` has no license field |

**Unsafe to copy** Pose-Dynamics source into the primary pilot. Use as methodological reference only. Backend may be used for isolated validation under Apache-2.0; do not vendor into this repo without an explicit decision.

---

## 4. Component reusability

### Directly reusable (as reference algorithms / validation oracles)

- Backend `rqa_dist` / `rqa_stats` (Apache-2.0) for **isolated** numerical checks
- Paper AMI / FNN logic in `state_space_recon.py` as a second estimator (not a drop-in replacement)
- Documented embedding orientation: \(X(t)=[x(t), x(t+\tau),\ldots]\) — matches ours

### Methodological reference only

- `config.py` defaults (`eDim=4`, `tLag=15`, `radius=0.15`, `tw=1`, `minl=2`, `rescaleNorm=True`, `pose_fps=30`)
- Mirror-game notebooks (`τ=20`, `m=4`, `FIXED_RADIUS=0.3`, `tw=1`, `minl=4`, z-score, keypoint magnitudes / CRQA)
- Windowing, PCA principal-movement pipelines, dyadic CRQA case studies
- Target-%REC helper `_radius_for_target_recurrence` (max-rescaled quantile path in the wrapper docstring)

### Incompatible with our data representation

- Paper signals: keypoint XYZ magnitudes, OpenPose/ZED pose features, PCA principal movements
- Ours: **regional angular-velocity-magnitude** from OptiTrack rotvec (120 Hz)
- Paper sampling often **30 Hz**; ours locked **120 Hz** with physical-time τ
- Paper examples emphasize **CRQA / multivariate CRQA** between parties; Stage 1 primary is **univariate Auto-RQA** per region

### Unavailable (missing submodules)

- Compiled recurrence engine paths expected by Pose-Dynamics imports
- MATB case-study submodule content

### Unsafe to copy (license unclear)

- Entire Pose-Dynamics Python package / notebooks / pipelines

---

## 5. Convention comparison

### Matched (or effectively aligned)

| Topic | Ours | Paper / backend | Notes |
|---|---|---|---|
| Embedding orientation | `[x(t),…,x(t+(m−1)τ)]` | Same | Matches Takens form in paper docs |
| Embedding length | `N-(m−1)τ` | Same | |
| Pairwise metric | Euclidean in embedded space | Same (C++ `rqa_dist`) | |
| Fixed radius vs mean distance | `ε = 0.35 × mean(d)` after Theiler | Backend `rescale=1`: threshold as fraction of **mean** distance | **Aligned in spirit**; see mean-definition caveat |
| Target RR mode | Quantile of Theiler-excluded distances | Wrapper supports `target_rec` | Comparable when absolute ε shared |
| Lmin default | 2 | Config default 2 (notebooks sometimes 4) | Case-study vs lock |
| Metrics set | RR, DET, Lmean, Lmax, ENTR, LAM, TT | Same family (`perc_recur`, `perc_determ`, …) | Scale: backend % vs our fraction |
| Univariate Auto-RQA | Primary | Supported | |
| NaN handling (series) | Drop/finite-clean longest run | Paper AMI drops non-finite | Similar intent |

### Critical clarification: `rescaleNorm=True` is **not** max-distance `[0,1]` in the backend

Pose-Dynamics docs/comments say `rescaleNorm=True` rescales distances to `[0,1]` by the **maximum**.  
The archive passes `int(params["rescaleNorm"])` into C++. For a Python `bool`, `int(True) == 1`.

Backend C++ (`rqa_utils.cpp`):

- `rescale == 1` → divide by **mean** of all matrix entries (includes diagonal zeros)
- `rescale == 2` → divide by **maximum**
- other → absolute threshold

So paper notebooks with `rescaleNorm=True` and `radius=0.3` are **mean-rescaled**, closer to our `0.35 × mean` than to max-normalized `[0,1]` radius.  
**Do not treat notebook `0.3` and our `0.35` as the same numeric threshold without stating this.**

### Unmatched / case-study-only

| Topic | Ours (locked) | Paper examples | Impact |
|---|---|---|---|
| Sampling rate | 120 Hz | Often 30 fps | Physical time differs if τ frames copied blindly |
| τ | 18 frames = **0.15 s** | e.g. 15–20 frames at 30 Hz ≈ 0.5–0.67 s | Case-study, not our default |
| m | 4 | Often 4 | Same integer; different physical embed span |
| Theiler | `τ` (=18) | Notebooks `tw=1` (backend zeros only main diagonal when `tw=1`) | Large difference if copied |
| Radius lock | 0.35 × **Theiler-excluded mean** | 0.15 / 0.3 with mean rescale (incl. diag zeros in mean) | Near-equivalent class; not identical |
| Target RR | 0.03 (z-score branch) | Optional; not Stage 1 amp-preserving lock | |
| Input norm | Amp-preserving primary; z-score parallel | Default z-score in config/notebooks | |
| Signal type | Regional angular-velocity magnitude | Pose/keypoint/PCA | Incompatible semantics |
| AMI binning | Percentile equal-width-ish quantile edges, fixed 16 bins | Min–max to `[0,1]` + equiprobable bin count ~`1+log2(N)` | Curves correlate on structured signals; τ picks can differ by 1 |
| FNN neighbors | Brute force + **temporal exclusion ±τ** | KDTree, **no** Theiler in FNN; percent false neighbors | Agree on noisy sine; diverge on pure periodic / degenerate |
| Constant signals | AMI/FNN → invalid/NaN | AMI returns zeros; still proposes a lag | Ours more conservative |
| Multivariate | Compact MdRQA on regions | Joint pose dims / CRQA | Different scientific object |
| RR denominator | `(N²−N)`; Theiler cells counted as non-recurrent | Backend `%REC` / `npts` convention | Small RR relative gap (~3%) even when DET matches |

Physical-time interpretation of τ is **explicit in our lock** (`tau_seconds=0.15`). Paper defaults are frame counts at their sampling rate — treat as case-study settings only.

---

## 6. Synthetic parity results

Suite: periodic sine, noisy sine, white noise, constant, structured sequence, full-/block-shuffled variants.  
Params for RQA compare: `τ=18`, `m=4`, `Lmin=2`, Theiler matched as `tw_backend = 19` (`|i−j|≤18`), `radius=0.35` with backend `rescale=1`.

### Qualitative (our implementation)

- PASS: sine DET > white-noise DET  
- PASS: full shuffle reduces sine DET  
- PASS: full shuffle reduces structured DET  
- Constant: near-full recurrence (degenerate attractor) — expected; not used as a Stage 1 DV

### AMI (paper Python vs ours)

- Structured / noisy signals: high curve correlation (e.g. noisy sine ~0.997); first-minimum τ often equal or ±1  
- White / shuffled: low AMI; minima unstable (expected)  
- Constant: ours → no τ; paper → lag with zero AMI  

### FNN

- Noisy sine: near-identical fractions; both choose `m=3`  
- Pure sine / structured: our temporal exclusion can yield NaNs; paper reports a curve — implementation difference, not a Stage 1 retune signal  
- Locked `m=4` came from **real T1** AMI/FNN, not these synthetics  

### Numerical RQA (mean-rescale `r=0.35`)

On sine / noise / structured: **DET, Lmean, Lmax, ENTR, LAM, TT** agree to machine precision or ≪1% relative.  
**RR** differs by ~3% relative (backend mean includes diagonal zeros; RR counting conventions).

Absolute-ε / target-RR check on sine: line statistics (Lmean/Lmax/ENTR) match; RR/DET can differ slightly when recurrence density sits on a steep threshold — still not a lock-changing discrepancy for our T1 regime.

**No tuning** was applied to force agreement.

---

## 7. Limited real-data parity (T1 only)

Executed on 6 cells: `651` T1 R1, ex11/ex13 × `{trunk_spine, left_arm, right_arm}`.

Protocol:

- Identical regional angular-velocity-magnitude series (our loader)  
- `rate=120`, `τ=18`, `m=4`, Theiler matched (`tw=19`), `Lmin=2`  
- Absolute ε = our `0.35 × mean` (Theiler-excluded), backend `rescale=0` with that ε  

Results:

| Metric | Agreement |
|---|---|
| DET, Lmean, Lmax, ENTR, LAM, TT | **Exact match** (within float noise) |
| RR | ~2.5–3.1% relative difference (denominator / counting) |

Same numeric `radius=0.35` with backend mean-rescale (not absolute-ε aligned) gives RR close to ours (~few percent), confirming the **mean-rescale family** equivalence — not max-distance `[0,1]`.

No T2/T3 inspection or optimization.

---

## 8. Discrepancies and likely causes

1. **Docstring vs backend for `rescaleNorm=True`** — bool→`1` means **mean**, not max. Cause: wrapper API vs C++ enum.  
2. **Mean definition** — backend mean over full matrix (diagonal zeros); ours mean over Theiler-finite pairs. Cause: implementation detail → small RR shift.  
3. **Theiler default** — paper notebooks `tw=1` vs our `tw=τ`. Cause: case-study settings.  
4. **AMI/FNN estimators** — binning and FNN neighbor exclusion differ. Cause: independent implementations; τ/m on real data already locked from ours.  
5. **Signal / rate / CRQA focus** — different scientific object. Cause: paper case studies ≠ guided OptiTrack velocity RQA.  
6. **Empty submodules** — archive incomplete for end-to-end Pose-Dynamics RQA. Cause: Git submodule not populated in the copy provided.

None of these imply our DET/LAM/Lmean Stage 1 structure metrics are miscomputed relative to the pinned backend under aligned thresholds.

---

## 9. Stage 1 gate impact

Assessed against possible effects on:

| Decision | Material change? |
|---|---|
| 120 Hz rate | **No** |
| `τ = 18` (0.15 s) | **No** |
| `m = 4` | **No** |
| Radius lock `0.35 × mean` | **No** — backend mean-rescale is the matching family |
| Surrogate disruption | **No** — qualitative ordering preserved |
| `PASS_TO_STAGE2` / freeze validity | **No** |

**Not** `STAGE1_REQUIRES_TECHNICAL_CORRECTION`.

---

## 10. Primary implementation decision

**Retain `rqa_guided_pilot` as primary.**

Use Pose-Dynamics + pinned `rqa-analysis@30fddb9` only as external validation. Do not replace Stage 1 code, do not copy unclear-license sources, do not change locked parameters to match paper notebook numbers.

Include this audit in the Stage 1 freeze documentation set. Proceed by the existing approval sequence (Stage 1 already frozen; Stage 2 already gated `LIMITED_PASS_STOP` — this audit does not reopen Stage 1 locks or authorize Stage 3).

---

## Appendix A — Inspected paths

- `Pose-Dynamics-main/src/pose_dynamics/nonlinear/state_space_recon.py`
- `Pose-Dynamics-main/src/pose_dynamics/nonlinear/rqa_utils.py`
- `Pose-Dynamics-main/src/pose_dynamics/config.py`
- `Pose-Dynamics-main/projects/mirror_game/notebooks/4_rqa_parameter_estimation.ipynb`
- `Pose-Dynamics-main/projects/mirror_game/notebooks/5_recurrence_analysis.ipynb`
- `Pose-Dynamics-main/README.md`, `requirements.txt`, `.gitmodules`, `pyproject.toml`
- Backend: `rqa_analysis/utils/rqa_utils.cpp`, `autoRQA.py`, `LICENSE`, `README.md`
