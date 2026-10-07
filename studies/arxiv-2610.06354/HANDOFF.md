# arXiv:2610.06354 — Continuation Handoff

## State

- Lifecycle: `MECHANISM_VERIFIED`
- Reproduction verdict: `PARTIAL`
- Free/lightweight phase: not complete
- Frozen synthetic evaluation: `graphdecide-mechanism-v1`

## Already executed

The model-independent GraphDecide mechanism has been independently reconstructed and verified on a frozen synthetic fixture.

Verified:

1. candidate identities and answer spaces are evaluator-owned;
2. reference answers are computed independently of the model adapter;
3. all six RQ1 structural operation contracts are represented separately;
4. invalid outputs are rejected rather than silently mapped;
5. unsupported responses remain distinct from invalid responses;
6. RQ3-style sequential state evolves from the model's own choices;
7. objective/gap are produced only for completed legal trajectories;
8. failed trajectories remain in completion coverage without artificial objective values.

CI run `37646670852` passed on Python 3.11 and 3.12.

## Frozen evaluation

Do not tune the mechanism against `graphdecide-mechanism-v1` after observing its results.

Any changed graph, candidate set, transition rule, or probe intended for development must use a new benchmark version.

## Next free/lightweight work

Before `PROTOCOL_VERIFIED`:

1. independently reconstruct RQ2 condition schemas for T / G / TG / BAG / A(A*);
2. encode the paired-contrast contract, including TG-BAG and G-C0;
3. implement a provider-neutral adapter boundary for native selection, constrained generation and candidate scoring;
4. add paired metric/bootstrap logic using independent legal synthetic data;
5. test held-out-label isolation and candidate-identity preservation;
6. reconstruct at least one public-data RQ1 or RQ3 slice if licensing permits.

## Local/heavy boundary

Do not start large model sweeps yet. Heavy/local execution is premature while RQ2 and adapter protocol work remains lightweight and unresolved.

## Real implementation direction

Keep graph state, relations, provenance, legal candidates, objectives and constraints outside the model. Treat the model as a replaceable decision layer only.

This is especially relevant to downstream graph-memory/GNN systems: learned graph representations may propose or score actions, but evaluator-owned state and evidence contracts should remain explicit and inspectable.

## Promotion rule

Move to `PROTOCOL_VERIFIED` only when the matched-condition and adapter/evaluator protocol is executable end to end without benchmark leakage. Move to `HEAVY_COMPUTE_READY` only when remaining work is genuinely model/data/compute gated.
