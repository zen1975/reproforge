# Study: arXiv 2610.06354 — GraphDecide

**Paper:** GraphDecide: Benchmarking System One Models on Graph Tasks  
**Intake:** VERIFIED against authoritative arXiv metadata and full PDF  
**Reproduction:** PARTIAL — mechanism only

## Why this paper

GraphDecide is useful to ReproForge because its central contract is model-independent. A graph task supplies input plus a candidate set; a model adapter returns a candidate identity; the evaluator owns ground truth, objective calculation and state transitions.

That separation matches the broader goal of keeping state, evidence, constraints and graph structure outside the model while treating the model as a replaceable decision layer.

## Independently reconstructed mechanism

The lightweight reproduction covers three invariants:

1. **candidate identity is preserved** — the decision layer cannot silently change the answer space;
2. **reference truth remains evaluator-owned** — graph algorithms compute RQ1 truth and the adapter never receives it;
3. **sequential histories are model-induced** — each RQ3 action updates evaluator-owned state, so later legal candidates follow the model's own prior decisions.

The synthetic mechanism fixture exercises all six RQ1 graph-cognition operations named by the paper:

- adjacency,
- exact degree,
- cycle existence,
- connectivity,
- distance threshold,
- articulation point.

It also runs a small TSP-style sequential construction to verify complete/legal trajectories, invalid-action failure, completion coverage and gap computation only for completed trajectories.

## Current boundary

This is **not** a benchmark reproduction. It does not reproduce the public RQ1 datasets, RQ2 ogbn-arxiv/STaRK-Prime conditions, any of the fourteen model-interface configurations, or the paper's RQ3 public optimization instances.

RQ2 matched graph-text contrasts remain protocol work.

The author repository is referenced only as provenance. Its code/assets are not copied because repository licensing is currently undeclared.

## Next stages

1. Freeze the synthetic mechanism fixture as observed evidence.
2. Reconstruct RQ2 T/G/TG/BAG/A(A*) paired-condition schema without using held-out labels.
3. Add a provider-neutral adapter contract for generation/scoring/native-selection readouts.
4. Build a legal independent RQ2 fixture and paired bootstrap evaluator.
5. Reconstruct at least one public-data RQ1 or RQ3 slice.
6. Promote to `PROTOCOL_VERIFIED` only after the benchmark evaluation shape is executable end to end.
