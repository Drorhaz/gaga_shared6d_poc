# S7 readiness recommendation

**Stop gate before S8.** Direction similarity / sign-flip analysis has not begun.

---

## Answers

### 1. Did Conv pass the T1/T2/T3 reliability re-gate?

**Yes.** Mean skills
T1=0.0010, T2=0.0219,
T3=0.0180; positive-cell fractions
75%/92%/79%.

### 2. What is the primary representation for downstream work?

**ConvMaskedPredictor** on `masked_angular_velocity`, mask 30%, deterministic
32-D mean-pool embedding. PCA and explicit features remain references.

### 3. Were embeddings and change vectors computed under the frozen rules?

**Yes.** Training-T1-only balanced standardization; exercise-balanced recording
aggregation; raw and standardized geometries co-primary; no whitening; no L2
normalisation of embeddings.

### 4. How many cells are interpretable?

D12: 18/24; D13:
16/24; D23:
18/24.
Failed cells must be excluded from any S8 direction claim that uses them.

### 5. Should S8 proceed?

**Eligible to proceed after review**, using:

* Conv embeddings and change vectors from `outputs/s7_conv/`;
* both raw-centred and standardized geometries as co-primary;
* only interpretable cells (both endpoints `skill > 0`);
* pre-registered sign-flip analysis with floor p = 0.125 and descriptive-only
  framing at N = 4.

Do **not** begin S8 until this report is reviewed. Do not treat change-magnitude
ratios as direction similarity.

---

## Recommendation

| Item | Value |
|---|---|
| Reliability re-gate | PASS |
| Primary representation | Conv / masked_angular_velocity |
| S7 status | done |
| S8 status | **stopped pending review** |

Artifacts: `outputs/s7_conv/`, `figures/s7_conv/`,
`reports/S6B_CONV_RELIABILITY_GATE.md`, `reports/S7_EMBEDDING_CHANGE_REPORT.md`.
