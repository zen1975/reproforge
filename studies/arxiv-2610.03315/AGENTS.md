# Agent Guide — arXiv:2610.03315

## State
- Lifecycle: `MECHANISM_VERIFIED`
- Reproduction: `PARTIAL`
- Free/light phase: NOT complete
- Capability: `agent.trajectory-budget-serializer`

This study stays in the lightweight lane for now.

## Completed
The deterministic trajectory budget allocator is implemented and stress-tested.

## Lightweight next step
Before any heavy compute:
1. implement independent MMR-style evidence selection;
2. reconstruct the judge-input protocol;
3. add localization/alignment metrics;
4. run a legally usable benchmark or independent evaluation set;
5. measure serialized size, runtime and cost proxies;
6. preserve negative/boundary cases.

Do not advance to `HEAVY_COMPUTE_READY` while these CPU/lightweight tasks remain.

## Local/heavy guidance
Only introduce larger judge/model runs after selection and evaluator protocol are stable and frozen.

If a judge model is used:
- pin provider/model/revision;
- preserve full judge input;
- version the rubric;
- separate judge disagreement from serializer failure.

## Real implementation direction
Keep deterministic budget allocation separate from learned/LLM evidence selection.

Production layering:
```text
trajectory
→ candidate evidence selection
→ deterministic budget allocation
→ serialized judge context
→ evaluator
```

The serializer must remain usable without an LLM.
