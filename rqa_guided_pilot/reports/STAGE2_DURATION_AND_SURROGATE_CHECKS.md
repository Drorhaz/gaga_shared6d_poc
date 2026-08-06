# Stage 2 Duration and Surrogate Checks

## Surrogates (amp-preserving Auto-RQA)

| Control | median DET drop | median LAM drop | median Lmean drop |
|---|---|---|---|
| Full shuffle | 0.924 | 0.904 | 4.267 |
| Block shuffle | 0.037 | 0.013 | 1.864 |

Full shuffle remains the primary negative control. Block shuffle is graded (weaker DET effect under near-ceiling DET).

## Duration truncation

Median |ΔDET| (trunc − primary): **0.0003**

Raw Lmax is diagnostic only; Lmean / Lmax·N⁻¹ used for claims.
