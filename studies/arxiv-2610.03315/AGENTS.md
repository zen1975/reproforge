# Agent Guide — arXiv:2610.03315

## State
- Lifecycle: `HEAVY_COMPUTE_READY`
- Reproduction: `PARTIAL`
- Free/light phase: complete
- Capability: `agent.trajectory-budget-serializer`

Read `status.yaml` and `HANDOFF.md` first.

## Verified boundary

Free/light verification includes deterministic budget allocation, MMR-shaped evidence selection, one-call judge payload/report contracts, Detection Rate, and Align.|Det.@1/@3 semantics.

A real model-backed boundary run has also been executed:

- model: `Qwen/Qwen2.5-0.5B-Instruct`
- resolved revision: `7ae557604adf67be50417f59c2c2f167def9a775`
- cases: 3 independent synthetic failed trajectories
- structured contract valid: 3/3
- Detection Rate: 1.0
- Align.|Det.@1: 1.0
- Align.|Det.@3: 1.0

These values are boundary evidence only. The fixture is tiny and the alignment metric can still score a reference group as matched when extra failure steps are predicted.

Frozen:
- `serializer-late-failure-stress-v1`
- `litetraj-protocol-synthetic-v1`
- `litetraj-qwen0.5b-judge-analogue-v1`
- `litetraj-qwen0.5b-judge-analogue-v2`

The Jaccard similarity used in the synthetic MMR fixture is an independently declared analogue, not an asserted unpublished paper constant.

## Local/heavy next step

Do not run another synthetic judge merely to improve the observed numbers.

Use a legally usable failed-trajectory slice with a paper-comparable pinned judge. Record model/revision, dataset hash, full judge inputs/outputs, rubric, tokens, latency, cost, detection and localization metrics.

Do not retune against any frozen fixture.

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
