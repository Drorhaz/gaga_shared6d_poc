# S6 reconstruction reliability gate (T1 / T2 / T3)

Evaluated **after** objective and architecture-relevant held-out-T1 decisions
were frozen. Objective: `masked_angular_velocity`. Model: trained
`SharedMotionTransformer` checkpoints (reported for completeness; architecture
recommendation still prefers conv — see readiness report).

Gate states (zero-crossing only; no new degradation threshold):

* `skill ≤ 0` → `fail_nonpositive` — do not interpret latent geometry
* `skill > 0` but below paired held-out T1 → `positive_degraded` — usable with caution
* `skill > 0` and ≥ paired held-out T1 → `positive_stable`

Per cell: participant × fold × seed (24 cells). Trajectory repetition follows
the fold definition (A→R2, B→R1). Held-out T1 = early-stop blocks; T2/T3 =
evaluation windows at the trajectory repetition.

---

## Observed summary

| Gate | T1 held-out | T2 | T3 |
|---|---|---|---|
| positive / positive_stable | 19 | 13 | 13 |
| positive_degraded | — | 8 | 7 |
| fail_nonpositive | **5** | **3** | **4** |

---

## Cells that fail the reliability gate

| Participant | Fold | Seed | T1 | T2 | T3 |
|---|---|---|---|---|---|
| 671 | A | 0 | ok | ok | **fail** |
| 651 | A | 1 | **fail** | ok | ok |
| 671 | A | 1 | ok | ok | **fail** |
| 671 | A | 2 | ok | **fail** | ok |
| 671 | B | 0 | ok | ok | **fail** |
| 790 | B | 0 | **fail** | **fail** | ok |
| 671 | B | 1 | **fail** | ok | ok |
| 671 | B | 2 | **fail** | ok | ok |
| 790 | B | 2 | **fail** | **fail** | **fail** |

Most frequent failures: **671** (especially T3 under Fold A; T1 under Fold B)
and **790** under Fold B. Participant **252** never fails the zero-crossing in
this table; **651** fails once (Fold A seed 1 T1).

Full table: `outputs/s6_transformer/reliability_t1_t2_t3.csv`.
Figure: `figures/s6_transformer/reliability_t1_t2_t3.png`.

---

## Interpretation

1. Held-out T1 skill is weak (~1–3% for most Transformer runs) and does not
   transfer uniformly to every participant × timepoint cell.
2. Several T2/T3 cells remain positive; several do not. Latent geometry must
   be restricted to cells with `skill > 0`.
3. Because the Transformer did not beat the conv baseline on held-out T1, any
   S7–S8 analysis should **prefer the convolutional checkpoints** and re-run
   this same reliability table on those before interpreting directions.
4. No shared longitudinal direction analysis was performed in S6.

---

## Status

Reliability diagnostics recorded. **Stop before S7–S8** pending review of the
readiness recommendation.
