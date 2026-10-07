# Agent Guide — arXiv:2610.06354

## State
- Lifecycle: `MECHANISM_VERIFIED`
- Reproduction: `PARTIAL`
- Free/light phase: NOT complete
- Working label: `GraphDecide`
- Frozen synthetic evaluation: `graphdecide-mechanism-v1`

Read `status.yaml` and `HANDOFF.md` first.

## Verified boundary

The model-independent decision mechanism is now independently verified on a frozen synthetic fixture.

Verified:
- candidate identities remain evaluator-owned;
- reference truth is independent of model output;
- adjacency, degree, cycle, connectivity, distance-threshold and articulation are separate RQ1 contracts;
- invalid output is rejected;
- unsupported output is reported separately;
- sequential legal candidates evolve from prior model decisions;
- failed trajectories receive no fabricated objective/gap and remain in coverage.

This is mechanism evidence only. It is not GraphDecide benchmark performance reproduction.

The author repository currently has no declared repository license. Do not copy, vendor, redistribute, or treat author code/assets as reusable implementation material unless that licensing state changes and is verified.

## Lightweight next step

Stay in the CPU/lightweight lane.

1. reconstruct RQ2 T / G / TG / BAG / A(A*) condition schemas from primary sources;
2. encode paired contrasts, especially TG-BAG and G-C0;
3. implement adapter-neutral native-selection / constrained-generation / candidate-scoring boundaries;
4. build a new legal synthetic fixture for paired condition evaluation;
5. verify held-out-label isolation and candidate-set identity;
6. add paired confidence-interval logic without tuning to observed frozen results.

Do not modify `graphdecide-mechanism-v1` to improve results. Create a new version.

Do not invent unpublished graph construction rules, coefficients, prompts, model revisions, seeds, evaluator settings, or dataset transformations.

## Local/heavy guidance

No heavy model sweep is justified yet.

Move toward local/GPU work only after:
- RQ2 protocol is executable;
- adapter behavior is frozen;
- a legal evaluation slice is identified;
- lightweight leakage/boundary tests pass;
- status reaches at least `PROTOCOL_VERIFIED`.

When heavy work starts, record model revision, interface/readout mode, inference settings, dataset/split identity, hardware and complete terminal outcomes.

## Real implementation direction

Keep graph state, relation provenance, evidence, legal candidates, constraints, objective evaluation and state transitions outside the learned model.

Treat native selectors, small LLMs, classifiers, GNNs or scoring models as replaceable decision layers behind the same contract.

For graph-memory/GNN applications, experience or relational representations may inform candidate scoring, but they must not silently own evaluator truth or mutate the legal action space.

## Frozen / no-tune

`graphdecide-mechanism-v1` is frozen after observation.

Any changed graph, action pool, transition rule or expected output used for development requires a new benchmark id.

## Promotion

Promote to `PROTOCOL_VERIFIED` only after the matched-condition and adapter/evaluator protocol is executable end to end. Promote to `HEAVY_COMPUTE_READY` only when the remaining unresolved work is genuinely compute/model/data gated.
