# arXiv:2610.07782 — Continuation Handoff

## State

- Lifecycle: `HEAVY_COMPUTE_READY`
- Reproduction: `PARTIAL`
- Free/light phase: complete

## Completed

- full 13-page PDF protocol review;
- CC BY 4.0 paper license verification;
- C1-C4 audit semantics independently implemented;
- structural independent-item vs shared-state applicability check implemented;
- frozen audit workflow executed and artifact retained;
- all intended positive/negative fixture checks passed.

## Frozen evidence

- `persistent-memory-ablation-audit-v1`
- workflow `38046596329`
- artifact `11668225187`
- digest `sha256:2338d3b42a145913416a0e5191de7c20799b69fe3c133727dc8b2fc195c9a31e`

Do not weaken C1-C4 to make a future benchmark appear positive.

## Local/heavy continuation

A paper-relevant reproduction needs:

1. live counters proving persistent write and recall execute;
2. pre-run contamination probes;
3. condition resets;
4. serialized arm diff restricted to the named memory axis;
5. counterbalanced execution order;
6. replicate-derived measurement floor;
7. paired per-question effect analysis;
8. cluster-aware aggregation where appropriate;
9. actual peak-KV accounting under known model geometry;
10. a regime where stored prior state can genuinely be useful.

Keep the decomposition working-set claim separate from persistent-memory efficacy.
