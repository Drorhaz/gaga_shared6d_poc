# Cache invalidation notice

**Status: binding rule for this project.**

Certain cached rotation features in the read-only source project
`../gaga_jcvpca` are **invalid for longitudinal analysis** and must not be used
in any subsequent stage of `gaga_shared6d_poc`. This notice records which ones,
why, the measured magnitude of the problem, and what replaces them.

Evidence: `outputs/s2_extract/cache_comparison.csv`,
`outputs/s2_extract/chain_composition_checks.csv`, and the registry field
`skeleton_variant` in `data/immutable/recording_registry.csv`.

---

## 1. The rule

> The cached rotation matrices in `gaga_jcvpca/outputs/cache/matrices/*.parquet`,
> and any feature derived from them, **must not be used as input** to any stage
> of this project. They may be read **only** as a validation reference for
> recordings whose skeleton template matches the assumption baked into that
> cache.

Stages S5 through S10 must draw exclusively from
`data/immutable/rotvec_18link/*.parquet`, produced by `scripts/s2_extract.py`
from the raw quaternions and checksummed in
`data/immutable/INPUT_MANIFEST.json`.

The reason is not that the cache is sloppily made. On 378 of 384 comparable
link-recordings it agrees with a fresh independent extraction **bit-identically**
(0.000e+00 rad). The problem is narrower and more dangerous than general
inaccuracy: it is a defect that appears *only in some timepoints of some
participants*, which is precisely the axis this study measures.

---

## 2. Root cause: the skeleton template changes mid-study

The Motive solved-skeleton template is not constant across the study.

| Participant | T1 | T2 | T3 |
|---|---|---|---|
| 252 | 55-bone | 55-bone | 55-bone |
| 651 | **51-bone** | 55-bone | 55-bone |
| 671 | **51-bone** | **51-bone** | 55-bone |
| 790 | 55-bone | 55-bone | 55-bone |

The 55-bone template carries `Spine2`, `Spine3`, `Spine4` and `Neck2`; the
51-bone template does not. The root bone is renamed at the same moment:
`651:651` becomes `651_T2:651_T2`, and `671:671` becomes `T3_671:T3_671`.

The source project's link map is fixed **per participant**. When the template
changes at a timepoint boundary, that fixed map silently changes meaning at the
same boundary. A template artifact is therefore perfectly confounded with
longitudinal change.

---

## 3. Affected recordings

Six recordings, all of them post-baseline:

| Recording | Template | Consequence in the cache |
|---|---|---|
| `651_T2_P1_R1` | 55-bone | 3 pelvis links dropped; `Ab_to_Chest` absent; head-neck mislabelled |
| `651_T2_P1_R2` | 55-bone | same |
| `651_T3_P1_R1` | 55-bone | same |
| `651_T3_P1_R2` | 55-bone | same |
| `671_T3_P1_R1` | 55-bone | `Ab_to_Chest` absent; head-neck mislabelled |
| `671_T3_P1_R2` | 55-bone | same |

The pattern is what makes this severe. For participant 651 the defect starts at
T2, so **every** longitudinal contrast for 651 (T1 vs T2, T1 vs T3) compares a
clean baseline against defective follow-ups. For 671 it starts at T3, so T1 vs
T3 and T2 vs T3 are affected while T1 vs T2 is not.

### 3.1 Pelvis links silently dropped

Three links are missing entirely from the cache for the four 651 recordings:

* `pelvis_to_Ab`
* `pelvis_to_LThigh`
* `pelvis_to_RThigh`

Cause: cached pelvis columns are named after the literal root bone, so the
column stem is `651_to_Ab` at T1 but must be `651_T2_to_Ab` at T2. The lookup
misses and the link is dropped rather than raising.

Effect: the cached feature space for `651-T2` and `651-T3` contains **14 links**
where `651-T1` contains 18. Pelvis orientation and both hip links vanish from
the follow-up timepoints of one participant only. Any distance computed between
T1 and T2 for 651 is computed over a different feature set at each end.

This is also the origin of the misleading `14link` and `16link` filenames in
`data/feature_manifests/`; the manifests themselves contain 18 and 22 links
respectively, and were renamed to their true counts on copy into this project.

### 3.2 Head-neck naming mismatch

For all six affected recordings, the cache column `Neck_to_Head` does **not**
contain the `Neck -> Head` rotation. It contains `Neck2 -> Head`: only the
final sub-link of the two-joint neck chain.

This was not inferred. It was tested directly: recomputing `Neck2 -> Head` from
the raw quaternions reproduces the cached `Neck_to_Head` column to
**0.000e+00 rad**, bit-identically, while the true `Neck -> Head` endpoint
rotation differs from it substantially.

**Observed error magnitude**, cached column versus true endpoint rotation:

| Recording | Max difference | Mean difference |
|---|---|---|
| `651_T2_P1_R1` | 0.7177 rad = **41.1 deg** | 0.2039 rad = 11.7 deg |
| `651_T2_P1_R2` | 0.6182 rad = 35.4 deg | 0.1898 rad = 10.9 deg |
| `651_T3_P1_R1` | 0.5497 rad = 31.5 deg | 0.1651 rad = 9.5 deg |
| `651_T3_P1_R2` | 0.5482 rad = 31.4 deg | 0.1653 rad = 9.5 deg |
| `671_T3_P1_R1` | 0.4433 rad = 25.4 deg | 0.1548 rad = 8.9 deg |
| `671_T3_P1_R2` | 0.4397 rad = 25.2 deg | 0.1551 rad = 8.9 deg |

A mean discrepancy of 9 to 12 degrees, peaking at 41 degrees, on a link whose
own median range of motion is 16.4 degrees. The systematic error therefore
exceeds the typical signal on that link, and it is present only at
post-baseline timepoints.

---

## 4. How canonical endpoint-relative extraction resolves this

The 18 canonical links are defined by **anatomical endpoints**, not by adjacency
in whatever template a given recording happens to use, and each endpoint is
resolved against that recording's own hierarchy at read time:

```text
q_rel = inv(q_parent_endpoint_global) * q_child_endpoint_global
```

Three properties follow, and each was verified rather than assumed.

**The spanning links are handled without a chain product.** A parent-relative
chain telescopes, so

```text
R(Ab->Spine2) . R(Spine2->Spine3) . R(Spine3->Spine4) . R(Spine4->Chest)
    = R(Ab->Chest) = inv(R_Ab_global) . R_Chest_global
```

Verified on all 18 recordings that carry the intermediates: 36 checks,
**worst error 3.735e-14 degrees**. So `Ab_to_Chest` and `Neck_to_Head` are
obtained on the 55-bone template with no accumulation of error and no special
case, and they are the *same anatomical quantity* as on the 51-bone template.

**The root is resolved by hierarchy, not by name.** `pelvis` is the
self-parented bone, so the rename from `651:651` to `651_T2:651_T2` is
irrelevant and the three pelvis links are never lost.

**The head-neck link is the true endpoint rotation.** `Neck_to_Head` here means
`Neck -> Head`, composed through `Neck2` where `Neck2` exists, and native where
it does not. The alias is not used.

Net result, confirmed by the clean reproduction: **all 24 recordings yield the
same 18 anatomical links**, from both templates, by one identical operation.
Per-recording link count is 18 with no exceptions.

---

## 5. Permitted use of the cache

The cache retains exactly one legitimate role: an **independent validation
reference**, which is how S2 uses it. Reimplementing the extraction from raw
quaternions and recovering 378 bit-identical matches is strong evidence that
the rotation convention, multiplication order, axis handling, sign-continuity
treatment and filter design in this project are all correct.

That evidence is only meaningful where the cache is itself correct, so the
comparison is classified rather than pooled: exact agreement, alias-explained,
or unexplained. Only the count of **unexplained** disagreements is gated, and
it is zero.

**Permitted:** reading the cache in S2 to validate extraction.
**Not permitted:** using the cache, or anything derived from it, as an input to
S5, S6, S7, S8, S9 or S10.

---

## 6. Scope of the warning beyond this project

Any longitudinal analysis in `gaga_jcvpca` that consumed
`outputs/cache/matrices/` for participants 651 or 671 should be treated as
suspect, because for those participants the feature set and the head-neck
definition both change at a timepoint boundary. This notice is a statement
about the cache, not a request to modify the source project, which remains
read-only for this work.
