# FINAL METHOD DECISIONS — Shared 6D Motion POC (Stage 0)

Staged here during planning. Move to the root of `../gaga_shared6d_poc` at S1.

These decisions are fixed **before** any T1/T2/T3 separation is viewed. Nothing below may be re-selected after seeing results.

---

## 1. Input representation

Source of truth is the original Motive / OptiTrack global bone quaternions in
`data/raw_skeleton/` (24 CSVs, 5.1 GB, 120 Hz). The model input is derived from
those quaternions; it is never taken from a source-project cache.

Authoritative path (see also `reports/REPRESENTATION_PATH.md`):

```text
Raw OptiTrack global quaternions          <- the source representation
→ canonical parent-relative quaternions     (18 endpoint-relative links)
→ rotvec                                    (INTERMEDIATE ONLY: filtering + QC)
→ rotation matrix
→ 6D                                        <- the model input
```

Expanded operations:

```text
global bone quaternions
→ endpoint-relative rotation:  q_rel = inv(q_parent_global) · q_child_global
→ sign continuity along time
→ SO(3) log map to rotation vector          # filter / QC only — not model I/O
→ Butterworth low-pass, 10 Hz, order 4, zero-phase, in tangent space
→ rotation matrix
→ 6D (first two columns)
→ model input
```

**Rotvec is intermediate only.** It exists so the validated Layer 2 Butterworth
filter can be reproduced byte-for-byte and so joint-angle QC has a natural
tangent-space measure. It is not the source representation and not the model
input. Nothing downstream of the 6D step reads rotation-vector coordinates.

Relative extraction **precedes** filtering. Filtering sub-links and then
combining is not equal to combining and then filtering.

**Balanced conclusion on 6D.** On this dataset, 6D did **not** fix an observed
continuity failure: both the rotation vector and 6D show zero spurious
discontinuities at 120 Hz behind a 10 Hz low-pass, including across all near-π
frames. 6D is still the model I/O representation because continuity is a
property of the parameterisation (Zhou et al. 2019), not of this sampling rate,
and the encode/decode costs nothing (Frobenius round-trip 1.2e-15). Do not claim
that 6D rescued wrapping artifacts here; it provides a continuous neural-network
representation by construction at minimal cost.

**18 canonical links, identical for all four participants**: `pelvis_to_Ab`, `pelvis_to_LThigh`, `pelvis_to_RThigh`, `Ab_to_Chest`, `Chest_to_Neck`, `Neck_to_Head`, four per arm (`Chest_to_?Shoulder`, `?Shoulder_to_?UArm`, `?UArm_to_?FArm`, `?FArm_to_?Hand`), two per leg (`?Thigh_to_?Shin`, `?Shin_to_?Foot`).

No chain product is required. The chain telescopes exactly and both endpoint bones exist in every participant's skeleton, so a single endpoint-relative call returns the native link for 671/651 and the spine-spanning link for 252/790. This also removes the existing `CANONICAL_LINK_ALIASES = {"Neck_to_Head": ("Neck2_to_Head",)}` approximation, which treats anatomically different joints as equivalent.

Excluded: global position, global heading, room orientation, and the participant-specific spine and neck subdivisions (`Ab_to_Spine2`, `Spine2_to_Spine3`, `Spine3_to_Spine4`, `Spine4_to_Chest`, `Neck_to_Neck2`), whose information is retained in aggregate by the spanning links.

Rejected alternative: the 17-link common subset. It contains no link between abdomen and chest for any participant, deleting the entire thoracolumbar spine from a study of curvilinear spine-driven movement.

### Training target — both objectives run in Stage 0

Masked 6D rotation reconstruction **and** masked angular-velocity prediction of the masked links.

The velocity target is the best-evidenced single recommendation in the reference review (MAMP's +10.1/+6.1 ablation, corroborated independently by GFP's target-network ablation, MotionBERT's velocity loss term, and HumMUSS Eq. 3). Its rationale is stronger here than in the per-participant design it was written for: a model trained to reconstruct pose can succeed by memorising habitual posture, and in a *shared* latent space that identity axis is exactly the one that must not dominate, since change vectors and cross-participant cosines are computed in it.

**Selection rule, fixed in advance.** The two losses are not directly comparable (geodesic degrees versus degrees per second), but `skill` is a ratio against each objective's own matched trivial baseline and is therefore dimensionless and comparable across objectives. Select on held-out `skill` at held-out T1; tie-break on the participant-identity probe, lower identity accuracy winning. Never select on the direction-similarity result — that would be circular. If close, prefer masked 6D reconstruction as simpler and more directly interpretable.

**Mask ratio is swept, not assumed**: {30, 50, 70}% on Fold A seed 0, scored on held-out training blocks only, then fixed for all full runs, with the sensitivity curve reported. MAMP found 90% optimal and MotionBERT found above ~45% harmful; the conflict is the finding, so the value is dataset-dependent and must be measured here.

---

## 2. Embedding

```text
full unmasked 6D input
→ trained encoder
→ final encoder token grid (18 links × 24 temporal patches = 432 tokens)
→ mean over all 432 tokens
→ one 32-dimensional window embedding
```

- Decoder serves the reconstruction objective only; discarded for embedding.
- No separate 32→16 latent head.
- No L2 normalisation of window embeddings — that would discard the magnitude needed to compare change against the repetition reference.
- A learned mask token is used during training, so the encoder always sees 432 tokens and unmasked inference is the natural limit case rather than a distribution shift.
- Extraction is deterministic: no mask sampling, no averaging over realisations, so embedding variability across seeds reflects training alone.

Aggregation:

```text
windows → mean within each exercise → equal-weight mean across ex09–ex13 → recording embedding
```

Exercise balancing is required because exercise durations vary *between* the timepoints being contrasted (ex11 spans 9–12 s, ex13 spans 11–19 s), so pooled windows would fold a mixture-composition shift into the change estimate. Pooled aggregation is a sensitivity. ex11 is retained as a separate interpretable breakdown.

---

## 3. Standardization

Fitted on **training-T1 embeddings within the current fold only**. T2 and T3 never inform centering or scaling.

Procedure:

1. Aggregate training-T1 window embeddings into contiguous-block centroids.
2. Weight each participant × exercise combination equally.
3. Estimate per-dimension mean and standard deviation from those balanced block-level observations.
4. Apply the fitted transform unchanged to held-out T1, T2 and T3.

Rationale: fitting on every overlapping window would treat correlated windows as independent and let longer exercises, recordings with more windows, or participants contributing more usable windows dominate the latent scale. Block centroids respect the dependence structure; equal participant × exercise weighting removes the duration and count imbalance.

**No full covariance whitening at Stage 0.** Effective sample size is governed by the 58 independent contiguous blocks, not the ~271 overlapping windows. At d = 32 that gives n/d ≈ 1.8 against a desirable ≥ 10, so the transform would be dominated by estimation noise and could manufacture apparent alignment.

Raw-centred and standardized geometry are **co-primary**, not primary-plus-sensitivity.

---

## 4. Reconstruction gate

```text
skill(T) = [error_trivial(T) − error_model(T)] / error_trivial(T)
```

**Mandatory.** `skill(T) > 0` at held-out T1, T2 and T3 before the corresponding latent geometry is interpreted. A zero-crossing, not a tuned constant.

**Descriptive diagnostic, paired within run.** For every participant, fold and seed, compare against the matched held-out-T1 skill from the *same* run:

```text
Δskill_T2 = skill(T2) − skill(held-out T1)
Δskill_T3 = skill(T3) − skill(held-out T1)
```

Folds and seeds from one participant share data and are not independent, so these are paired comparisons — never a pooled distribution of 24 values. Report held-out-T1 skill, T2 skill, T3 skill, the paired difference, bootstrap uncertainty where feasible, and consistency across folds and seeds.

Three states:

1. **Model failure** — `skill(T) ≤ 0`. Do not interpret the latent direction at that timepoint.
2. **Useful but degraded** — `skill(T) > 0` yet clearly below its paired held-out-T1 value. May reflect meaningful novelty; interpret with caution. This is the *expected* signature if real change occurred.
3. **Stable quality** — `skill(T) > 0` and broadly comparable to its pair.

No new fixed degradation threshold. The `0.5 × skill(held-out T1)` line may appear as an optional visual reference only, never as a pass/fail rule.

---

## 5. Direction-similarity statistic

Mean pairwise cosine over the six participant pairs, computed **within each (fold, seed) separately** and under both raw-centred and standardized geometry.

```text
Δ12 = z(T2) − z(T1),   Δ13 = z(T3) − z(T1),   Δ23 = z(T3) − z(T2)
```

Reported separately and **not** as three independent tests, since `Δ23 = Δ13 − Δ12`.

Latent coordinates are never averaged across independently trained folds. Folds and seeds combine at the statistic level only. Agreement across the two geometries means positive mean pairwise cosine and the same sign-flip rank under both; cosine is not invariant to affine transformation, so a direction visible under only one scaling is an artifact of that choice.

Change magnitude is compared against **within-session repetition variability** measured at T2 and T3 (`Drep_T2`, `Drep_T3`, reported separately; `max` as a stated-conservative sensitivity, noting a max over two noisy estimates is upward-biased).

---

## 6. Sign-flip assumption

> The exact sign-flip analysis is the primary empirical reference under a participant-level sign-symmetry assumption: under the null, each participant's observed change direction and its inverse are treated as exchangeable.

It is **not** assumption-free.

- Sign flips operate on participant change vectors, not on individual pairwise cosine values. This is what keeps the dependence among the six pairwise cosines — constrained by Gram-matrix positive-semidefiniteness — correctly respected.
- The 16 sign patterns collapse to **8 distinct** mean-pairwise-cosine values, because globally reversing all vectors leaves every cosine unchanged.
- The minimum exact p-value is therefore **0.125**.
- The random isotropic-vector distribution is **theoretical context only**. A trained latent concentrates variance and, with whitening rejected, inter-dimension correlation remains, so isotropy does not hold.
- At N = 4 no exact participant-level null reaches conventional significance (sign-flip floor 0.125; T2↔T3 label-permutation floor 0.0625). The analysis is descriptive and cannot support a significance claim. It stays descriptive even if the observed value exceeds every one of the eight configurations.

Both the assumption and this limitation must appear in the final report.

---

## 7. Matched-task baseline

Required Stage 0 work, not deferred.

PCA, mean-motion and interpolation do not perform masked reconstruction, so "the Transformer beats PCA" would conflate architecture with objective. The two baselines answer different questions:

- **PCA** (d = 32, fitted on the training repetition): is a learned representation useful at all?
- **Convolutional masked predictor**: is attention useful?

The convolutional baseline receives the same 18-link 6D input, the same 24 temporal patches, the same structured masks, the same folds, the same training and evaluation recordings, and the same embedding extraction and downstream analyses. It runs on the **selected** objective only, keeping the architecture comparison separable from the objective comparison. It replaces temporal attention with a small temporal convolution (kernel 3) and spatial attention with a simple linear mixing across links. Target ≈ 14k parameters against the Transformer's ≈ 38k.

**Incremental-value criterion.** Do not claim the Transformer adds value unless it improves the matched baseline in reconstruction skill with non-overlapping bootstrap intervals across folds and seeds **and** produces at least equally stable longitudinal and direction-similarity results. If the baseline matches or exceeds it on both, the go/no-go recommends the simpler model.

---

## 8. Interpretation limitations

**Session and timepoint are non-identifiable.** Every participant's T1/T2/T3 fall on three different days; R1 and R2 are always the same session, 9–15 minutes apart. No design element separates day from timepoint. Consequently the session-identity probe from the original specification is **not implemented** — it would be arithmetically identical to the timepoint probe and would create false reassurance. The available proxy is a per-recording bone-length check: stable solved segment lengths across timepoints indicate a consistent skeleton solve; divergence flags a session artifact.

**The repetition reference is a lower bound.** Within-session repetition variability does not capture marker reapplication, recalibration, skeleton re-solving, or recording-day effects. Failing to exceed it is decisive against a change; exceeding it does **not** establish that change exceeds between-session measurement noise, which this design cannot estimate. It is never called a measurement noise floor.

**N = 4 caps inference.** No exact participant-level null can reach p < 0.05. All cross-participant conclusions are descriptive.

**Participant 252 differs in protocol duration** (42 days T1→T3 versus ~28 for the others). Retained in the primary analysis; interval reported explicitly; included in the jackknife with the no-252 case highlighted. Latent change is **not** normalised by days — that would impose linear accrual, implausible for this intervention and unverifiable with three timepoints. Change magnitude is not interpreted as equivalent exposure across participants. Direction similarity is scale-invariant, so this bears far less on the headline outcome than on magnitude.

**Provenance hazards.** Longitudinal ordering keys on the embedded Motive `Capture Start Time`, never filenames — `252_T2` is named `2026-04-26` but was captured `2026-05-19`. `Length Units` is recorded and asserted per recording; `252_T3` is in Meters while all others are in Millimetres, and the source project's `skeleton_marker_to_meters` additionally applies an axis permutation only in the Millimetres branch.

**Acceptable claim ceiling.** The strongest supportable conclusion is:

> The model detected a repeatable change in the recorded motion representation between sessions, exceeding within-session repetition variability.

Not supportable: a behavioural change, an intervention effect, a population estimate, or any claim that change exceeds between-session measurement noise.
