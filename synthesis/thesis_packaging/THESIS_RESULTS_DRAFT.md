# Results (thesis draft)

*Empirical report only. Causal and theoretical interpretation deferred to Discussion. Binding evidence hierarchy: A2 supported where gated; A3 not formally supported; `51 organization ≠ A3`.*

---

## 1. Data quality and comparison framework

Analyses were conducted as four within-participant case studies (participants 252, 651, 671, 790) using guided improvisation windows spanning exercises 09–13. Each participant was recorded at three longitudinal timepoints (T1, T2, T3), each with two within-session repetitions (R1, R2).

The primary longitudinal contrast was **T1→T2 (D12)**. **T1→T3 (D13)** was treated as supplemental evidence and interpreted with coverage flags. Under the authoritative marker-gap JcvPCA stack, D12 coverage was **adequate** for all four participants; D13 coverage was limited for 671, 252, and 651, and adequate for 790.

For JcvPCA, longitudinal change in link contribution was compared with each participant’s own T1 R1–R2 signed natural variability (NV). Parallel method-specific within-session repetition references (Drep) were used for Conv embeddings, explicit features, RQA metrics, and existing regional coupling features. These repetition references are conceptually similar but **not numerically interchangeable**.

Marker-gap policy excluded links with insufficient marker support. This reduced the analyzable link set most strongly for participant 651 (D12 denominator **n_links = 10**).

---

## 2. JcvPCA primary longitudinal results (D12)

Reference-anchored JcvPCA quantified changes in the relative contribution of body links to whole-body movement-variance structure. An A2 finding required signed longitudinal change to exceed T1 R1–R2 NV and to remain direction-stable under R1/R2 anchor swap (tier S2).

| Participant | A2 (S2) / n_links | S3 | Coverage | rep_pass |
|---|---:|---:|---|---|
| 671 | 8 / 18 | **4** | adequate | True |
| 790 | 7 / 20 | 0 | adequate | False |
| 651 | 4 / **10** | 0 | adequate | False |
| 252 | 3 / 20 | 0 | adequate | False |

Source: `09_headline_a2_summary.csv` (marker-gap policy stack).

S3 (candidate A3 stack: S2 + adequate coverage + repetition-pass robustness + Step-5 organization label) was met only for **four links in participant 671 at T1→T2**. A3 is **not** reported as a confirmed claim in these Results. Step-5 mechanism classification across cells yielded 51 organization / 4 amplitude / 4 mixed labels; these are descriptive mechanism labels and are **not** counted as A3 findings.

Persistence of A2 links between T2 and T3 was strongest for 671 (six persistent links). Participants 252 and 651 had no persistent A2 links; 790 had one (`LFArm_to_LHand`).

D13 A2 counts were 9 (671), 12 (252), 2 (651), and 3 (790), but D13 is not used as the shared primary comparison because coverage was limited for three of four participants.

---

## 3. Participant-specific JcvPCA patterns (D12)

**671.** Broadest formal D12 evidence stack: eight A2 links spanning trunk/Ab, bilateral thighs, left arm, and left distal leg links, including four S3 candidates, with adequate coverage and `rep_pass = True`.

**790.** Seven A2 links with adequate coverage (thighs, chest–shoulder, arm, and distal leg links). No S3 links; `rep_pass = False`.

**651.** Four A2 links (left forearm–hand, left upper–forearm, right shoulder–upper arm, right thigh–shin) on a reduced link set (**4/10**). No S3 links after marker-gap policy (pre-policy S3 counts for 651 are obsolete).

**252.** Three A2 links at D12 (chest–left shoulder; bilateral forearm–hand), adequate coverage, no S3. Anatomical change was present but limited in count relative to the other participants at D12.

Anatomical patterns differed across participants; no shared spatial direction is claimed.

---

## 4. Cross-method evidence (D12 primary)

### Conv (detection + exercise localization)

A convolutional model trained with a masked angular-velocity objective passed the cohort reliability gate. At D12, embedding change exceeded method-specific Drep for participants 651 (median ratio ≈ 9.25; 5/6 reliable cells), 790 (≈ 1.61; 4/6), and 671 among sparse reliable cells (≈ 1.68; **3/6**). Participant 252 showed reliable endpoints but pooled D12 change **≤ Drep** (median ≈ 0.78). Exercise localization among reliable cells emphasized ex13/ex09/ex10 for 651, ex13/ex11/ex12 for 790, and ex11/ex13/ex12 for 671 (where cells passed). Transformer architecture comparison favored Conv; masked-6D training failed. PCA served as an identity reference only and was not used as a longitudinal outcome.

### Explicit features (interpretation)

Descriptive features exceeding their own Drep included participation entropy / effective dimensionality / active-region counts (especially 651 and 790) and symmetry / regional coupling themes (especially 252). Amplitude-residual variants were available for selected features. These scalars do not provide link-level anatomical localization equivalent to JcvPCA.

### RQA (temporal characterization)

Stage 2 closed at `LIMITED_PASS_STOP`. Surrogate, truncation, and sensitivity checks were acceptable, but amplitude-independent novelty was insufficient for promotion. Two amp-preserving complementary cells were retained as limited temporal context: **651–ex13–D12** and **790–ex11–D12**. RQA was not treated as a primary longitudinal measure.

---

## 5. Existing regional coupling results

Coupling metrics were taken from already-computed explicit features (`regional_coupling`: mean signed zero-lag correlation of regional angular-speed time series; `trunk_arm_lagged_coupling`: max absolute correlation between trunk and arms over ±5 frames ≈ ±42 ms at 120 Hz). Values were aggregated as window means at participant × timepoint × repetition × exercise resolution for ex09–ex13 (complete 120-cell grid). No new joint-angle cross-correlation was computed. These metrics are **not** Chang-style anatomical in-phase/anti-phase joint coupling.

Using matched R1/R2 contrasts and requiring same-sign longitudinal change larger than T1 Drep on both repetitions (with a descriptive Drep-stability floor), selected D12 cells showed coupling change beyond within-session repetition variability. **Both increases and decreases** were observed.

Key empirical observations:

1. **651 – ex13 – trunk_arm_lagged_coupling:** robust **increase** (Δ_mean ≈ +0.13 > Drep), same sign on R1 and R2.  
2. **671:** **mixed** exercise-specific pattern — ex12 trunk–arm coupling **increase** (Δ_mean ≈ +0.20); ex10 regional_coupling **decrease**; ex09 coupling **stable** despite strong pooled JcvPCA A2.  
3. **790 – ex11:** coupling changes were **inconsistent across repetitions** and were not interpreted as robust; a robust regional_coupling **decrease** was observed at ex13.  
4. **252:** selected mixed increases and decreases passed the robust criterion at D12 (e.g., regional decreases at ex10/ex13; trunk–arm increase at ex10), alongside modest JcvPCA A2 and Conv D12 ≤ Drep.

Many other exercise cells were R1/R2 direction-inconsistent and were not interpreted.

---

## 6. Overall empirical synthesis

Longitudinal changes were **participant-specific** and appeared across multiple but **non-equivalent** movement representations. The strongest and most anatomically interpretable evidence came from JcvPCA A2 at D12. Existing regional coupling, Conv embeddings, explicit features, and limited RQA complementarity provided selected supporting or clarifying evidence without measuring the same construct. Coupling changes were mixed in direction and exercise-specific. No shared cohort direction, uniform coupling decrease/increase, or confirmed A3 claim is reported here.
