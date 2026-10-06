# arXiv:2609.37590 — Continuation Handoff

## State

- Lifecycle: `HEAVY_COMPUTE_READY`
- Reproduction verdict: `PARTIAL`
- Free/lightweight phase: complete

ReproForge independently implements the deterministic FOCUS span-selection core and a provider-neutral Algorithm 1 harness. The published control-flow shape is executable and evidence-backed. Lightweight model analogues were also executed to test the draft-model boundary.

## Already executed

- authoritative arXiv intake and full-paper/appendix review;
- paper/license metadata capture;
- independent span-level utility selector;
- defensive rescue union;
- frozen synthetic mechanism/protocol benchmark: 4 / 4 cases PASS;
- provider-neutral Algorithm 1 control-flow harness;
- executed protocol verification: 7 / 7 checks PASS;
- published defaults captured: N=3, tau=0.3, draft temperature=0.7, main-agent temperature=0.0, seed=42;
- paper memory trigger values captured for AppWorld (4096) and OfficeBench / 8-Objective QA (2048);
- exact paper Peak Tokens, Dependency and cumulative-token metric formulas implemented;
- fail-closed parser for malformed/missing dependency citations;
- fail-closed validation against hallucinated/nonexistent span IDs;
- SmolLM2-135M analogue: 0 / 3 valid dependency rollouts;
- Qwen2.5-0.5B-Instruct analogue: 0 / 3 valid rollouts because every rollout cited nonexistent future span IDs.

## Important negative evidence

The lightweight draft-model tests are useful failures.

### SmolLM2-135M

The model did not reliably produce the required dependency-citation format.

### Qwen2.5-0.5B-Instruct

The model partially followed the requested syntax but cited IDs that were not present in the historical trace, such as `s_7` through `s_11`.

ReproForge rejects these references before utility estimation.

This means the reusable capability must treat **referential integrity of draft dependencies as a hard contract**, not assume that structured-looking output is valid.

These failures must not be generalized to the paper's Qwen3-8B/14B, Phi-4, or GPT-4.1-family draft models.

## Not reproduced

The following remain outside the free/lightweight phase:

- paper-quality dependency rollouts from Qwen3-8B;
- paper-quality dependency rollouts from Qwen3-14B;
- Phi-4 draft behavior;
- GPT-4.1 / GPT-4.1-mini agent/draft behavior;
- AppWorld task-success experiments;
- OfficeBench task-success experiments;
- 8-Objective QA experiments;
- WebVoyager experiments;
- tau2-Bench experiments;
- the paper-reported peak-context reductions;
- the paper-reported dependency reductions;
- the paper-reported task-success improvements;
- full benchmark cost/latency comparisons.

Therefore `REPRODUCED` is not justified.

## Frozen evaluations — do not tune against

Do not tune prompts, thresholds, parsing rules, or model settings against:

- `focus-synthetic-protocol-v1`;
- `focus-provider-neutral-protocol-v1`;
- the preserved SmolLM2-135M negative analogue;
- `focus-qwen0.5b-draft-analogue-v1-negative`.

Create a new experiment version and a new unseen synthetic trace if prompt/model-path tuning is needed.

## Published protocol values currently captured

```text
rollouts N              3
utility threshold tau   0.3
draft temperature       0.7
main-agent temperature  0.0
seed                    42

AppWorld trigger         4096 tokens
OfficeBench trigger      2048 tokens
8-Objective QA trigger   2048 tokens
```

The source paper uses complete reasoning/action/observation spans as the compression unit.

## Recommended next local step

The next useful step is **not more tiny-model prompt tuning**.

Run the existing model-backed analogue with a paper-scale open draft model, starting with Qwen3-8B on suitable local GPU hardware:

```bash
python studies/arxiv-2609.37590/experiments/run_model_backed_analogue.py \
  --model-id Qwen/Qwen3-8B \
  --experiment-id focus-qwen3-8b-local-v1 \
  --rollouts 3 \
  --temperature 0.7 \
  --max-new-tokens 256
```

Pin and record the exact model revision/hash used. Do not infer an immutable revision from the paper if it is not published.

The immediate acceptance question is:

> Does a paper-scale draft model produce valid references only to historical span IDs while preserving required causal/negative state?

Only after this path succeeds should full benchmark integration be attempted.

## Full benchmark continuation

For a full reproduction attempt, integrate the provider-neutral FOCUS harness with one of the paper's agent environments.

For each agent step:

1. serialize the current reasoning/action/observation history into complete spans;
2. compute context tokens using the benchmark's declared trigger policy;
3. when over budget, request N=3 draft rollouts;
4. strictly validate cited historical span IDs;
5. compute citation-frequency utility;
6. apply tau=0.3;
7. union defensive rescued spans;
8. execute the main agent on the retained complete spans;
9. record per-step input/output token counts;
10. compute Peak Tokens, Dependency, cumulative tokens, steps, and task success.

Start with one benchmark/model pair before broad sweeps.

## Expected evidence for local continuation

Preserve:

- model ID;
- exact model revision/hash;
- model license/access source;
- GPU model/count and VRAM;
- Python / PyTorch / Transformers / CUDA versions;
- experiment seed;
- N / tau / temperature;
- memory trigger;
- exact prompt version/hash;
- raw rollout outputs;
- parser success/failure;
- unknown-reference failures;
- dependency sets;
- rescue sets;
- retained/dropped span IDs;
- task result;
- input/output token counts per step;
- Peak Tokens;
- Dependency;
- cumulative tokens;
- artifact/checkpoint hashes where applicable;
- explicit comparison boundary against paper results.

Do not commit restricted model weights, private benchmark data, or secrets.

## ReproForge verification entrypoints

```text
studies/arxiv-2609.37590/experiments/run_focus_synthetic.py
studies/arxiv-2609.37590/experiments/run_provider_neutral_protocol.py
studies/arxiv-2609.37590/experiments/run_model_backed_analogue.py

capabilities/agent.decision-preserving-context-compressor/compressor.py
capabilities/agent.decision-preserving-context-compressor/parser.py
capabilities/agent.decision-preserving-context-compressor/harness.py
capabilities/agent.decision-preserving-context-compressor/metrics.py
```

## Promotion

Do not move this study to `REPRODUCED` because the deterministic core or protocol-shape tests pass.

Promotion requires sufficiently equivalent model-generated dependencies and benchmark execution against the declared paper-level claims.

Until that exists, keep:

```text
lifecycle: HEAVY_COMPUTE_READY
reproduction_status: PARTIAL
```
