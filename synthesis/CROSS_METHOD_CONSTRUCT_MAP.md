# Cross-method construct map

## Evidence roles (locked)

| Method | Role(s) | Unique contribution |
|---|---|---|
| **JcvPCA** | DETECTION · ANATOMICAL_LOCALIZATION · INTERPRETATION | Link-specific redistribution of contribution to whole-body coordination structure in T1 subspace |
| **Conv** | DETECTION · EXERCISE_LOCALIZATION | Independent learned detector that longitudinal dynamics changed; which exercises drive \|Δ\| |
| **Explicit features** | INTERPRETATION | Biomechanical / coordination descriptors (energy shares, entropy, dimensionality, symmetry, regional coupling) |
| **RQA** | TEMPORAL_CHARACTERIZATION | Recurrence / predictability of movement-intensity dynamics (not promoted as primary longitudinal) |
| **Transformer** | SENSITIVITY | Whether architecture choice alters detection relative to Conv |
| **PCA (S5)** | REFERENCE | Linear identity separability baseline — not a longitudinal outcome |
| **Task-variable stabilisation** | — | **NOT MEASURED** (Verrel layer absent) |

---

## What each method uniquely tells us

### JcvPCA
Which links changed their relative contribution beyond T1 R1–R2, with direction stability (A2/S2), coverage, and (rarely) S3 candidacy. Primary anatomical localization method.

### Conv
Whether a held-out-skill-gated embedding change exceeds embedding Drep, and which exercises localize that change. Does **not** name links.

### Explicit features
Whether interpretable scalars (entropy, dimensionality, symmetry, regional speed coupling, etc.) also exceed their Drep, including amplitude residuals. Descriptive; direction of dimensionality change has **no universal “better” meaning** (Newell & Vaillancourt).

### RQA
Whether recurrence structure of intensity series shows amp-preserving complementary temporal patterns in selected cells. Stage 2 gate: `LIMITED_PASS_STOP`.

### Transformer
Confirms Conv preference; masked_6D failed; no additional longitudinal claim.

### PCA reference
Shows identity structure is linearly recoverable; not used as longitudinal adaptation evidence.

---

## Overlap / complementarity / redundancy

| Relation | Detail |
|---|---|
| **Complementary** | JcvPCA (where) ↔ Conv (whether / which exercise) ↔ features (what biomechanical scalars moved) |
| **Partial overlap** | Explicit regional coupling vs JcvPCA redistribution — related coordination theme, different construct |
| **Redundant if misused** | Treating Conv “yes” and JcvPCA “yes” as two votes for the same claim |
| **Not interchangeable** | JcvPCA NV ≠ Conv Drep ≠ RQA Drep numerically |

---

## Literature guardrails (mandatory)

1. **JcvPCA redistribution ≠ DOF unfreezing.**
2. **Redistribution ≠ stronger local coupling** (Chang: local coupling can weaken while whole-body structure organises).
3. **Dimensionality / entropy change has no universal better direction** (Newell & Vaillancourt).
4. **Task-variable stabilisation is NOT measured** (Verrel layer) → do not claim improved task performance control.

---

## Unresolved questions (not blocking packaging)

- Local joint-angle coupling change beyond R1/R2 (optional xcorr).
- Causal role of Gaga / psilocybin / instruction.
- Population-level effects.
- Formal A3 after supervisor sign-off.
