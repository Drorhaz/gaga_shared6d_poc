# S6b ConvMaskedPredictor reliability re-gate

Re-evaluation of the **selected** architecture/objective from S5–S6:

* model: `ConvMaskedPredictor`
* objective: `masked_angular_velocity`
* mask ratio: 30% (frozen)
* skill vs best matched trivial baseline (mean-motion / interpolation)

Same cell structure as the Transformer reliability table: participant × fold × seed
(24 cells). Held-out T1 = early-stop blocks; T2/T3 = evaluation windows at the
fold’s trajectory repetition.

---

## Proceed / stop rule (operational)

```text
PASS iff
  mean skill(T1) > 0 AND mean skill(T2) > 0 AND mean skill(T3) > 0
  AND fraction of cells with skill > 0 is ≥ 50% at each of T1, T2, T3
```

Per-cell `skill ≤ 0` still forbids interpreting that cell’s latent geometry.

---

## Observed summary

| Metric | T1 held-out | T2 | T3 |
|---|---|---|---|
| Mean skill | 0.0010 | 0.0219 | 0.0180 |
| Fraction skill > 0 | 75.00% | 91.67% | 79.17% |
| Cells fail_nonpositive | 6 | 2 | 5 |

**Gate result: `PASS`**

---

## Cells that fail the zero-crossing

```
participant fold  seed  gate_T1_heldout          gate_T2          gate_T3  skill_T1_heldout  skill_T2  skill_T3
        671    A     0         positive  positive_stable fail_nonpositive          0.035798  0.043114 -0.027081
        651    A     1 fail_nonpositive  positive_stable  positive_stable         -0.003316  0.035556  0.029281
        671    A     1         positive  positive_stable fail_nonpositive          0.028638  0.044849 -0.023656
        671    B     0 fail_nonpositive  positive_stable fail_nonpositive         -0.102640  0.031206 -0.108159
        790    B     0 fail_nonpositive fail_nonpositive  positive_stable         -0.018196 -0.041010  0.040086
        671    B     1 fail_nonpositive  positive_stable fail_nonpositive         -0.037554  0.020571 -0.016797
        671    B     2 fail_nonpositive  positive_stable  positive_stable         -0.389354  0.037795  0.027797
        790    B     2 fail_nonpositive fail_nonpositive fail_nonpositive         -0.003869 -0.187912 -0.001659
```

Full table: `outputs/s7_conv/reliability_t1_t2_t3.csv`  
Figure: `figures/s7_conv/reliability_t1_t2_t3.png`

---

## Interpretation

* Observed skill at T1/T2/T3 is positive on average with majority of cells clearing the zero-crossing.
* Failed cells must not be used for latent-direction interpretation.
* S7 proceeded with Conv as primary representation.
