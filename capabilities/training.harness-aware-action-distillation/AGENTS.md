# Capability Agent Guide — Harness-Aware Action Distillation

- Status: experimental
- Source study: `studies/arxiv-2610.02858`
- Heavy training instructions live in the study `AGENTS.md` and `HANDOFF.md`.

## Contract
Keep the capability provider-neutral. The core constructs/validates preferences and computes the published training primitives without knowing about a specific benchmark or API.

## Lightweight checks
Always retain deterministic tests for admissibility, held-object/state constraints, no-effect filtering, inactive contrasts, masked preference loss, and zero preference-gradient → lambda=0.

## Heavy/local work
Do not place benchmark-scale training orchestration here. Run it in the supporting study and link Evidence back into `capability.yaml`.

## Real implementation
Prefer:
```text
external state/evidence harness
→ validator
→ preference records
→ trainer
→ small-model operator
```

Adapters/providers must not change validity semantics.
