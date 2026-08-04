# Proposed Stage 0b plan (not approved for implementation)

Written because Stage 0 decision was **LIMITED GO**. Do **not** implement without a
separate explicit decision.

## Goals

1. Characterise within-participant structure of Conv (or PCA) embeddings on
   structured exercises.
2. Test whether free-movement sessions show related organisation.
3. Keep reliability gating and repetition references mandatory.

## Candidate analyses (priority order)

1. **Within-participant clustering** of window embeddings (T1-fit / T2–T3 apply),
   with exercise labels as external validation — not discovery of intervention effect.
2. **Motif discovery** on structured exercises (discrete states from clusters).
3. **Transition entropy** on motif sequences; compare T1 vs T2/T3 within participant.
4. **Free-movement transfer**: embed free sessions with frozen Conv; compare to
   structured latent neighbourhoods.
5. Only if transfer fails: limited joint training protocol (pre-registered).

## Hard constraints

* No new claim of shared cross-participant direction without redesign of the
  S8 gate and larger N.
* No Transformer scaling unless it beats Conv on held-out T1 skill with the
  same protocol.
* Do not treat Stage 0b as confirmatory for the intervention.

## Stop criteria

If clustering/motifs are not stable across seeds or are fully explained by
amplitude/exercise identity, stop and retain LIMITED GO instrument only.

---

## Update after LIMITED GO review

Shared-direction search remains closed. Before clustering/motifs/free-movement, Stage **0B-A (individual movement-change profiles)** was executed — see `STAGE0B_A_READINESS_RECOMMENDATION.md`. Next step is gated there.
