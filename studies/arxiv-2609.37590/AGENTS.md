# Agent Guide — arXiv:2609.37590

## State
- Lifecycle: `HEAVY_COMPUTE_READY`
- Reproduction: `PARTIAL`
- Free/light phase: complete
- Capability: `agent.decision-preserving-context-compressor`

## Already verified
Independent core, provider-neutral Algorithm-1-style harness, paper metrics, strict/fail-closed dependency parsing, and two lightweight model-backed boundary tests are already executed.

The Qwen0.5B/SmolLM draft analogues are negative/boundary evidence. Do not tune them into positive results.

## Local/heavy next step
Run Qwen3-8B first through the existing model-backed analogue.

Before scaling:
- pin model revision;
- verify historical-span references remain resolvable after compression;
- log retained/dropped span IDs;
- preserve rollout dependency graphs;
- test rescue behavior separately from normal utility selection.

Then integrate one full benchmark before attempting all paper benchmarks.

Full paper-scale targets include AppWorld, OfficeBench, 8-Objective QA, WebVoyager and tau2.

## Real implementation direction
This capability is useful as an agent-memory/context layer only if future decision dependencies remain auditable.

Keep deterministic compression core, dependency estimator, optional rescue/risk layer, and provider adapters separate.

Never silently drop a span that is still referenced by a retained historical dependency.
