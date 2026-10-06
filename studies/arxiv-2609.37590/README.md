# Study: arXiv 2609.37590

**Paper:** FOCUS: Training-Free Decision-Preserving Context Compression for LLM Agents  
**arXiv:** https://arxiv.org/abs/2609.37590  
**Intake:** VERIFIED against arXiv v1 and full PDF  
**Lifecycle:** HEAVY_COMPUTE_READY  
**Reproduction:** PARTIAL

## Why this study

FOCUS treats agent context compression as future-decision preservation rather than generic summarization or redundancy removal. Historical interaction units remain intact as complete reasoning-action-observation spans.

The reusable capability hypothesis is:

`agent.decision-preserving-context-compressor`

## Published mechanism captured

Algorithm 1 has four operational stages:

1. trigger compression when context exceeds a memory budget;
2. sample multiple stochastic future plan sketches;
3. score each historical span by how often future plans cite it as a dependency;
4. retain spans above threshold and union spans rescued by defensive verification.

Published defaults captured in `experiments/paper_protocol_config_v1.json` include `N=3`, `tau=0.3`, draft temperature `0.7`, main-agent temperature `0.0`, and seed `42`.

## ReproForge implementation boundary

The first implementation is an independent deterministic core. It consumes already-generated dependency sets and rescue decisions.

It does **not** claim to reproduce:
- GPT-4.1 / GPT-4.1-mini rollouts;
- Qwen3-8B/14B or Phi-4 draft behavior;
- AppWorld, OfficeBench, 8-QA, WebVoyager, or tau2-Bench task success;
- paper token/cost reductions.

## Frozen synthetic evidence

`focus-synthetic-protocol-v1` verifies:
- N=3 citation-frequency selection;
- tau=0.3 threshold behavior;
- whole-span retention;
- defensive rescue;
- the known set-valued-goal failure mode.

The failure-mode case is intentionally negative evidence: generalized future plans may cite a procedure while failing to cite individual entity spans, causing those entity-specific facts to be pruned.

## Provider-neutral protocol verification

ReproForge now includes an executable Algorithm 1 control-flow harness. The draft-model transport remains injectable, while the published protocol shape is enforced around it.

Executed GitHub Actions evidence passed **7 / 7** checks:

- no compression below the memory threshold;
- compression above the threshold;
- exactly N=3 draft calls;
- draft temperature 0.7 forwarded;
- deterministic seed offsets from seed 42;
- citation-frequency selection at tau=0.3;
- defensive rescue union;
- irrelevant span pruning.

The OfficeBench-style 2048-token trigger was used in this frozen protocol test. This is protocol-shape evidence with scripted draft outputs, not paper benchmark reproduction.

## Model-backed negative evidence

A first real-model analogue used `HuggingFaceTB/SmolLM2-135M-Instruct` with three stochastic rollouts at temperature 0.7. The tiny model did not emit the required `Depends on: [...]` citation format in any rollout (0/3). Instead it continued a trajectory-like history.

This exposed an important runtime boundary: a dependency-frequency compressor is only as reliable as the draft model's structured dependency output. ReproForge therefore changed the parser to **fail closed** when no dependency citation lines are present rather than treating an empty dependency set as valid.

The failed tiny-model run is preserved as negative evidence and is not counted as protocol success.

## Qwen2.5-0.5B model-backed boundary

A second lightweight analogue used `Qwen/Qwen2.5-0.5B-Instruct` with the paper-shaped dual-objective draft prompt, N=3, and temperature 0.7.

The model partially followed the requested `Depends on: [...]` structure, but every rollout cited at least one nonexistent/future span ID such as `s_7` through `s_11`.

Result:

- valid referential rollouts: **0 / 3**
- unknown-reference rollouts: **3 / 3**
- strict parser behavior: **fail closed**

This is useful negative evidence: syntactically structured dependency output is not enough. FOCUS-style compression requires citations to be referentially valid against the actual historical trace.

This result does not imply that the paper's Qwen3-8B/14B, Phi-4, or GPT-4.1-family draft models fail.

## Next gate

The free/lightweight phase is complete. Continue with a paper-scale draft model, beginning with Qwen3-8B locally, and verify historical-span referential integrity before full benchmark integration. See `HANDOFF.md`.
