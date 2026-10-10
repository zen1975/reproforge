# arXiv:2609.38143 — Verification Report

## Current verdict

**PARTIAL / HEAVY_COMPUTE_READY**

The current free/lightweight boundary is complete.

## Deterministic bank mechanism

Experiment: `meta-skill-bank-mechanism-v1`

Verified:

- when / provide / use schema;
- evidence-grounded ADD;
- evidence-grounded REVISE;
- at most one mutation per batch;
- rejection of unknown evidence references;
- fixed top-k relevance selection;
- mutation rejection after freeze;
- frozen-bank read integrity.

Workflow: `38047109174`

Artifact: `11666859850`

Digest:

`sha256:ce802c6717bbd9395d4d28c26e53fcdb133f6fdfe93094b94464a7f696fd508e`

Result: **PASS**

## Real 0.5B update-proposal boundary

Experiment: `meta-skill-qwen0.5b-update-analogue-v1`

Model:

`Qwen/Qwen2.5-0.5B-Instruct`

Resolved revision:

`7ae557604adf67be50417f59c2c2f167def9a775`

Observed:

- cases: **5**
- schema-valid rate: **40%**
- decision accuracy: **40%**
- evidence grounding on expected mutations: **0%**
- skill-ID accuracy on expected mutations: **33.3%**

The model correctly emitted ADD on two ADD-labelled cases, but KEEP and REVISE cases largely collapsed toward ADD. Even valid proposals cited or described evidence incorrectly relative to the frozen evidence contract.

Workflow: `38047285509`

Artifact: `11667079783`

Digest:

`sha256:77d21ccacfd085ea101bc8686317165fbf221c216c318a24ae2b342f544e2f1f`

Interpretation:

**model proposal != admissible bank mutation**

The safe reusable architecture is:

```text
execution evidence
→ model reflection/proposal
→ external schema + evidence validator
→ at-most-one mutation gate
→ meta-skill bank
→ freeze
```

The frozen fixture must not be prompt-tuned to manufacture better mutation accuracy.

## Current-environment closure

Remaining meaningful work requires fresh task-specific harness construction and Target execution on held-out benchmark tasks under a frozen bank.

Therefore:

- `HEAVY_COMPUTE_READY`
- `free_light_phase_complete: true`
- `reproduction_status: PARTIAL`

## What must not be claimed

Do not claim:

- Harness-Bench/NewtonBench reproduction;
- the paper's reported benchmark gains;
- Builder-enactment superiority;
- that Qwen2.5-0.5B is representative of paper-scale Builder behavior.
