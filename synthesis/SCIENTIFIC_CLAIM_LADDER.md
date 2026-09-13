# Scientific claim ladder

Purpose: define what the thesis may write. Project evidence is source of truth; Chang/Newell/Verrel are guardrails only.

---

## SUPPORTED

Claims with direct, role-appropriate evidence in the authoritative stacks:

1. **Participant-specific longitudinal kinematic change** exists in JcvPCA A2 (S2) links for all four participants at D12 (counts: 671=8, 790=7, 651=4, 252=3), relative to each participant’s own T1 R1–R2 signed NV.
2. **Link-specific redistribution** of relative contribution within T1’s retained subspace for those A2 links (anatomical localization via link IDs in `NV_PROFILE.csv`).
3. **Selected changes exceed method-specific within-session repetition variability** — JcvPCA S2/A2; Conv embedding \|Δ\| > Drep for 651/790/671 (671 sparse cells) at D12; 252 Conv D12 ≤ Drep.
4. **Participant/timepoint patterns differ** (no shared cohort direction): e.g. 671 unique S3 candidates + persistence; 252 D12 Conv weak vs D13 Conv strong; 651 heavy exclusions + strong Conv D12.
5. **D12 has more consistent JcvPCA coverage** than D13 across the four participants (adequate for all at D12).
6. **Conv reliability gate PASSES** at cohort level; masked_angular_velocity is the selected objective; masked_6D failed.
7. **Transformer does not outperform Conv** on the locked comparison (`ARCHITECTURE_RECOMMENDATION.json`).
8. **RQA Stage 2 is technically valid** (surrogates/truncation/sensitivity) but **not promoted** as a primary longitudinal measure (`LIMITED_PASS_STOP`; 0 z-score novel cases).
9. **Step-5 mechanism labels:** among NV-exceeding links, organization predominates (51/4/4) — **descriptive only**, not A3.

---

## CONSISTENT WITH, BUT NOT PROVEN

Allowed only as cautious interpretation, never as demonstrated fact:

1. **Longitudinal motor adaptation** (participant-specific) — change exceeds repetition floors in multiple constructs for some participants, but adaptation as a process is not experimentally isolated.
2. **Coordination reorganization / redistribution language** beyond A2 metrics — especially where Step-5 organization labels co-occur with A2; still not A3.
3. **Selected local coupling / symmetry / entropy shifts** (explicit features) accompanying latent or JcvPCA change — descriptive complementarity.
4. **Local freedom with whole-body organisation** — Chang-style analogy only; not measured with Chang-equivalent joint-angle r0.
5. **Increased independence of selected local DOF** — not directly measured; do not infer from dimensionality alone (Newell).
6. **RQA temporal complementary interpretation** for 651–ex13–D12 and 790–ex11–D12 (amp-preserving only).

---

## NOT SUPPORTED

Do **not** write as established results:

1. **Group-level intervention / learning effect** across participants.
2. **Causal Gaga effect.**
3. **Psilocybin effect** on movement coordination.
4. **Shared whole-cohort direction** of change.
5. **Global increase in motor flexibility.**
6. **Global unfreezing of DOF** / Bernstein stage progression as proven in this dataset.
7. **Amplitude-independent whole-body coordination reorganization as A3** — S3 only in 671 T2 (4 links) and **supervisor sign-off pending**; `51 organization ≠ A3`.
8. **Task-variable stabilisation improvement** (Verrel layer not measured).
9. **“Better learning” from ↑ or ↓ effective dimensionality / participation entropy** (Newell: direction is constraint-dependent).
10. **JcvPCA redistribution = stronger local joint coupling** (Chang: can diverge).
11. **Equivalence of JcvPCA NV, Conv Drep, and RQA Drep** as numerical quantities.
12. **Promotion of RQA or Transformer or PCA** to primary longitudinal outcomes.

---

## Thesis wording templates

**Allowed:**  
> “In participant 671, eight links showed T1→T2 contribution changes that exceeded that participant’s T1 R1–R2 signed natural variability and were direction-stable (A2), with adequate coverage and repetition-pass robustness; four of these met the S3 candidate stack pending supervisor interpretation.”

**Forbidden:**  
> “Participants showed motor learning and DOF unfreezing under Gaga, confirmed by 51 organization findings and Conv/RQA agreement.”
