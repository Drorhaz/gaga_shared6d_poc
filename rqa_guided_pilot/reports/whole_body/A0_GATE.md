# A0 gate — whole-body configuration-space RQA

**Verdict:** `PASS`

T1-only representation and data-integrity verification. No RQA metrics, no distance matrices, no T2/T3 rotvec loads.

## Verified facts

- Canonical order (18 links): `pelvis_to_Ab`, `pelvis_to_LThigh`, `pelvis_to_RThigh`, `Ab_to_Chest`, `Chest_to_Neck`, `Neck_to_Head`, `Chest_to_LShoulder`, `LShoulder_to_LUArm`, `LUArm_to_LFArm`, `LFArm_to_LHand`, `Chest_to_RShoulder`, `RShoulder_to_RUArm`, `RUArm_to_RFArm`, `RFArm_to_RHand`, `LThigh_to_LShin`, `LShin_to_LFoot`, `RThigh_to_RShin`, `RShin_to_RFoot`
- Loader order matches YAML: **True**
- Root token: `pelvis`; pelvis-parent links: ['pelvis_to_Ab', 'pelvis_to_LThigh', 'pelvis_to_RThigh']
- Region counts: {'trunk_spine': 2, 'head_neck': 2, 'left_arm': 4, 'right_arm': 4, 'left_leg': 3, 'right_leg': 3}
- YAML spanning-link IDs: Ab_to_Chest, Neck_to_Head
- T1 native-adjacent for those endpoints (51bone_basic): ['651', '671']
- T1 spanning intermediates (55bone_extended): ['252', '790']
- Filter/rate (from experiment.yaml, not re-applied): butterworth_lowpass 10.0 Hz order 4; capture 120.0 Hz
- Rotvec layout: (T, 18, 3) after load_rotvec; parquet wide 54 columns {link}_{rx,ry,rz}; units assumed radians
- T1 cells: 40 / expected 40
- T1 duration_s min/median/max: 6.000 / 10.000 / 16.000
- T1 n_frames min/max: 720 / 1920
- Policy OK: 40/40; trimmed=0; near-π cells=0; jump cells=0
- T1 max |rotvec| angle rad: 2.8709400637789813; max per-frame ||Δrotvec|| rad: 0.27739610358678857
- T1 max NaN fraction: 0.0

### T1 skeleton variants (registry metadata, T1 rows only)

- pid 252 R1: 55bone_extended n_bones=55 root=252:252
- pid 252 R2: 55bone_extended n_bones=55 root=252:252
- pid 651 R1: 51bone_basic n_bones=51 root=651:651
- pid 651 R2: 51bone_basic n_bones=51 root=651:651
- pid 671 R1: 51bone_basic n_bones=51 root=671:671
- pid 671 R2: 51bone_basic n_bones=51 root=671:671
- pid 790 R1: 55bone_extended n_bones=55 root=790:790
- pid 790 R2: 55bone_extended n_bones=55 root=790:790

## Assumptions

- Stored rotvecs are already 10 Hz order-4 zero-phase Butterworth-filtered (experiment.yaml / Layer 2); A0 does not re-filter.
- Units are radians (rotations.py log-map); A0 infers this from pipeline docs, not from a unit tag in parquet.
- Global root orientation/translation are absent because links are endpoint-relative to named bones; A0 does not reconstruct Motive global quats.
- Per-frame step uses Euclidean ||Δrotvec|| as a jump diagnostic only, not the planned SO(3) geodesic pairwise distance.

## Fail reasons / issues

- (none)

## Scientific consequences

- Global laboratory orientation and translation are **not** in the 18-link state. A0 supports an **internal articulated configuration** claim, not unrestricted posture recurrence.
- Equal-link distance would still overweight arms (4+4 links). That is a later distance-aggregator choice, not an A0 data failure.
- A0 does **not** validate the 120-cell longitudinal grid. Only the 40 T1 cells were inspected.

## Manifest

- git: `4c3f0754f93aae87f6c2b2d72044371b068f33e0`
- utc: `2026-08-13T00:00:01.169770+00:00`
- facts: `outputs/whole_body/A0_representation_facts.json`

## A1 authorization

A0 PASS. A1 is eligible for **separate** authorization only. A1 was not started.
