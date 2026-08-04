# Readiness recommendation at the S4 gate

This is the pre-registered pause. Stages S1 to S4 are complete and no model has
been trained. Nothing beyond this point should run until this document has been
reviewed.

---

## Recommendation

**Proceed to S5 (baselines) and S6 (compact model).**

All four validation gates pass, and they pass on evidence rather than on
assumption:

| Gate | Result |
|---|---|
| S1 ingest and provenance | 24/24 recordings, SHA-256 over 5.51 GB, ordering monotonic on embedded capture time |
| S2 extraction | 378 bit-identical matches to the trusted cache, 6 alias-explained, **0 unexplained** |
| S2 chain identity | 36 checks, worst 3.7e-14 degrees |
| S3 representation | 6D round trip lossless at 1.2e-15 Frobenius; 0 discontinuities |
| S4 windowing | 1657 windows, 0 boundary crossings, 0 split blocks, 0 missing data |

The input pipeline is trustworthy. Every one of the 24 recordings now yields
the same 18 anatomical rotations, derived by one identical operation, verified
against an independent source of truth.

---

## What changed in our understanding during S1-S4

### The skeleton template changes mid-study

Discovered in S2, not anticipated in the plan. Participant 651 switches from a
51-bone to a 55-bone Motive template between T1 and T2; participant 671 does so
between T2 and T3.

This would have been a first-order confound under a per-participant link map,
because the template changes at precisely the timepoint boundary the study
measures. The endpoint-relative design was adopted to reconcile topology
*across* participants; it turns out to be necessary *within* them too. This
project is unaffected, and the finding is now documented and tested rather than
latent.

It also means the source project's cached features for `651-T2`, `651-T3` and
`671-T3` silently drop the three pelvis links and mislabel the head-neck link
by up to 41 degrees. Those caches should not be reused for longitudinal work.

### Two measurement subtleties were corrected

* The 6D round-trip gate initially used the geodesic angle and was failing
  bit-perfect round trips, because `arccos` is ill conditioned near zero error.
  The gate now uses the Frobenius norm; the geodesic value is still reported.
* Reporting the norm of the *filtered* rotation vector as a joint angle
  produced an impossible 190.6 degrees. The true geodesic angle is bounded by
  180 as it must be; the excess is tangent-space filter overshoot, now measured
  separately and confined to 0.013 percent of frames in one link of one
  recording.

Neither changed a conclusion, but both would have put a wrong number in a
report.

---

## What must travel with every downstream result

1. **N = 4.** Everything after this point is descriptive. The sign-flip null
   has a floor of p = 0.125 and the T2/T3 label permutation a floor of
   p = 0.0625. Neither can produce conventional significance, by construction.
2. **Timepoint and session are perfectly confounded** within a participant.
   Each timepoint is one session, so no analysis here can separate a
   behavioural change from a session artifact. The per-recording bone-length
   check is a partial proxy; the session-identity probe was dropped as
   non-identifiable.
3. **Participant 252 was followed for 42 days** against 27-28 for the others,
   and is the only participant whose T3 was exported in Meters. It is carried
   as a pre-specified protocol-duration sensitivity, including the
   jackknife-without-252 case.
4. **651 and 671 changed skeleton template mid-study.** Immaterial here by
   construction, but it must be stated, because it would not be immaterial for
   any position-based or bone-length-based follow-up.
5. **The training set is roughly 400 windows per fold**, about 10 minutes of
   motion from four people. This is the binding constraint on the experiment.

---

## Risks going into S5-S6, and what will detect them

| Risk | Detection already built in |
|---|---|
| The model memorises four people rather than learning motion | participant-identity probe; objective selection is tie-broken on it |
| 38k parameters still overfit 400 windows | matched-task convolutional baseline at ~14k parameters on identical masks and targets; PCA at d=32 |
| Masking task is trivially solvable | structured link-by-span masking; mask-ratio sweep over 30/50/70 percent scored on held-out blocks only |
| Latent change is really an amplitude change | explicit amplitude control and correlation with interpretable features |
| Result is an artifact of latent geometry | direction similarity required to agree under both raw-centred and standardized geometry |
| Selection on the outcome | objective chosen on held-out skill and the identity probe, **never** on direction similarity |

---

## Explicit stop conditions for S5-S6

Training should be halted and this gate revisited if any of the following
occurs:

* the participant-identity probe exceeds chance substantially under both
  objectives, indicating the latent encodes who rather than what;
* the compact model fails to beat PCA at d=32 on held-out skill, in which case
  the transformer is not earning its complexity and the analysis should
  continue with PCA;
* the mask-ratio sweep shows held-out skill is flat across 30/50/70 percent,
  indicating the pretext task carries no signal.

---

## Next commands

```bash
python scripts/s5_baselines.py      # PCA, mean-motion, interpolation, conv baseline
python scripts/s6_masksweep.py      # 30/50/70 percent on fold A seed 0 only
python scripts/s6_train.py          # both objectives x 2 folds x 3 seeds
```

Reproducing S1-S4 from scratch:

```bash
python scripts/s1_ingest.py
python scripts/s2_extract.py
python scripts/s3_validate_repr.py
python scripts/s4_window.py
```
