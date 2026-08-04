# S9 final controls and representation comparison

No new architectures or objectives. Comparisons use existing S5–S8 artifacts.

---

## Observed — identity and pretext skill

| Representation | Identity probe (chance 0.25) | Held-out T1 skill (velocity) |
|---|---|---|
| PCA (d=32) | 0.841 | n/a (not a masked predictor) |
| Conv | 0.446 ± 0.045 | 0.0359 ± 0.0045 |
| Transformer (sensitivity) | (see S6) | 0.0292 |

Conv is less identity-dominated than PCA and is the only learned model with a
matched trivial-baseline skill > 0 under the selected objective.

## Observed — reliability and change vs repetition (Conv)

| | T1 | T2 | T3 |
|---|---|---|---|
| Fraction skill > 0 | 75% | 92% | 79% |

| Delta | n interpretable | median \|Δ\|/Drep | fraction > 1 |
|---|---|---|---|
| D12 | 18 | 1.53 | 67% |
| D13 | 16 | 2.48 | 81% |

## Observed — direction similarity (from S8)

Shared-direction evidence: **False**.

Stability (raw mean pairwise): D12=-0.091
(25% runs >0);
D13=0.020
(33% runs >0).

Jackknife sign-flip rate: 46%.

Transformer sufficient direction runs: 13;
mean pairwise among them: 0.085.

## Interpretation

1. **Conv adds something beyond PCA** for representation quality: positive
   masked-velocity skill and substantially lower identity probe accuracy.
2. **Conv does not establish a stable shared direction** across participants
   after reliability gating (S8).
3. **Individual change often exceeds repetition variability** in interpretable
   cells — the instrument is more useful within-participant than across.
4. Explicit features remain the interpretable reference; amplitude-controlled
   entropy residuals from S5 are small and must not be over-read at N=4.
5. Session–timepoint confounding is unresolved: T1/T2/T3 are single sessions.

Artifacts: `outputs/s9_final/representation_comparison.json`.
