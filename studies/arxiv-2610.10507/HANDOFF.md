# arXiv:2610.10507 — Continuation Handoff

## State

- Lifecycle: `HEAVY_COMPUTE_READY`
- Reproduction: `PARTIAL`
- Free/light phase: complete

## Completed

- full paper/prompt review;
- CC BY 4.0 license verification;
- action/state/provenance mechanism reconstruction;
- frozen deterministic mechanism workflow;
- real pinned Qwen2.5-0.5B Router analogue.

## Frozen evidence

- `recast-routing-mechanism-v1`
  - workflow `38046764417`
  - artifact `11668100624`
  - digest `sha256:3bf32aa4e4e6d8b52db2e49fb6e2d237c526a285421cfd28dd9712c11e313eec`

- `recast-qwen0.5b-router-analogue-v1-accept-collapse`
  - workflow `38046855731`
  - artifact `11668455566`
  - digest `sha256:cd81ba35b33ed569c82387d8b7086b0c0ffd2b9cdee01a9ae237bcbb657c87c8`

Do not retune either fixture.

## Boundary result

0.5B Router:

- valid contract: 87.5%;
- action accuracy: 12.5%;
- primitive accuracy: 0%;
- premature accept: 100% on the explicit guard case;
- all parseable outputs selected ACCEPT_CONTEXT.

Notably, some outputs correctly described the lack of evidence in prose but still chose ACCEPT_CONTEXT.

Treat routing action as the audited object, not the natural-language rationale.

## Local/heavy continuation

Next paper-relevant work requires:

1. larger/trained RouterLM;
2. SFT and GRPO recipe;
3. actual lexical/semantic/relational backends;
4. frozen CompilerLM and AnswerLM;
5. benchmark tasks/source profiles;
6. raw routing traces;
7. separate action, primitive, synthesis, premature-accept, compiler, and final-answer error accounting.

Keep evidence truth and sufficiency validation external when evaluating the Router.
