# JcvPCA evidence hierarchy audit

**Authoritative stack:** `gaga_jcvpca/results_committee_case/marker_gap_policy_ex09_13/` (regenerated 2026-07-28)  
**Governing claims:** `gaga_jcvpca/results_committee_case/step00_claim_framework/CLAIMS.md`  
**Headline table:** `.../tables_to_show/09_headline_a2_summary.csv`  
**NV tiers:** `.../step08_nv_and_stability/NV_PROFILE.csv`  
**Step-5 mechanism:** `.../step05_amplitude_vs_organization/classification_summary.md`  
**S3 caveat:** `gaga_jcvpca/docs/slide45_figures/backup/S3_definition_and_caveat.md` (2026-07-30)

---

## Locked definitions

| ID / label | Authoritative meaning | Minimum evidence | Status in marker-gap stack |
|---|---|---|---|
| **A1** | A link’s relative contribution to shared movement-variance structure changed T1→T2 or T1→T3 | Step 4 link/region tables | Descriptive fact wherever Step 4 reports change |
| **A2** | That change exceeds observed T1 R1–R2 variability **and** is direction-stable under R1/R2 anchor swap | Signed tier **S2** | Formal longitudinal claim; headline in `09_*.csv` |
| **A3** | Pattern consistent with broader participation of previously low-contributing links (reweighting in T1 subspace) | **S3** + supervisor sign-off | **Not formally supported** — `SUPERVISOR_NV_DECISION.md` pending; CLAIMS claim-scope pending |
| **S0** | `\|long_signed\| ≤ \|nv_signed\|` | Step 8 | Within T1 repetition spread |
| **S1** | Exceeds NV magnitude but **not** reference-direction-stable | Step 8 | Reported; **not** A2 |
| **S2** | Exceeds NV **and** `sign(long_signed) = sign(long_signed_rev)` | Step 8 | **A2 minimum** |
| **S3** | S2 + adequate coverage + `rep_pass` + Step-5 `classification == organization` | Step 8 + Step 5 + Step 4b | Candidate A3 only; **4 links, 671 T1→T2 only** |
| **organization** (Step 5) | Exceeds Step-5 NV **and** ROM ratio in flat band 0.7–1.3 | Step 5 | Descriptive mechanism class |
| **amplitude** (Step 5) | Exceeds Step-5 NV **and** ROM outside band with consistent JcvPCA sign | Step 5 | Descriptive mechanism class |
| **mixed** (Step 5) | Exceeds Step-5 NV **and** ROM shifts without consistent sign | Step 5 | Descriptive mechanism class |

### Footing asymmetry (documented, unresolved by supervisor)

- **S2/A2** uses matched **single-rep signed** floor (`T1_R1 vs T1_R2` vs `T1_R1 vs T{k}_R1`).
- **Step-5 organization** uses **pooled** longitudinal effect over single-rep floor on mean-|Δ|.
- Therefore a link can be S2/A2 yet fail Step-5’s pooled NV test (or vice versa in edge cases). Governing S3 still requires Step-5 `organization`.

---

## Headline numbers (authoritative)

From `09_headline_a2_summary.csv`:

| Pid | T1→T2 A2 (S2) | T1→T3 A2 | S3 | Coverage T2 / T3 | rep_pass T2 / T3 |
|---|---:|---:|---:|---|---|
| 671 | 8 | 9 | **4 (T2 only)** | adequate / limited | True / False |
| 252 | 3 | 12 | 0 | adequate / limited | False / False |
| 651 | 4 | 2 | 0 | adequate / limited | False / False |
| 790 | 7 | 3 | 0 | adequate / adequate | False / False |

**S3 links (671 T1→T2 only):** `671_to_LThigh`, `LFArm_to_LHand`, `LShin_to_LFoot`, `LThigh_to_LShin`.

**Step-5 organization totals across 8 cells:** **51 organization / 4 amplitude / 4 mixed**  
(`classification_summary.md`; also `docs/slide45_figures/README.md`).

---

## Critical non-equivalence

### `51 organization ≠ 51 A3 findings`

| Why organization is not A3 | Evidence |
|---|---|
| Different evidence standard | Organization = Step-5 mechanism label; A3 requires S3 stack + supervisor |
| Footing mismatch | Step-5 pooled mean-\|Δ\| NV ≠ S2 matched signed NV |
| Additional gates | S3 needs coverage adequate + `rep_pass` + organization |
| Empirical gap | 51 organization labels vs **4** S3 links (671 T2 only) |
| Supervisor gate | A3 still pending sign-off |

Presentation guidance (`S3_definition_and_caveat.md`): treat S3 as supporting detail for **671 only**; headline = A2 pass counts.

---

## Stale vs authoritative conflicts (do not silent-merge)

| Stale claim | Where | Authoritative correction |
|---|---|---|
| 651 T2 has S3=5 | `SUPERVISOR_MEETING_*_2026-07-18.md`, `METRICS_DIGEST.md` §8v6 | Marker-gap: **651 S3=0**; S3 only 671 T2 |
| 252 T3 organization 19/19 | July-18 supervisor brief (pre-policy) | Marker-gap Step 5: **10 organization / 0 amplitude / 0 mixed** |
| Transient hand-copied `S3=0` | Early `tables_to_show/05` snapshot race | `tables_to_show/README.md`: authoritative NV had **S3=4** throughout |
| Pre-policy Step 5 totals 70/5/8 | `results_committee_case/step05_*` (2026-07-14) | Marker-gap: **51/4/4** |

**Rule for synthesis:** use only `marker_gap_policy_ex09_13` + slide45 (2026-07-30) for numbers. Flag July-18 packs as historical.

---

## D12 vs D13 coverage (locks primary contrast)

- **T1→T2 (D12):** coverage **adequate** for all four participants.
- **T1→T3 (D13):** coverage **limited** for 671, 252, 651; adequate only for 790.
- `rep_pass` True only for 671 T2.

**Synthesis rule:** D12 is the shared primary comparison; D13 is supplemental with coverage flags. Do not cherry-pick the strongest contrast per participant for the shared matrix.

---

## Persistence (descriptive)

Source: `step09_persistence_t2_t3/persistence_summary.md`

| Pid | Persistent A2 links T2∩T3 | Note |
|---|---|---|
| 671 | 6 | Strongest temporal continuity |
| 790 | 1 (`LFArm_to_LHand`) | Mostly transient T2 |
| 252 | 0 | Broad T3 emergent pattern |
| 651 | 0 | Transient / emergent only |

---

## Synthesis implications

1. **SUPPORTED ceiling for JcvPCA:** A2 (S2) with coverage stated; participant-specific.
2. **A3 / amplitude-independent whole-body reorganization:** not formally supported.
3. **“Organization” language:** allowed as Step-5 descriptive mechanism among NV-exceeding links; never as synonym for A3/S3.
4. **Redistribution ≠ DOF unfreezing** (CLAIMS + Chang/Newell guardrails).
