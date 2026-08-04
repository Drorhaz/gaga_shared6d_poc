# S8 direction similarity report

Primary representation: **ConvMaskedPredictor** / `masked_angular_velocity` / mask 30%.
Reliability-qualified inputs only (both endpoints `skill > 0`). Latent coordinates
are never averaged across folds or seeds.

## Inclusion (observed)

| Delta | Geometry | n sufficient runs | Mean of mean-pairwise | % runs with mean>0 |
|---|---|---|---|---|
| D12 | raw | 4 | -0.091 | 25% |
| D12 | std | 4 | -0.124 | 25% |
| D13 | raw | 3 | 0.020 | 33% |
| D13 | std | 3 | 0.125 | 100% |
| D23 | raw | 5 | 0.271 | 60% |
| D23 | std | 5 | 0.248 | 60% |

Full inclusion table: `outputs/s8_direction/inclusion_table.csv`.

## Derived — pairwise similarity

See `similarity_summary.csv`, `pairwise_cosines.csv`, `consensus_projections.csv`.

Raw vs standardized same-sign agreement: **71%**.
Both positive: **29%**.

## Interpretation

insufficient stable shared direction, but enough reliable cells to complete Stage 0 controls and GO/NO-GO (LIMITED / METHOD path)

Shared-direction evidence flag: **False**.

Δ12, Δ13 and Δ23 are not independent (`Δ23 = Δ13 − Δ12`). N=4 forbids population inference.

## Status

S8 complete. Continuation to S9/S10: **True**.
