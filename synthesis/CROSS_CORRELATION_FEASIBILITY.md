# Cross-correlation feasibility

**Classification (locked):** `XCORR_OPTIONAL_BACKUP_ONLY`  
**Literature decision:** `ROADMAP_MINOR_UPDATE` — see `CHANG_PAPER_IMPACT_REVIEW.md`  
**This phase:** no computation

---

## Chang framework (relevant points only)

- Normalised signed zero-lag cross-correlation of **anatomical Cardan** joint angles within planes.
- In-phase (+1) / anti-phase (−1) interpretation.
- Intra-limb pairs; PCA can organise globally while some local couplings weaken.
- Cross-sectional skill design; authors call for longitudinal work.
- Direction of DOF change not universal (cites Newell & Vaillancourt).

## Relevance to Gaga longitudinal data

Scientifically interesting as a **local complement** to JcvPCA whole-body redistribution, but not required for thesis conclusions given signal limits.

---

## Signal candidates

### Candidate 1 — anatomical flexion / abduction / rotation

| Criterion | Assessment |
|---|---|
| Matches Chang | Yes |
| Supported by current pipeline | **No** without new anatomical calibration |
| CLAIMS scope | Anatomical joint-angle statements from relative link rotvecs are **forbidden** |
| Risk | Euler/Cardan wrapping artifacts |
| Decision | **Rejected** for current synthesis |

### Candidate 2 — signed parent-relative rotvec / angular-velocity components

| Criterion | Assessment |
|---|---|
| Technically closer to existing data | Yes |
| Phase meaning | Component synchrony only — **not** Chang anatomical in-phase/anti-phase |
| Decision | Usable only with restricted language; not sufficient to upgrade classification |

### Speed magnitude (existing features)

**Do not** interpret signed/abs speed correlations as in-phase / anti-phase joint coupling.

---

## If later approved (minimal pre-registration only — not run now)

- Pairs: torso neck↔trunk; per arm shoulder–elbow, elbow–wrist, shoulder–wrist; per leg hip–knee, knee–ankle, hip–ankle.
- Primary output: signed zero-lag `r0` (Fisher-z).
- Secondary: `rmax`, `lag_at_max` with T1-only lag window in physical time (do not default to ±5 frames ≈ ±42 ms).
- R1/R2 Drep on z; matched Δ12/Δ13; same-sign across R1/R2; QC on length/artifacts.
- Map categorically to JcvPCA links (not mathematical equivalence).
- D12 primary; D13 supplemental.
- Stop if signal QC fails or anatomical claims cannot be avoided.

**Expected compute cost:** moderate offline pass; not blocking thesis packaging.

---

## Why not upgrade or downgrade

| Option | Rejected because |
|---|---|
| `XCORR_MINIMAL_IMPLEMENTATION_RECOMMENDED` | No safe Chang-equivalent signal; thesis story does not require it |
| `XCORR_NOT_SCIENTIFICALLY_JUSTIFIED` | Optional local-vs-global concordance remains scientifically coherent *if* a later safe signal exists |
| `XCORR_ALREADY_SUFFICIENT` | Existing regional speed coupling is not Chang-style |

**Retain:** `XCORR_OPTIONAL_BACKUP_ONLY`.
