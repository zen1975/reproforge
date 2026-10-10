# arXiv:2610.10507 — Verification Report

## Current verdict

**PARTIAL / HEAVY_COMPUTE_READY**

The current free/lightweight boundary is complete.

RECAST treats context construction as a sequential evidence-building process in which a Router chooses one of three actions per round:

- `CALL_PRIMITIVE`;
- `SYNTHESIZE`;
- `ACCEPT_CONTEXT`.

ReproForge independently verified the state/provenance/action semantics and then tested a real pinned 0.5B model behind the frozen routing contract.

## Independent mechanism verification

Experiment: `recast-routing-mechanism-v1`

Workflow: `38046764417`

Artifact: `11668100624`

Digest:

`sha256:3bf32aa4e4e6d8b52db2e49fb6e2d237c526a285421cfd28dd9712c11e313eec`

Result: **PASS**

Verified:

- structured CALL_PRIMITIVE / SYNTHESIZE / ACCEPT_CONTEXT validation;
- evidence source provenance;
- failure outcomes enter history but do not silently add evidence;
- evidence deduplication;
- raw operands are insufficient when the task requires a derived computation;
- ACCEPT becomes legal only after required derived evidence exists;
- incomplete synthesis constraints fail closed;
- malformed/unknown actions fail closed;
- missing provenance fails closed.

## Real 0.5B Router boundary

Experiment: `recast-qwen0.5b-router-analogue-v1`

Model:

`Qwen/Qwen2.5-0.5B-Instruct`

Resolved revision:

`7ae557604adf67be50417f59c2c2f167def9a775`

Frozen cases:

1. exact identifier → lexical primitive;
2. conceptual/paraphrase evidence → semantic primitive;
3. structured filtering/grouping → relational primitive;
4. derived sliding-window computation → SYNTHESIZE;
5. already-complete derived evidence → ACCEPT_CONTEXT;
6. raw operands only → must not ACCEPT;
7. failed lexical lookup with evidence still absent → continue evidence construction;
8. irregular nested-log computation → SYNTHESIZE.

Results:

- structured contract validity: **7/8 = 87.5%**
- action accuracy: **1/8 = 12.5%**
- primitive subtype accuracy: **0%**
- premature-accept rate on the explicit computed-evidence guard: **100%**
- parseable cases selecting `ACCEPT_CONTEXT`: **7/7**
- one SYNTHESIZE-expected case produced truncated invalid JSON.

Workflow: `38046855731`

Artifact: `11668455566`

Digest:

`sha256:cd81ba35b33ed569c82387d8b7086b0c0ffd2b9cdee01a9ae237bcbb657c87c8`

### Important negative result

Several incorrect outputs explicitly said in the `reason` field that evidence was missing or that computation was still required, yet still selected `ACCEPT_CONTEXT`.

So the frozen boundary is:

`correct diagnostic language != correct routing policy`

and:

`valid structured action != evidence sufficiency awareness`

The only correct routing case was the one where final derived evidence was already present.

This fixture is retained as negative evidence and must not be prompt-tuned after observing the result.

## Paper-scale claims not reproduced

The paper trains a Qwen3.5-9B RouterLM using SFT followed by GRPO and evaluates with frozen CompilerLM/AnswerLM across heterogeneous benchmarks.

Those training/benchmark claims are not reproduced here.

## Current-environment closure

Further prompt variations on the frozen 0.5B fixture would not constitute stronger reproduction evidence.

Remaining meaningful work requires:

- larger/trained RouterLM;
- SFT/GRPO;
- CompilerLM;
- AnswerLM;
- real primitive backends;
- benchmark environments;
- paper-scale end-to-end evaluation.

Therefore:

- `HEAVY_COMPUTE_READY`
- `free_light_phase_complete: true`
- `reproduction_status: PARTIAL`

## What must not be claimed

Do not claim:

- full RECAST reproduction;
- reproduction of paper benchmark success;
- reproduction of SFT/GRPO gains;
- that small models generally cannot route evidence;
- CompilerLM or AnswerLM quality.

The 0.5B result is a frozen negative boundary result.
