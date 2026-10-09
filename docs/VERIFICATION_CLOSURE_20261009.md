# ReproForge Verification Closure — 2026-10-09

This document records the point at which the current free/lightweight and CPU-accessible verification work is considered complete for the active studies.

It does **not** mean that every paper has been fully reproduced.

The distinction is:

- **CURRENT-ENVIRONMENT COMPLETE**: no additional free/lightweight or ordinary CPU experiment is required to establish the study's current boundary; the next meaningful step depends on external model access, GPU-class compute, legal public data, or paper-scale benchmark execution.
- **REPRODUCED**: paper-level claims have been independently tested under protocol-equivalent conditions. None of the active studies should be called reproduced unless its own status explicitly says so.

## Active study matrix

| Study | Lifecycle | Free/light | Current-environment closure | Remaining primary work |
|---|---|---:|---|---|
| arXiv:2609.37590 — FOCUS | HEAVY_COMPUTE_READY | complete | CURRENT-ENVIRONMENT COMPLETE | Qwen3-8B/14B or comparable paper-scale draft-model execution and full agent benchmarks |
| arXiv:2610.02858 — HAD | HEAVY_COMPUTE_READY | complete | CURRENT-ENVIRONMENT COMPLETE | true long-horizon on-policy benchmark training with larger student/teacher and substantially more updates |
| arXiv:2610.03213 — task-tool relevance | HEAVY_COMPUTE_READY | complete | CURRENT-ENVIRONMENT COMPLETE | authorized Gemma 3 access, GPU LoRA SFT, then paper-scale GRPO where justified |
| arXiv:2610.03315 — LiteTrajEval | HEAVY_COMPUTE_READY | complete | CURRENT-ENVIRONMENT COMPLETE | legal public failed-trajectory slice, paper-comparable pinned judge, cost/runtime comparison |
| arXiv:2610.06191 — evidence-aware stopping | HEAVY_COMPUTE_READY | complete | CURRENT-ENVIRONMENT COMPLETE | independent regeneration of 7B–32B model trajectories, beginning with Qwen3-8B test300 |
| arXiv:2610.06354 — GraphDecide | HEAVY_COMPUTE_READY | complete | CURRENT-ENVIRONMENT COMPLETE | legal public RQ1/RQ2 slice with paper-relevant model/readout configurations |

## New model-backed closure evidence added on 2026-10-09

### arXiv:2610.03315 — LiteTrajEval

A real small open model was run through the reconstructed one-call judge contract.

Model:

`Qwen/Qwen2.5-0.5B-Instruct`

Resolved model revision:

`7ae557604adf67be50417f59c2c2f167def9a775`

Environment:

- PyTorch `2.14.1+cpu`
- Transformers `4.57.6`
- GitHub Actions CPU runner

Experiment:

`litetraj-qwen0.5b-judge-analogue-v2`

Result:

- cases: 3 independent synthetic failed trajectories
- structured report contract valid: 3/3
- Detection Rate: 1.0
- Align.|Det.@1: 1.0
- Align.|Det.@3: 1.0

Workflow:

`37899828376`

Artifact:

`11602290522`

Artifact digest:

`sha256:28f7144782299e1c87c86d7a78efd0ed7ef1f9366c1809af3cefb92d5e95008b`

Interpretation:

This verifies that the reconstructed single-call contract is executable with a real 0.5B model and that the evaluator pipeline accepts and scores real model output. It does **not** establish paper-level judge quality. The fixture is deliberately tiny and the alignment metric can count a failure group as matched even when the model predicts extra steps.

Canonical evidence:

- `studies/arxiv-2610.03315/evidence/litetraj_qwen0.5b_judge_analogue_v2.result.json`
- `studies/arxiv-2610.03315/evidence/C1.qwen0.5b-judge-analogue-v2.evidence.json`

### arXiv:2610.06354 — GraphDecide

A real small open model was run behind the reconstructed matched-condition candidate contract.

Model:

`Qwen/Qwen2.5-0.5B-Instruct`

Resolved model revision:

`7ae557604adf67be50417f59c2c2f167def9a775`

Environment:

- PyTorch `2.14.1+cpu`
- Transformers `4.57.6`
- GitHub Actions CPU runner

Experiment:

`graphdecide-rq2-qwen0.5b-analogue-v2`

Result:

- matched items: 4
- conditions: T / G / TG / BAG / A
- valid candidate output rate: 1.0
- T accuracy: 0.5
- G accuracy: 0.5
- TG accuracy: 0.5
- BAG accuracy: 0.5
- A accuracy: 0.5
- TG-BAG: 0 percentage points
- G-A: 0 percentage points
- raw behavioral pattern: `c0` selected for all 20 decisions

Workflow:

`37899838200`

Artifact:

`11601674028`

Artifact digest:

`sha256:6a078c24e854bdaef3e25009cef282b0531e5e8fd439ee07dc5a569ca050bc8d`

Interpretation:

This is intentionally retained as **negative boundary evidence**.

The model successfully obeyed the candidate-output interface but showed no evidence of using graph information on this frozen analogue. Therefore:

`valid interface behavior != graph-evidence utilization`

Do not prompt-tune or modify the frozen fixture to manufacture a positive graph effect.

Canonical evidence:

- `studies/arxiv-2610.06354/evidence/graphdecide_rq2_qwen0.5b_analogue_v2.result.json`
- `studies/arxiv-2610.06354/evidence/C4.qwen0.5b-rq2-analogue-v2.evidence.json`

## Publication boundary for the currently unpublished studies

The following studies now have a stable result boundary suitable for a transparent research-progress post:

### arXiv:2610.03213

Postable boundary:

- free/lightweight protocol complete;
- specialized baselines and blind/frozen evaluations executed;
- real Qwen2.5-0.5B LoRA evidence exists;
- exact Gemma/GRPO paper-scale reproduction remains external-compute/gated.

Do not claim exact paper reproduction.

### arXiv:2610.03315

Postable boundary:

- deterministic protocol complete;
- real 0.5B model has exercised the one-call judge contract;
- tiny synthetic localization result is positive;
- public benchmark and cost/runtime claims remain unreproduced.

Do not present 1.0 synthetic alignment as benchmark quality.

### arXiv:2610.06191

Postable boundary:

- stopping rule, delta protocol, mean6 and answer-after-five audits are executable;
- official released evidence has been audited;
- independent model-trajectory regeneration remains unexecuted because the next meaningful step requires 7B–32B model compute.

Do not claim independent trajectory reproduction.

### arXiv:2610.06354

Postable boundary:

- mechanism and RQ2 matched-condition protocol complete;
- real 0.5B model-backed run executed;
- the 0.5B result is negative: valid outputs but no graph-use signal;
- public graph benchmark/model reproduction remains unexecuted.

The negative result should be preserved rather than hidden.

## Global rule

A study may be described as "verification complete to the current environment boundary" only when:

1. `free_light_phase_complete: true`;
2. lifecycle is `HEAVY_COMPUTE_READY` or later;
3. the handoff is ready;
4. frozen evaluations are listed;
5. negative evidence is retained;
6. the next step is genuinely gated by model/data/compute access rather than unfinished lightweight protocol work;
7. CI is green.

This closure document does not override any study-specific `status.yaml`, `HANDOFF.md`, or `AGENTS.md`.
