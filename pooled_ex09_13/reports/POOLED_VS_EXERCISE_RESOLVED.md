# Pooled vs exercise-resolved comparison

Exercise-resolved synthesis source: `synthesis/CROSS_METHOD_PARTICIPANT_MATRIX.md`, `COUPLING_INTERPRETATION_SUMMARY.md`.

## 671

- Exercise-level coupling was mixed (ex12 ↑ trunk–arm, ex10 ↓ regional, ex09 stable).
- Pooled coupling **transforms but does not cancel**: regional=EXCEEDS/DECREASE; trunk_arm=EXCEEDS/INCREASE.
- JcvPCA remains the strongest stack (A2=8, S3=4). Conv=LIMITED (3/6 interpretable).
- Classification: **JCVPCA_DOMINANT** (pooling does not create balanced multimethod convergence).

## 651

- Exercise-level: ex13 was a multi-method hotspot (Conv, RQA complementary, trunk–arm ↑).
- Pooled block: Conv=EXCEEDS (median ratio 7.572446640861111); trunk_arm=EXCEEDS/INCREASE (Δ=0.0969 vs ex13 cell ~+0.13).
- Pooled trunk–arm ↑ survives equal-weight aggregation but is **weaker than the ex13 cell** → interpret ex13 as a **localized driver** that still contributes block-wide, not a purely cancelled local effect.
- JcvPCA A2 remains 4/10 (exclusions unchanged). Class: **POOLED_MULTIMETHOD_CONVERGENCE** (JcvPCA + Conv + trunk–arm).

## 790

- Exercise-level: ex11 RQA complementary but coupling unreliable; ex13 regional ↓ robust.
- Pooled: regional=LIMITED/DECREASE; trunk_arm=EXCEEDS/INCREASE.
- Pooling neither fully stabilizes nor erases mixed evidence; RQA full-block not computable from Stage1 cache.

## 252

- Exercise-level: modest D12 JcvPCA; Conv D12 ≤Drep; mixed coupling cells.
- Pooled: regional=EXCEEDS/DECREASE; trunk_arm=LIMITED/INCREASE; Conv D12 ≤Drep; D13 stronger.
- D12/D13 method discrepancy **preserved**, not resolved by pooling.

## Pooled coupling D12 facts

- 252 `regional_coupling`: EXCEEDS DECREASE (Δ=-0.0539, Drep=0.0093)
- 252 `trunk_arm_lagged_coupling`: LIMITED INCREASE (Δ=0.0234, Drep=0.0336)
- 651 `regional_coupling`: LIMITED INCREASE (Δ=0.0098, Drep=0.0110)
- 651 `trunk_arm_lagged_coupling`: EXCEEDS INCREASE (Δ=0.0969, Drep=0.0252)
- 671 `regional_coupling`: EXCEEDS DECREASE (Δ=-0.0484, Drep=0.0049)
- 671 `trunk_arm_lagged_coupling`: EXCEEDS INCREASE (Δ=0.0617, Drep=0.0197)
- 790 `regional_coupling`: LIMITED DECREASE (Δ=-0.0543, Drep=0.0926)
- 790 `trunk_arm_lagged_coupling`: EXCEEDS INCREASE (Δ=0.0434, Drep=0.0110)
