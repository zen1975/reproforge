# arXiv:2610.03315 — Continuation Handoff

## State

- Lifecycle: `MECHANISM_VERIFIED`
- Reproduction verdict: `PARTIAL`
- Free/lightweight phase: not complete

## Already executed

The deterministic fixed-budget serializer kernel has been implemented and stress-tested against naive head truncation. Evidence is stored under the study's `evidence/` directory.

## Next free/lightweight work

Before declaring `HEAVY_COMPUTE_READY`:

1. implement independent MMR/evidence selection equivalent to the paper description;
2. build or identify a legal evaluation set for failure-localization/judge-input testing;
3. implement the single-judge-call input/output contract;
4. measure localization/alignment-style metrics where the paper specifies them;
5. separate mechanism evidence from any paper-reported cost/runtime values;
6. save reproducible Evidence and keep CI green.

## Frozen evaluation

Do not tune the serializer against `serializer-late-failure-stress-v1` after observing its results. Create a new stress version for further tuning.

## Promotion

Move to `PROTOCOL_VERIFIED` when the paper's end-to-end evaluation shape is implemented and executable with independent legal data. Move to `HEAVY_COMPUTE_READY` only if the remaining primary work is genuinely large-scale/gated compute.
