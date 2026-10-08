# Agent Guide — arXiv:2610.03315

## State
- Lifecycle: `HEAVY_COMPUTE_READY`
- Reproduction: `PARTIAL`
- Free/light phase: complete
- Capability: `agent.trajectory-budget-serializer`

Read `status.yaml` and `HANDOFF.md` first.

## Verified boundary

Free/light verification now includes deterministic budget allocation, MMR-shaped evidence selection, one-call judge payload/report contracts, Detection Rate, and Align.|Det.@1/@3 semantics.

Frozen:
- `serializer-late-failure-stress-v1`
- `litetraj-protocol-synthetic-v1`

The Jaccard similarity used in the synthetic MMR fixture is an independently declared analogue, not an asserted unpublished paper constant.

## Local/heavy next step

Run one pinned judge model on a legally usable failed-trajectory slice before any broad sweep.

Record model/revision, dataset hash, full judge inputs/outputs, rubric, tokens, latency, cost, detection and localization metrics.

Do not retune against frozen synthetic results.

## Real implementation direction

Keep deterministic preprocessing and budget allocation separate from learned/LLM judging.

Production layering:

```text
trajectory
→ status/hints
→ evidence selection
→ deterministic budget allocation
→ serialized judge context
→ one judge call
→ evaluator
```

The deterministic serializer must remain usable without an LLM.
