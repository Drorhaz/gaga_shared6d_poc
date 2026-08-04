# Guided Analysis — Thesis Discussion Points

Each bullet distinguishes **result** / **interpretation** / **speculation**.
Claim classes: *directly observed*, *derived metric*, *descriptive interpretation*, *future hypothesis*.

---

## Thesis-ready result statements (primary)

1. **Reliability-qualified Conv change vs Drep**  
   *Measured:* recording-level Conv embedding change magnitude for T1→T2/T1→T3, ratio to within-session Drep.  
   *Reliable units:* gated participant×fold×seed cells (skill>0 at endpoints).  
   *Finding:* many gated cells, especially for 651 and 790 (and 252 on T1→T3), exceed Drep.  
   *Amplitude:* not flagged as amplitude-dominated in Stage 0B-A profiles; feature residuals often co-support.  
   *Limits:* not all cells pass; R1/R2 is within-session only; session–timepoint confounding.  
   *Class:* directly observed (latent magnitude); comparison is a derived metric.

2. **Explicit coordination features**  
   *Measured:* entropy, effective dimensionality, symmetry, coupling, regional shares vs R1/R2, plus amp residuals.  
   *Reliable comparisons:* primarily 651/790 both deltas; 252 mainly T1→T3; 671 limited.  
   *Finding:* selected features exceed repetition references and sometimes survive amplitude residualization.  
   *Limits:* descriptive at N=4; multiple features; not a single biomechanical mechanism proof.  
   *Class:* derived metrics + descriptive interpretation.

3. **Exercise localization**  
   *Measured:* exercise-level Conv change/Drep on ex09–ex13.  
   *Finding:* participant-specific exercise emphasis; no shared exercise pattern.  
   *Class:* directly observed localization; absence of shared pattern is a negative result.

4. **No shared direction**  
   *Measured:* pairwise cosines of reliability-qualified change vectors (raw/std), jackknife, sign-flip.  
   *Finding:* `shared_direction_evidence=False`; instability across folds/seeds/scaling.  
   *Class:* directly observed negative result.

---

## Discussion arguments

### Individual motor adaptation (evidence)
- **Result:** gated within-participant latent and feature changes often > R1/R2.  
- **Interpretation:** compatible with individual coordination adaptation over T1→T2/T3.  
- **Speculation (avoid as fact):** that Gaga *caused* the change, or that changes are clinically beneficial.

### Absence of shared direction
- **Result:** S8 failed pre-registered stability criteria.  
- **Interpretation:** heterogeneous individual trajectories in representation space.  
- **Speculation:** a larger N or different tasks might reveal subtypes — future hypothesis only.

### Why heterogeneous adaptation is plausible in guided improvisation
- **Interpretation:** open-ended cueing invites multiple solutions; annotations do not impose P1–P5 stages.  
- Not a confirmed psychological mechanism — framing aid only.

### Why explicit features are required
- **Result:** Conv detects change; identity/region occlusion alone are insufficient for biomechanics.  
- **Interpretation:** thesis claims about coordination should cite entropy/dimensionality/symmetry/coupling (+ residuals).

### Conv role
- **Result:** positive pretext skill; gated change/Drep useful at recording/exercise levels; lower identity loading than PCA in controls.  
- **Interpretation:** Conv = reliability-gated detector/localizer.  
- **Not:** standalone biomechanical explanation.

### Why PCA was not primary
- **Result:** stronger identity dominance / weaker motion-change instrument role in Stage 0 controls.  
- **Interpretation:** keep as compression/identity reference.

### Why Transformer complexity was not justified
- **Result:** matched runs did not outperform Conv on selected velocity objective.  
- **Interpretation:** added capacity not warranted for this N and task.

### Clustering / motifs
- **Result:** `clustering_justified=False`; unstable across seeds; neighborhoods exercise-dominated.  
- **Interpretation:** no confirmatory repertoire taxonomy on guided data.

### R1/R2 reference
- **Result:** within-session repetition variability.  
- **Interpretation:** lower-bound / proximal reference for “larger than immediate repeatability.”  
- **Not:** full test–retest noise floor across days/marker reapplication (`DATA_VALIDATION_REPORT` caution).

### Confounding and N=4
- **Result:** timepoint inseparable from session/day; N=4.  
- **Interpretation:** prevents causal and population claims.  
- **Future hypothesis:** structured-versus-free transfer with frozen encoder.

---

## Unsupported framings (do not use)
- “Gaga produced a consistent coordination strategy across participants.”
- “Transformer is the primary model.”
- “Stable shared latent direction of learning.”
- “Motifs / P1–P5 stages explain the longitudinal effect.”
- “R1/R2 is a complete noise floor.”
