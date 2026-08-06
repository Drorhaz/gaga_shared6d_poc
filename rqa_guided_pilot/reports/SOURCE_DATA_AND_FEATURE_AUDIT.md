# Source data and feature-representation audit

**Date:** 2026-08-04  
**Scope:** T1-only technical + scientific feature audit before Stage 1 freeze  
**Decision file:** `FEATURE_REPRESENTATION_DECISION.md`  
**Classification:** `CURRENT_FEATURE_VALID_ADD_SECONDARY_LATER`  
**Stage 1 technical correction:** **No**

All frozen Project A inputs remained read-only. Diagnostics wrote only under `rqa_guided_pilot/outputs/feature_audit/`.

---

## 1. Source files inspected

| Location | Role |
|---|---|
| `../gaga_jcvpca/data/raw_skeleton/{252,651,671,790}/*.csv` | Motive solved-skeleton exports (quats + bone positions) |
| `../gaga_jcvpca/configs/paths.yaml`, `body_regions.yaml` | Sibling path registry / legacy regions |
| `../3Layers_project/Layer2_Motive_Kinematics/` | Original Layer-2 relative-quat → rotvec → Butterworth pipeline |
| `data/immutable/rotvec_18link/*.parquet` | Frozen 18-link filtered rotvecs (rad) |
| `data/immutable/INPUT_MANIFEST.json` | Units, skeleton variant, checksums |
| `outputs/s4_windows/window_index.csv` | Exercise segmentation windows |
| `configs/canonical_links_18.yaml`, `configs/experiment.yaml` | Link/region map; filter specs |
| `src/gaga_shared6d/{motive_io,rotations,explicit_features,data_windows}.py` | Extraction + speed definition |
| `rqa_guided_pilot/src/rqa_pilot/signals.py` | RQA regional speed |
| `rqa_guided_pilot/Pose-Dynamics-main/` | Paper velocity / RQA input path (read-only) |
| `reports/REPRESENTATION_PATH.md` | Prior representation documentation |

**Path note:** Layer2 lives at `projects/3Layers_project/`, not under `gaga_jcvpca/`.

---

## 2. Units and coordinate frames

| Quantity | Unit / frame |
|---|---|
| Motive bone quaternions | Dimensionless, SciPy `[x,y,z,w]`, **Coordinate Space=Global** |
| Parent-relative link orientation | Local link frame via \(q_\mathrm{rel}=\mathrm{inv}(q_p)\,q_c\) |
| Stored rotvec | **Radians** (axis-angle vector) |
| Regional angular speed (A1/A2) | **Degrees/s** |
| Bone positions | Motive Length Units: T1 all **Millimeters**; only `252_T3` is **Meters** |
| Positional speeds in this audit | **m/s** after `/1000` for mm exports |
| Capture rate | **120 Hz** (all takes) |

Rotations are **unaffected** by Length Units. Positional amplitudes are not. Marker pipeline `skeleton_marker_to_meters` also applies an axis permutation in the mm branch; this audit scaled bone positions by 1000 only (no marker remap).

---

## 3. Raw → RQA transformation chain

```
Motive CSV (global bone quaternions @ 120 Hz)
  → resolve 18 endpoint bone pairs (canonical_links_18.yaml)
  → q_rel = inv(q_parent_global) * q_child_global
  → quaternion sign continuity along time (dot < 0 → flip)
  → rotvec = Log_SO(3)(q_rel)   [radians]
  → invalid quats → NaN; QC near-π / jump flags
  → zero-phase Butterworth LP order 4, cutoff 10 Hz on rx,ry,rz
  → immutable parquet rotvec_18link/{recording_id}.parquet
  → slice [start_frame:end_frame] from window_index / segment index
  → link speed: degrees(||r[t+1]-r[t]||) * fps     [A1]
  → regional nanmean over links in region
  → finite_clean (longest finite run)
  → optional integer downsample (no re-filter)
  → amp-preserving or trial z-score
  → delay embed → distance matrix → Theiler → threshold → RQA metrics
```

**Filter vs differentiate:** filtering is on rotvec **before** speed; RQA downsample does not re-filter.  
**Segment boundaries:** speed uses only frames inside the sliced segment (`diff` within slice); no cross-segment derivative.

---

## 4. Exact current angular-speed formula (A1)

Answers:

1. **Yes** — speed is from **parent-relative** (endpoint-relative) joint orientations stored as rotvecs.  
2. **Not explicitly** `q(t)^{-1} q(t+1)` at the speed step — that geodesic is A2.  
3. **Yes** — current code is \(\|\mathbf{r}(t+1)-\mathbf{r}(t)\|_2 \cdot f_s\) then degrees:  
   `norm(diff(rotvec)) * fps` with `np.degrees`.  
4. **Yes** — sign continuity on relative quaternions before log-map (`apply_sign_continuity`).  
5. **Yes** — consistent local link frame via global parent/child composition; SciPy convention fixed.  
6. **Degrees/s** for the RQA series (rotvec storage is radians).  
7. **Differentiation after filtering** (filter on rotvec, then FD).  
8. **Yes** — segment slice first; no cross-boundary FD.  
9. Invalid quats → NaN in rotvec; regional `nanmean`; `finite_clean` keeps longest finite run.  
10. Regions from `canonical_links_18.yaml`; `nanmean` over member links.  
11. **Yes, unequal link counts** (arms 4, legs 3, trunk_spine 2, head_neck 2) → equal weight **per link**, so multi-link regions are not equal-weight per anatomical “segment length.” Documented; not a Stage 1 gate failure.  
12. **651/671 template changes** alter which intermediate bones exist (51 vs 55). Endpoint-relative `Ab_to_Chest` / `Neck_to_Head` still defined, but **anatomical composition** of spanning links differs across templates. Within **T1**, each participant is internally consistent (651/671 T1 = 51-bone). Longitudinal T2/T3 template shifts remain a known confound for later stages, not a T1 A1 invalidation.

\[
s_{\mathrm{region}}(t)=\frac{1}{|L_r|}\sum_{\ell\in L_r}
\frac{180}{\pi}\,\|\mathbf{r}_\ell(t+1)-\mathbf{r}_\ell(t)\|_2\cdot f_s
\]

Code: `explicit_features._link_speed` ≡ `rqa_pilot.signals.link_speed_deg_s`.

---

## 5. Quaternion-geodesic comparison (A2)

**Definition (A2):** from consecutive **filtered** link rotvecs,

\[
\omega = \frac{180}{\pi}\,\mathrm{angle}\big(R(t)^{-1} R(t+1)\big)\cdot f_s
\]

with `Rotation.from_rotvec` / `.magnitude()` (shortest geodesic on SO(3)).

### Aggregate (T1, all 4 participants, ex09–13 segments, all 18 links)

| Statistic | Value |
|---|---|
| n (frame×link) | 850 320 |
| median \|A1−A2\| | **0.060 deg/s** |
| median relative \|A1−A2\|/max(|A1|,|A2|) | **0.19%** |
| p95 abs / p99 abs | 10.7 / 34.9 deg/s |
| max abs | 285 deg/s (rare) |
| correlation | **0.998** |
| frac \|Δ\| > 10 deg/s | 0.95% |
| frac \|Δ\| > 50 deg/s | 0.011% |

Largest residuals: forearm links (`LUArm_to_LFArm`, `RUArm_to_RFArm`) where ‖rotvec‖ is often large → Euclidean chord in rotvec space ≠ SO(3) geodesic. Trunk/leg links: near-exact (median abs ≪ 0.1 deg/s, corr ≈ 1).

**Near-π / wrapping:** max filtered angle ≈ 3.33 rad; fraction > 0.9π ≈ 5×10⁻⁵. Not a systemic wrapping epidemic.

**Segment boundaries:** boundary vs interior median abs similar (0.034 vs 0.060); not boundary-driven.

**Downsample:** trunk regional A1↔A2 corr ≈ 1.0 at 120/60/30 Hz.

### Limited RQA (T1, 4 pids × ex11/13 × trunk/L/R arm, locked τ=18,m=4,r=0.35)

| Metric | median \|A1−A2\| | median rel | corr |
|---|---|---|---|
| DET | 0.00070 | 0.07% | 0.994 |
| LAM | 0.00033 | 0.03% | 0.990 |
| Lmean | 0.047 | 0.87% | 0.997 |
| RR | 0.00042 | 1.3% | 0.993 |
| ENTR | 0.015 | 0.44% | 0.997 |
| DET shuffle drop | 0.00087 | 0.10% | 0.995 |

Both: median AMI τ = **18**, FNN m = **4**; median R1/R2 \|ΔDET\| ≈ 0.014; strong surrogate DET drop ≈ 0.92.

**Decision rule:** agree sufficiently + same technical conclusion → **retain A1**. A2 = validation / sensitivity reference, not Stage 1 replacement.

---

## 6. Paper velocity definition

From Pose-Dynamics (`linear_features.py`, mirror-game README/notebooks):

| Aspect | Paper practice |
|---|---|
| Source | Markerless 2D/3D **keypoint positions** (OpenPose / ZED), not OptiTrack joint rotations |
| Linear speed | \(\|\Delta \mathrm{coords}\|/\Delta t\) magnitude (and optional vectors) |
| RQA primary path (mirror game) | Preprocess → **pelvis-centre** → Procrustes → **PCA principal movements** → CRQA/MdRQA on PM (or keypoint **position magnitude** series in notebook 5) |
| Rate | Typically **30 Hz** |
| Filter | Butterworth 10 Hz order 4 on positions (before / in preprocess) |
| Body-size / alignment | Resolution norm (MOSAIC); Procrustes + pelvis centre (mirror game) |

**Actually implemented for RQA:** pose / PM trajectories (and sometimes position magnitude), **not** OptiTrack angular speed.  
**Linear speed** is used for linear kinematic summaries, not as the sole Auto-RQA input in the main case studies.

**Transferable idea:** root-centering to suppress locomotion.  
**Do not copy:** markerless landmark pipelines, Procrustes+PCA as mandatory RQA input, 30 Hz defaults, dyadic CRQA as Stage 1 primary.

---

## 7. Positional constructions tested (T1)

Bones: pelvis/root, Chest, LHand, RHand, LFoot, RFoot, Ab.  
Speeds in m/s after mm→m.

| Channel | Definition |
|---|---|
| B1_root | \(\|\Delta p_{\mathrm{root}}\|\,f_s\) |
| LHand_global | \(\|\Delta p_{\mathrm{LHand}}\|\,f_s\) |
| LHand_rootrel | \(\|\Delta (p_{\mathrm{LHand}}-p_{\mathrm{root}})\|\,f_s\) |
| Chest_rootrel | analogous |

---

## 8. T1-only comparison results (summary)

Locked angular params used for positional RQA **only as a diagnostic scaffold** (not proposed locks).

| Feature | med DET | med DET drop | med R1R2 \|ΔDET\| | Notes |
|---|---|---|---|---|
| A1_trunk | 0.981 | 0.930 | **0.008** | Best repeatability |
| A1_left_arm | 0.966 | 0.904 | 0.019 | Primary arm channel |
| B1_root | 0.834 | 0.789 | 0.037 | Translation dynamics |
| LHand_global | 0.933 | 0.889 | 0.040 | Includes room motion |
| LHand_rootrel | 0.921 | 0.877 | 0.028 | Distinct from A1 (corr≈0.21) |
| Chest_rootrel | 0.699 | 0.659 | 0.058 | Weaker structure |

Translation dominance: median corr(hand_global, root_speed) ≈ **0.15** (hands not reducible to root travel in these exercises).  
Body-size proxy CV across participants ≈ **7.5%**.  
Root travel per take differs by participant (252 highest).

---

## 9–10. Candidate table and scientific meaning

See `FEATURE_REPRESENTATION_DECISION.md` (authoritative classification).

| ID | Class |
|---|---|
| A1 | PRIMARY |
| A2 | SENSITIVITY_ONLY |
| B1 | REJECTED (as primary) |
| B2 | SECONDARY_COMPLEMENTARY |
| C | SENSITIVITY_ONLY |

---

## 11. Implications for Stage 1 locks

Locks remain valid **for A1 only**:

- rate 120 Hz; τ=18; m=4; radius 0.35×mean; block shuffle 0.30 s  

Do **not** apply these to B2 without re-estimation.

---

## 12. Must Stage 1 be rerun?

**No.** A1↔A2 do not change the Stage 1 technical gate. Positional candidates are not primary.

---

## 13. Should positional velocity enter Stage 2?

- **Not as primary.**  
- **Optional secondary:** root-relative hand (and maybe foot) speeds, with separate AMI/FNN/radius, Length-Units guards, and explicit “endpoint displacement” language.  
- Global root speed only as a translation **covariate / sensitivity**, not an Auto-RQA DV for joint dynamics.

---

## 14. Final freeze recommendation

**`CURRENT_FEATURE_VALID_ADD_SECONDARY_LATER`**

Include this audit, the decision report, the paper-code audit, and manifests in the Stage 1 freeze package. Proceed with the existing freeze → Stage 2 sequence on **A1**.

Artifacts:

- `scripts/feature_representation_audit.py`
- `outputs/feature_audit/a1_a2_math.json`
- `outputs/feature_audit/a1_a2_rqa_summary.json`
- `outputs/feature_audit/positional_summary.json`
- `manifests/source_data_feature_manifest.json`
