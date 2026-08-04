# Stage 0B-A2 — Guided sequence segmentation

## Critical namespace note

In this project, **P1 in session keys (`*_T*_P1_R*`)** means **Task Part 1**, not a progressive improvisation cue stage. Source annotations provide **exercise_id boundaries (ex01–ex17)**, not P1–P5 progressive instruction labels within Group4.

Group4 (ex09–ex13) is labeled **Curvilinear exploration** in `gaga_jcvpca/configs/exercise_map.yaml`. No validated cue-timed sub-stage map exists for finer progressive instructions.

## Supported analysis units

| Unit | Supported? | Notes |
|---|---|---|
| Exercise ex09–ex13 | **Yes** | Authoritative segmentation workbook |
| Full Group4 aggregate | **Yes** | Equal-weight exercise mean (S7) |
| P1–P5 progressive stages | **No** | Not in source annotations |
| Early/middle/late thirds within exercise | **Yes (derived)** | Temporal thirds of windows; not cue labels |
| Transitions between exercises | **Limited** | Boundaries exist; transition windows not specially annotated |

## Coverage summary (evaluation windows)

| Exercise | Focus | n blocks | mean dur (s) | mean eval windows | frac suitable |
|---|---|---|---|---|---|
| ex09 | Curvilinear exploration (Group4 start) | 24 | 9.1 | 4.2 | 100% |
| ex10 | Curvilinear exploration (Group4) | 24 | 10.5 | 5.0 | 100% |
| ex11 | Curvilinear exploration (Group4; breakdown exercise) | 24 | 10.5 | 5.0 | 100% |
| ex12 | Curvilinear exploration (Group4) | 24 | 8.8 | 4.1 | 100% |
| ex13 | Curvilinear exploration (Group4 end) | 24 | 14.4 | 6.8 | 100% |

Full table: `outputs/stage0b_guided_closeout/guided_segmentation.csv`.

**Decision:** Do not invent P1–P5 labels. Localize with exercise + early/mid/late thirds.
