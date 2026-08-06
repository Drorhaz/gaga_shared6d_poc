# Stage 2 Gate Report

# Decision: `LIMITED_PASS_STOP`

## Gate inputs

| Check | Value |
|---|---|
| Qualified pid×ex×delta (z-score novel/complementary) | 0 |
| Amp-preserving complementary pid×ex×delta | 2 |
| Novel z-score rows | 0 |
| Full-shuffle DET drop median | 0.924 |
| Surrogate OK | True |
| Truncation OK | True |
| Sensitivity OK | True |

## Secondary analyses

- Compact MdRQA median DET drop vs shuffle: 0.923
- CRQA trunk–arms median DET drop (shuffle-one): 0.890
- CRQA run as a limited trunk–arm coordination check; interpret relative to existing `trunk_arm_lagged_coupling`.

## Sensitivity summary

| setting | median_abs_dDET | median_abs_dLAM | median_abs_dLmean | sign_agree_DET_frac |
| --- | --- | --- | --- | --- |
| lmin3_amp_preserving | 0.0473 | 0.0240 | 0.8061 | 1.0000 |
| tau_17 | 0.0008 | 0.0005 | 0.1505 | 1.0000 |
| tau_19 | 0.0008 | 0.0005 | 0.1312 | 1.0000 |
| radius_0.3 | 0.0069 | 0.0036 | 0.9001 | 1.0000 |
| radius_0.4 | 0.0048 | 0.0022 | 0.9247 | 1.0000 |


## Interpretation of this decision

`LIMITED_PASS_STOP`: Stage 2 is technically valid (surrogates, truncation, sensitivity), and two amp-preserving complementary pid×exercise×delta cases exist (651–ex13–D12; 790–ex11–D12), but **no z-score-qualified novelty cases** clear the median `|Δ|/Drep > 1` bar. Therefore RQA does not yet justify Stage 3 expansion.

## Stop

Stage 3 is **not** started and is **not recommended** from this gate without new evidence or protocol revision.

## Limitations

- N=2 participants in Stage 2; session–timepoint confounding remains.
- DET near ceiling under amp-preserving view; z-score/target-RR and Lmin=3 sensitivity mitigate over-reading.
- R1/R2 is within-session variability, not a full noise floor.
