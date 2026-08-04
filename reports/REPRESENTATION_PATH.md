# Representation path

The authoritative statement of what the model consumes and where it comes from.
Everything here is verified by `scripts/s2_extract.py` and
`scripts/s3_validate_repr.py`; see `reports/DATA_VALIDATION_REPORT.md` and
`reports/REPRESENTATION_VALIDATION_REPORT.md` for the measurements.

---

## The path

```text
Raw OptiTrack global quaternions          <- the source representation
  -> canonical parent-relative quaternions   (18 endpoint-relative links)
  -> rotvec                                  (INTERMEDIATE ONLY: filtering + QC)
  -> rotation matrix
  -> 6D                                      <- the model input
```

Step by step, with the operation actually applied:

| # | Stage | Operation | Role |
|---|---|---|---|
| 1 | Global bone quaternions | read from the Motive CSV `Bone` rotation channels | **source representation** |
| 2 | Canonical parent-relative quaternions | `q_rel = inv(q_parent_global) * q_child_global` over the 18 canonical endpoint pairs, then quaternion sign-continuity correction | derived, still quaternion |
| 3 | Rotation vector | SO(3) log map, then zero-phase 4th-order Butterworth low pass at 10 Hz in the tangent space | **intermediate only** |
| 4 | Rotation matrix | `Rotation.from_rotvec(...).as_matrix()` | intermediate |
| 5 | 6D | first two columns of the rotation matrix | **model input** |

Decoding is Gram-Schmidt (Zhou et al. 2019, Eqs. 14-16):
`b1 = N(a1)`, `b2 = N(a2 - (b1.a2) b1)`, `b3 = b1 x b2`.

---

## Confirmations requested

### The model input comes from the original quaternion data

Confirmed. Every value the model will see traces back to the raw Motive
quaternion channels through steps 1-5 above. No intermediate cached product of
the source project is used as an input. Specifically:

* `gaga_jcvpca/outputs/cache/matrices/*.parquet` is read **only** to validate
  step 2 against an independent implementation. It is never an input. See
  `reports/CACHE_INVALIDATION_NOTICE.md` for why it must not become one.
* The relative rotation at step 2 is computed from the global quaternions of
  the two **endpoint** bones directly. No chain product is formed, and the
  validity of that shortcut is verified numerically, not assumed
  (36 checks, worst error 3.735e-14 degrees).
* Extraction precedes filtering. Filtering sub-links and then combining them is
  not equal to combining and then filtering, so the order is fixed and enforced
  by construction in `extract_link_rotvec`.

### The rotation vector is an intermediate, not the source and not the input

Confirmed, and it is worth being precise about why it appears at all.

The rotation vector exists in the path for exactly two reasons:

1. **Filtering.** The validated Layer 2 pipeline in the source project applies
   its Butterworth low pass in rotation-vector tangent space. Reproducing that
   step byte-for-byte is what allows the 378 bit-identical agreements in S2,
   which is the strongest available evidence that the rotation convention,
   multiplication order, axis handling and sign-continuity treatment are all
   correct. Moving the filter elsewhere would forfeit that check.
2. **Quality control.** Joint angles, near-pi fractions and per-frame jump
   diagnostics are naturally expressed as a rotation vector's norm and
   direction.

It is **not** the source representation: it is derived from the quaternions at
step 3. It is **not** the model input: the model consumes the 6D encoding at
step 5. Nothing downstream of step 5 reads rotation-vector coordinates.

This distinction has a concrete consequence. Tangent-space filtering pushed one
link in one recording (`RShoulder_to_RUArm` in `790_T1_P1_R1`) past the pi
branch in 0.013 percent of frames, giving a stored rotation-vector norm of
190.6 degrees. Because the rotation vector is an intermediate, this does not
reach the model: `Rotation.from_rotvec` maps that vector to a valid rotation
(169.4 degrees about the opposite axis), and the resulting matrix and 6D
encoding are correct. Had the rotation vector been the model input, the same
event would have presented as a 341-degree coordinate jump.

---

## Sensitivity path (not the project default)

A direct path without rotvec or Butterworth was **not** implemented before S3b.
It is now available as a sensitivity branch only:

```text
Raw OptiTrack global quaternions
  → canonical parent-relative quaternions
  → rotation matrix                         (no rotvec, no Butterworth)
  → 6D
```

Implemented in `rotations.extract_link_matrix_direct` and compared on a
representative subset by `scripts/s3b_filter_sensitivity.py`. Result:
`reports/FILTER_SENSITIVITY_REPORT.md` — recommendation **KEEP_PRIMARY**.
The validated filtered path above remains the model input path.

---

## The balanced conclusion about 6D

**6D did not fix an observed continuity failure in this dataset.** It provides a
continuous representation by construction, at negligible cost.

The measurements, stated plainly:

| Observation | Value |
|---|---|
| Spurious discontinuities, rotation vector | **0** |
| Spurious discontinuities, 6D | **0** |
| Near-pi frames examined (angle > 0.9 pi) | 426 |
| Largest true geodesic angle in the dataset | 178.4 deg |
| 6D encode/decode round-trip error | 1.206e-15 Frobenius |

A discontinuity was defined operationally as the representation moving more
than 1.0 in its own space while the body rotated less than 0.1 rad between
frames. Neither representation produced one, including across every near-pi
frame.

The reason is sampling, not luck in any deep sense: at 120 Hz behind a 10 Hz
low pass, consecutive frames differ by milliradians, so the rotation vector
never gets the opportunity to wrap. **On these particular recordings, a
rotation-vector input would have worked too.**

So the case for 6D rests on two things, and neither is a rescue narrative:

1. **Continuity is a property of the parameterisation, not of this sampling
   rate.** The rotation vector's continuity here is contingent on 120 Hz
   sampling and aggressive smoothing. 6D is continuous as a map from SO(3)
   regardless, which matters for a representation that is meant to survive
   contact with a future N = 50 dataset that may be sampled, filtered or
   segmented differently. Zhou et al. (2019) is the reference for why
   discontinuous parameterisations are hard for neural networks to regress.
2. **It costs nothing.** The conversion is non-destructive and exact to float64
   (1.2e-15), so the representation contributes no error of its own. Any
   reconstruction error observed at S6 belongs to the model.

What should **not** be claimed: that 6D was necessary here, that it repaired
wrapping artifacts, or that the rotation vector was observed to fail. It was
not. The honest summary is that 6D buys a guarantee for free, and the guarantee
is worth having for a representation intended to scale beyond this dataset.

The one genuine artifact observed (filter overshoot past pi, section above) is
an argument for keeping the rotation vector *out* of the model input, which is
the design already in place.
