# Stage 2 Method Report

**Branch:** `exploratory/guided-rqa-stage2`  
**Stage 1 freeze:** `rqa-stage1-feasibility-pass-v1` @ `120 Hz lock`  
**Scientific freeze untouched:** `guided-analysis-freeze-v1` @ `5062e22`

## Scope

- Participants: 651, 790
- Exercises: ex11, ex13
- Timepoints: T1, T2, T3
- Repetitions: R1, R2
- Primary method: regional Auto-RQA on angular-velocity-magnitude dynamics
- Views: amplitude-preserving (fixed radius); trial z-score (target RR)

## Locked parameters (not retuned on T2/T3)

| Parameter | Value |
|---|---|
| Rate | 120 Hz |
| τ | 18 frames (0.15 s) |
| m | 4 |
| Embed span | 0.45 s |
| Radius (amp-preserving) | 0.35 × mean distance |
| Target RR (z-score) | 0.03 |
| Theiler | 18 |
| Lmin | 2 (+ sensitivity 3) |
| Block shuffle | 0.3 s |

## Metrics

Primary: RR (fixed-radius only), DET, Lmean, LAM, ENTR.  
Secondary: Lmax/N_embed, ε (target-RR), Lmean in seconds.

## Language

Analyses concern **regional angular-velocity-magnitude dynamics** and **multiregional angular-velocity states** (MdRQA). Not posture/pose/motif recurrence.
