# Feature representation decision

**Final classification:** `CURRENT_FEATURE_VALID_ADD_SECONDARY_LATER`

**Primary remains:** regional angular-velocity magnitude from filtered parent-relative link rotvecs (`A1`).

**Stage 1 locks:** retain (120 Hz, τ=18, m=4, radius 0.35×mean, block 0.30 s).  
**Stage 1 rerun:** not required.  
**Not** `STAGE1_REQUIRES_TECHNICAL_CORRECTION`.

Companion reports:

- `SOURCE_DATA_AND_FEATURE_AUDIT.md` (chain, math, T1 evidence)
- `PAPER_CODE_REFERENCE_AUDIT.md` (external RQA engine parity)

---

## Candidate decision table

| ID | Representation | Class | Rationale |
|---|---|---|---|
| **A1** | Regional mean of `‖Δrotvec‖·fps` (deg/s) | **PRIMARY** | Valid for joint-orientation-change intensity; T1 RQA stable; matches scientific question; A2-equivalent for Stage 1 conclusions |
| **A2** | Regional mean of SO(3) geodesic speed from consecutive filtered rotvecs | **SENSITIVITY_ONLY** | Mathematically preferred local definition; median agreement with A1 excellent; rare forearm large-angle residuals; does **not** change AMI/FNN/RQA gates → keep as validation reference, not replacement |
| **B1** | Global positional speed (root / endpoints in room frame) | **REJECTED** (as RQA primary) | Measures capture-volume translation + articulation; worse R1/R2 than A1; not the joint-dynamics question; unit/axis hazards outside T1 |
| **B2** | Pelvis/root-relative endpoint positional speed | **SECONDARY_COMPLEMENTARY** | Distinct from angular speed (median corr ≈ 0.21 with arm angular); captures endpoint displacement; acceptable T1 surrogate disruption; slightly weaker R1/R2; optional later, **own** τ/m/radius |
| **C** | Compact hybrid (angular + root-rel endpoints) | **SENSITIVITY_ONLY** | Constructs are distinct enough to imagine a hybrid, but no strong need before Stage 2; defer; do not enlarge state now |

---

## Scientific meaning (locked language)

| Candidate | Measures | Does **not** measure |
|---|---|---|
| A1 / A2 | How intensely **regional joint orientations** change over time | Posture return, motif identity, endpoint path, room translation |
| B1 | How quickly points move through the **capture volume** | Pure articulation |
| B2 | How quickly points move relative to the **pelvis/root** | Joint-level rotational contribution |

Do not equate angular speed, linear speed, global translation, energy, coordination, or posture recurrence.

---

## Why A1 stays primary

1. **Math:** Parent-relative filtered rotvecs; FD magnitude is an approved high-rate approximation. Geodesic A2 agrees at median relative difference **0.19%** (n≈8.5×10⁵); Stage 1 RQA metrics correlate ≥0.99 with A2 under locked params.
2. **Science:** Matches guided improvisation interest in **joint contribution / rotational dynamics**, not locomotion through the volume.
3. **T1 tech:** AMI τ≈18, FNN m≈4, strong full-shuffle DET drop, acceptable R1/R2 — same under A2.
4. **Robustness:** Rotation path independent of mm/m export; T1 all Millimeters. Template changes (651/671) affect spanning composition but endpoint-relative definition is consistent within T1.
5. **Paper:** Paper RQA is primarily on **root-centered / Procrustes / PCA pose trajectories**, not OptiTrack angular speed. Do not replace A1 to imitate markerless pipelines.

## Why not replace with A2

Local FD vs geodesic gaps concentrate on high-angle forearm links (rotvec chord ≠ SO(3) geodesic when ‖r‖ is large). After regional averaging, recurrence structure and parameter diagnostics are unchanged. Replacing A1 would force lock invalidation without scientific gain for Stage 1. Retain A2 as a sensitivity/validation check if Stage 2 revisits forearm-heavy claims.

## Why B2 is secondary later (not freeze-blocking)

- Distinct construct (endpoint displacement).
- Not translation-dominated (hand↔root speed corr ≈ 0.15).
- Usable surrogate disruption; R1/R2 slightly worse than A1.
- Must **not** inherit angular locks; needs own AMI/FNN/radius if used in Stage 2.
- Guard Length Units (252_T3 Meters) and avoid marker-only axis remaps for bone positions.

## Implications

| Item | Decision |
|---|---|
| Invalidate `parameter_lock_stage1.json`? | **No** |
| Rerun Stage 1? | **No** |
| Include audits in Stage 1 freeze? | **Yes** |
| Positional velocity in Stage 2 as primary? | **No** |
| Optional Stage 2 secondary B2? | **Yes**, with separate params |
| Hybrid C now? | **No** |

---

## Freeze recommendation

Proceed with the previously approved Stage 1 freeze sequence using **A1** and existing locks. Attach:

- `SOURCE_DATA_AND_FEATURE_AUDIT.md`
- `FEATURE_REPRESENTATION_DECISION.md`
- `PAPER_CODE_REFERENCE_AUDIT.md`
- manifests under `rqa_guided_pilot/manifests/`

Stage 2 may use angular-speed primaries as already designed; root-relative endpoint speed only as an optional complementary channel with its own estimation.
