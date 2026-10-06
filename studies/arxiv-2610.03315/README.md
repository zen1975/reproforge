# Study: arXiv 2610.03315

**Paper:** Lightweight, Rubric-Guided Trajectory Evaluation for Production AI Agents  
**Intake:** VERIFIED against authoritative arXiv metadata and full PDF  
**Paper license:** CC BY 4.0  
**Reproduction:** NOT_RUN

## Why this paper

This study targets a reusable production problem: evaluating long AI-agent execution trajectories without repeatedly paying the cost and latency of multi-call LLM diagnosis.

The paper's architecture separates:

1. offline domain-specific rule generation,
2. online deterministic trajectory normalization and failure hints,
3. fixed-budget evidence-aware serialization,
4. one rubric-guided LLM judge call.

That decomposition is useful beyond the paper's benchmark and maps cleanly to reusable system capabilities.

## ReproForge extraction

The first promoted candidate from this paper is intentionally narrower than the full evaluator:

`agent.trajectory-budget-serializer`

It captures the deterministic tier-based budget allocation kernel described in the paper. The complete LiteTrajEval reproduction remains `NOT_RUN`; no claim is made that the current kernel reproduces the reported benchmark results.

## Verified paper details used for planning

- Magentic-One-style evaluation: 44 failed samples / 78 normalized failure groups.
- tau-retail evaluation: 29 failed samples / 31 normalized failure groups.
- Fixed trajectory budget reported for LiteTrajEval evaluation: 50,000 characters.
- Baseline: AgentRx in a cost-minimized multi-call configuration.
- Metrics: Detection Rate and group-level alignment conditional on detected samples at tolerance 1 and 3.
- The paper reports roughly 20–35 percentage-point alignment gains on Magentic-One, up to 23 points on tau-retail, about 6x lower cost under the same judge model, and more than 8x lower full evaluation time.

## Current boundary

ReproForge does not redistribute the PDF, paper figures, datasets, prompts, model outputs, or author implementation. Dataset licensing is tracked separately and remains unresolved at intake.

## Next reproduction stages

1. Reconstruct normalized trajectory schema and rule profile format.
2. Reproduce deterministic preprocessing and hint generation.
3. Reproduce cross-step de-duplication and evidence selection.
4. Connect one configurable rubric-guided judge adapter.
5. Reconstruct the reported failed-trajectory evaluation sets or a protocol-equivalent set.
6. Reproduce Detection Rate, Align.|Det.@1/@3, token, cost, and runtime measurements.
7. Promote broader trajectory-evaluation capabilities only if evidence supports them.
