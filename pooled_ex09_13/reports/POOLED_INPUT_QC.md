# Pooled input QC

- Segment rows (ex09–13): **120** (expect 120)
- Recording units: **24** (expect 24)
- Exercises per unit: Counter({5: 24})

## Boundary checks
- All evaluation windows verified ⊆ [start_frame, end_frame) for their exercise.
- No synthetic continuity between exercises.

## Per-unit sample counts

| pid | T | R | n_frames sum | n_windows sum |
|---|---:|---:|---:|---:|
| 252 | 1 | 1 | 6120 | 23 |
| 252 | 1 | 2 | 6594 | 25 |
| 252 | 2 | 1 | 6360 | 25 |
| 252 | 2 | 2 | 6600 | 25 |
| 252 | 3 | 1 | 6120 | 25 |
| 252 | 3 | 2 | 6120 | 24 |
| 651 | 1 | 1 | 6000 | 24 |
| 651 | 1 | 2 | 6120 | 24 |
| 651 | 2 | 1 | 6240 | 25 |
| 651 | 2 | 2 | 6480 | 26 |
| 651 | 3 | 1 | 6240 | 24 |
| 651 | 3 | 2 | 6240 | 24 |
| 671 | 1 | 1 | 6240 | 26 |
| 671 | 1 | 2 | 6360 | 24 |
| 671 | 2 | 1 | 6360 | 24 |
| 671 | 2 | 2 | 6840 | 27 |
| 671 | 3 | 1 | 6600 | 27 |
| 671 | 3 | 2 | 6840 | 28 |
| 790 | 1 | 1 | 6240 | 25 |
| 790 | 1 | 2 | 6600 | 26 |
| 790 | 2 | 1 | 6360 | 25 |
| 790 | 2 | 2 | 6480 | 26 |
| 790 | 3 | 1 | 6840 | 27 |
| 790 | 3 | 2 | 6360 | 25 |
