# S5 mask-ratio sweep

Fold **A**, seed **0**, scored on **held-out T1 early-stop blocks only**.
T2/T3 were not viewed for selection.

---

## Sweep table (held-out T1 skill)

| Mask ratio | `masked_6d` skill | `masked_angular_velocity` skill |
|---|---|---|
| 30% | −1.123 | **+0.036** |
| 50% | −0.754 | **+0.043** |
| 70% | −0.470 | +0.021 |

Parameter count: 14,342 (`masked_6d`) / 14,237 (`masked_angular_velocity`).

Figure: `figures/s5_masksweep/mask_ratio_sweep.png`.

---

## Selection

**Frozen mask ratio: 30%.**

Rule applied:

1. Prefer ratios with positive skill on at least one objective
   (`masked_6d` is negative at all ratios — the conv model loses to
   mean-motion / interpolation on 6D reconstruction).
2. Score = mean skill over positive-skill objectives only
   → here just `masked_angular_velocity`.
3. Best score 0.0426 at 50%; 30% is within 0.02 (0.0357).
4. Tie → **lowest ratio (conservative)**.

Documented uncertainty: 30% and 50% are effectively tied for velocity; 70% is
worse for velocity even though it is least-bad for the failed 6D objective.
Mean-of-both-objectives would have wrongly preferred 70% by diluting a failed
pretext into the vote; that rule was rejected.

Written to `configs/experiment.yaml` as `s5.frozen_mask_ratio: 0.3` and
`outputs/s5_masksweep/SELECTED_MASK_RATIO.txt`.

---

## Interpretation

* **6D reconstruction is a failed pretext for this conv model** at all mask
  ratios (skill < 0). Interpolation of continuous 6D at 120 Hz is a very strong
  trivial baseline.
* **Angular-velocity prediction shows weak but positive skill** (~3–4%).
* The frozen 30% ratio is the conservative choice in a near-tie. Full S5 runs
  use this value only; it will not be retuned after seeing T2/T3.
