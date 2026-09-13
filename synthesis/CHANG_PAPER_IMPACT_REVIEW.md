# Paper impact review — Chang / Newell & Vaillancourt / Verrel

**Date:** 2026-08-07  
**Baseline:** approved JcvPCA-centered synthesis roadmap (`XCORR_OPTIONAL_BACKUP_ONLY`; A3 not formally supported; D12 primary)  
**Role of papers:** methodological / interpretive reference only  
**Source of truth:** validated project reports, tables, CSVs, and code — not Bernstein narratives

This review asks whether any paper finding **materially improves, corrects, or challenges** the current roadmap. Similarity of methods (cross-correlation, PCA, Bernstein language) is **not** by itself a reason to update.

Papers read:

1. Chang et al. (2020), *Whole-body kinematics and coordination in a complex dance sequence: Differences across skill levels* (`Human Movement Science` 69:102564)  
2. Newell & Vaillancourt (2001), *Dimensional change in motor learning* (`Human Movement Science` 20:695–715)  
3. Verrel et al. (2013), *Coordination of degrees of freedom and stabilization of task variables in a complex motor skill: expertise-related differences in cello bowing* (`Experimental Brain Research` 224:323–334)

---

## 1. Paper findings relevant to our study

### Chang et al. (2020)

- **Design:** cross-sectional skill groups (beginner / intermediate / expert), fixed cyclical Cha-Cha “Alternate Basic,” whole-body 36 Cardan joint angles (x–y–z), 100 Hz.
- **Coupling measure:** normalised **signed zero-lag** cross-correlation of joint-angle time series; values +1 (in-phase) to −1 (anti-phase); computed **within anatomical planes**; intra-limb pairs only (torso neck–trunk; shoulder–elbow–wrist; hip–knee–ankle; adjacent and non-adjacent).
- **Amplitude / speed:** most joints increased amplitude and angular speed with skill; interpreted as kinematic DOF unfreezing; **no decreases** observed; ankle amplitudes largely task-constrained.
- **Local coupling:** only 11/27 couplings differed by skill; when they changed, usually **early reductions** in coupling strength (or phase flips such as shoulder–elbow anti-phase → in-phase). Lower-limb flexion couplings remained strong.
- **Whole-body PCA:** fewer PCs needed for >90% variance with skill; PC1 explained more variance in experts → “more organised” coordinative structure.
- **Key interpretive point:** local intra-limb coupling can **weaken** while PCA organisation **increases**. Authors note no conflict because PCA includes **inter-limb** relations; greater whole-body organisation can arise via inter-limb dependency even if some intra-limb couplings loosen.
- **Bernstein / universality:** authors cite Newell & Vaillancourt (2001) that freezing→unfreezing is frequent but **not universal**; task constraints can reverse or freeze selected DOF.
- **Limitation (authors):** cross-sectional design cannot support causal skill-development claims; they explicitly call for **longitudinal** verification.

### Newell & Vaillancourt (2001) — theoretical safeguard

- Bernstein’s stage account of DOF change is **too narrow**.
- Organisation of mechanical DOF **and** attractor dimension of motor output can **increase or decrease**, depending on the confluence of constraints.
- Directional change in dimension depends on whether the task-relevant intrinsic dynamic must become higher- or lower-dimensional to meet new demands.
- Pathways of change are **not limited** to: (a) Bernstein’s increase in biomechanical DOF, or (b) Mitra-style universal reduction of dynamical dimension.
- **Implication for us:** reduced dimensionality ≠ better learning by default; increased dimensionality ≠ DOF unfreezing by default; JcvPCA redistribution ≠ proof of freeing DOF; stronger whole-body organisation ≠ stronger local joint coupling.

### Verrel et al. (2013) — construct distinction

- Separates **task-variable stabilisation** (bow angle, string touch, velocity/duration variability) from **execution-level DOF use/coordination** (joint amplitudes; PCA loadings / variance explained among arm joints).
- Experts: better task-variable control **and** more coordinated use of distal DOF; novices less distal integration.
- Warns that “freezing” lacks precise operationalisation if defined only as amplitude.
- Explicitly recommends both amplitude **and** coordination (cross-correlation / PCA) for characterisation; notes Konczak violin “freezing” conclusion may reflect incomplete control of task parameters.
- Limitations: cross-sectional expert–novice; calls for longitudinal work; no full forward model linking joints to task variables in their setup.

---

## 2. Direct similarities

| Aspect | Comparable? | Note |
|---|---|---|
| Whole-body coordination interest | Yes | Chang and our JcvPCA both target whole-body structure, not a single task limb |
| Local vs global organisation can diverge | Yes | Chang: weaker local coupling + stronger PCA organisation; our roadmap already treats this as a concordance question |
| PCA / variance-structure language | Partial | Chang uses joint-angle covariance PCA; we use reference-anchored JcvPCA on relative link rotvecs — related construct family, not the same estimand |
| Intra-limb pair set | Conceptual only | Chang’s torso/arm/leg pairs match the *proposed* minimal xcorr set in the roadmap |
| Bernstein as background frame | Surface only | Both can *mention* freezing/unfreezing; neither paper makes our claims true |
| Dance / aesthetic movement context | Weak | Chang = prescribed Latin basic; ours = guided improvisation exercises |

---

## 3. Important differences

| Dimension | Chang / Verrel / Newell | Our project |
|---|---|---|
| Design | Cross-sectional skill groups (Chang, Verrel) | Longitudinal repeated measures (T1/T2/T3) with within-session R1/R2 |
| Task | Fixed cyclical Cha-Cha (Chang); constrained cello bowing (Verrel) | Guided improvisation windows ex09–ex13 |
| Signal | Anatomical Cardan joint angles (Chang, Verrel) | Parent-relative rotvec / link contribution (JcvPCA); regional speed magnitudes (explicit coupling) |
| Coupling already computed | Signed zero-lag joint-angle r0 (Chang) | Regional speed coupling + max\|corr\| trunk–arm lag ±5 frames — **not** Chang-equivalent |
| Inference unit | Group-level skill contrasts | N=4 participant-specific case studies |
| Task-variable layer | Verrel measures bow stabilisation explicitly | No Verrel-style end-effector / task-variable stabilisation analysis in current freeze |
| Dimensional change theory | Newell: direction contingent on constraints | Our entropy / effective-dimensionality features are descriptive only; must not inherit a universal direction |

Our longitudinal R1/R2 floor is a **design advantage** over Chang and Verrel; it does not license importing their skill-group conclusions.

---

## 4. Recommendations that transfer

Only the following are scientifically justified for *our* synthesis writing:

1. **Preserve local ≠ global.** Chang’s finding that local coupling can loosen while whole-body structure organises supports keeping a categorical concordance map if xcorr is ever run — and supports **not** equating JcvPCA redistribution with stronger pairwise coupling.
2. **Do not treat dimensional / entropy direction as universal learning progress.** Newell requires task- and participant-specific interpretation of ↑/↓ dimensionality or participation entropy.
3. **Do not equate JcvPCA redistribution with DOF unfreezing.** Redistribution is reweighting within the T1 subspace (project CLAIMS); unfreezing is a stronger Bernstein claim.
4. **Distinguish construct layers (Verrel).** Keep separate:
   - whole-body organisation / link redistribution (JcvPCA);
   - local joint/regional coupling (explicit features; possible future xcorr);
   - biomechanical descriptors (energy, symmetry, entropy);
   - task-variable stabilisation (**not currently measured** → claim N/A).
5. **Keep amplitude control / mechanism language cautious.** Chang interprets amplitude↑ as unfreezing in a prescribed skill progression; our Step-5 organisation vs amplitude labels are descriptive and must not be rewritten as skill-stage unfreezing.
6. **Retain longitudinal R1/R2 + Fisher-z logic if xcorr is ever approved.** Chang used group Kruskal–Wallis on raw *r*; our repeated-measures design justifies Fisher-z + Drep — a refinement *we* already planned, not something Chang requires.

---

## 5. Recommendations that should NOT transfer

Do **not** copy into the current project:

1. Cross-sectional beginner→expert group narrative as if it were our longitudinal result.
2. Prescribed Cha-Cha / cello skill-stage staging (early unfreeze / late refine) as a forced timeline for Gaga participants.
3. Anatomical Cardan plane-wise in-phase / anti-phase claims from parent-relative rotvecs or speed magnitudes.
4. Treating reduced number of PCs / higher PC1 variance as proof of “better” learning in our data (Chang’s group PCA is not our JcvPCA estimand; Newell blocks universal dimensional progress).
5. Treating increased joint amplitude/speed as required evidence of adaptation in improvisation (task constraints differ; our Step-5 already separates amplitude vs organisation).
6. Adding Verrel-style task-variable analyses solely to reproduce cello bowing methods.
7. Promoting DOF unfreezing, global flexibility, or motor learning to SUPPORTED because Chang/Verrel used Bernstein language.
8. Upgrading xcorr solely because Chang used cross-correlation.
9. Expanding to a full pairwise matrix or inter-limb coupling battery because Chang mentioned inter-limb dependency in PCA discussion.

---

## 6. Impact on current roadmap

| Roadmap component | Impact | Rationale |
|---|---|---|
| JcvPCA interpretation | `MINOR CLARIFICATION` | Keep “link-contribution redistribution / reweighting in T1 subspace”; explicitly avoid equating redistribution with DOF unfreezing or with stronger local coupling (Chang local↓/global↑; Newell non-universal direction). |
| A1 / A2 / A3 hierarchy | `NO CHANGE` | Hierarchy is project-internal evidence logic; papers do not alter S2/S3/A3 gates or the 51-organisation ≠ A3 resolution. |
| R1 / R2 framework | `NO CHANGE` | Papers lack matched within-session repetition floors; our Fisher-z / Drep / same-direction proposal remains appropriate and is an advantage, not a defect. |
| Cross-correlation status | `NO CHANGE` — keep `XCORR_OPTIONAL_BACKUP_ONLY` | Chang shows local coupling *can* clarify local-vs-global stories, but does **not** create a necessary unresolved question we can answer safely: we lack trustworthy anatomical Cardan signals; existing regional speed coupling cannot carry in-phase/anti-phase meaning; thesis conclusions do not require new xcorr. Upgrade to MINIMAL would require a safe Chang-equivalent signal — not available without new anatomical calibration. Downgrade to NOT_JUSTIFIED would overstate: optional backup remains scientifically coherent *if* a later approved signal pass is carefully limited. |
| Signal representation | `NO CHANGE` (reinforced) | Chang’s interpretation depends on anatomical Cardan components within planes. Parent-relative rotvec components and speed magnitudes are **not** equivalent. Candidate 1 remains rejected; Candidate 2 cannot inherit Chang phase language. |
| Participant matrix | `MINOR CLARIFICATION` | Add categorical column/note: task-variable stabilisation = N/A; local coupling vs whole-body redistribution kept separate; no forced shared Bernstein stage across 252/651/671/790. |
| Claim ladder | `MINOR CLARIFICATION` | Add Newell safeguard: dimensional/entropy direction is constraint-dependent. Keep motor adaptation / DOF unfreezing / amplitude-independent reorganisation out of SUPPORTED unless project evidence hierarchy already allows (A3 still not formally supported). |
| Presentation figures | `NO CHANGE` | Do not add a Chang-style coupling or skill-group figure. Keep: (1) method + R1/R2; (2) four-participant JcvPCA D12; (3) robustness / cross-method synthesis. |

---

## 7. Final decision

### `ROADMAP_MINOR_UPDATE`

**Why not `ROADMAP_UNCHANGED`:**  
Newell and Verrel identify real interpretive failure modes that the baseline plan only partially named: (i) assuming a universal direction of dimensional/DOF change; (ii) collapsing task-variable control, local coupling, and whole-body organisation into one “coordination improved” claim. Those clarifications should be written into the claim-ladder / construct-map sections of the roadmap before the ten synthesis reports are drafted.

**Why not `ROADMAP_MATERIAL_UPDATE_REQUIRED`:**  
No core decision reverses:

- JcvPCA remains the narrative center.
- A3 / S3 / organisation hierarchy stands.
- D12 primary / D13 supplemental stands.
- `XCORR_OPTIONAL_BACKUP_ONLY` stands.
- Anatomical Cardan imitation remains unjustified.
- Main figures remain JcvPCA-centered without a required xcorr panel.

### Surgical roadmap updates applied

1. **Claim ladder / construct map wording:** add Newell bidirectional dimensional-change safeguard; add Verrel three-layer distinction; mark task-variable stabilisation as not measured.
2. **JcvPCA interpretation note:** redistribution ≠ unfreezing; redistribution ≠ stronger local coupling.
3. **XCORR status:** unchanged classification; rationale reinforced (Chang supports *optional interpretive complementarity*, not mandatory compute given signal limits).

### Explicit non-actions

- No new cross-correlation computation  
- No JcvPCA recompute  
- No Conv/Transformer retrain  
- No RQA reopen  
- No Verrel-style task-variable pipeline  
- No rewrite of validated project conclusions to fit Bernstein  

---

## Appendix A — Cross-correlation classification argument (detail)

**Question:** Does Chang create an important *unresolved* scientific question that new xcorr would answer in *our* dataset?

| Argument for upgrade to MINIMAL | Counter-argument |
|---|---|
| Local vs global divergence is scientifically interesting | Already acknowledged; can be discussed conceptually using existing JcvPCA + regional features without Chang-equivalent r0 |
| Intra-limb pairs are well-defined | Signal for signed anatomical phase is missing; CLAIMS forbid anatomical joint-angle statements from current features |
| Would map to JcvPCA links | Concordance map is optional backup; not required for thesis conclusions |

**Verdict:** keep `XCORR_OPTIONAL_BACKUP_ONLY`.

---

## Appendix B — Claim-ladder check against papers

| Claim class | Example claims | Paper effect |
|---|---|---|
| SUPPORTED | Participant-specific longitudinal kinematic change; link-specific redistribution exceeding R1/R2 where A2 holds | Reinforced as the correct ceiling for hard claims; papers do not add group skill effects |
| CONSISTENT WITH, BUT NOT PROVEN | Longitudinal motor adaptation; coordination reorganisation; selected local independence with whole-body organisation | Allowed only as cautious interpretation; Chang’s local↓/global↑ is analogy, not evidence; Newell forbids assuming one dimensional direction |
| NOT SUPPORTED | Group-level learning; causal Gaga/psilocybin; global DOF unfreezing; amplitude-independent whole-body reorganisation as A3; “better learning” from ↑/↓ dimensionality alone | Explicitly reinforced by Chang’s cross-sectional caveat + Newell’s non-universality + our pending A3 supervisor gate |
