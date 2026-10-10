# Agent Guide — arXiv:2610.10507

## State
- Lifecycle: `HEAVY_COMPUTE_READY`
- Reproduction: `PARTIAL`
- Free/light phase: complete
- Frozen: `recast-routing-mechanism-v1`, `recast-qwen0.5b-router-analogue-v1-accept-collapse`

Read `status.yaml` and `HANDOFF.md` first.

## Verified boundary

Deterministic mechanism PASS:

```text
Task/source/evidence/history
→ exactly one Router action
→ external executor
→ evidence + provenance + feedback
→ next round
→ AnswerLM only after valid ACCEPT
```

Real 0.5B boundary:

- 87.5% structured-contract validity;
- 12.5% action accuracy;
- 0% primitive subtype accuracy;
- premature ACCEPT on the computed-result guard;
- ACCEPT collapse on every parseable case.

Do not prompt-tune frozen fixtures.

## Local/heavy next step

Paper-relevant continuation requires trained/larger RouterLM, real primitives, CompilerLM, AnswerLM and benchmark-scale evaluation.

## Real implementation direction

Never let a fluent `reason` field override the audited action.

A router can verbally recognize missing evidence and still terminate incorrectly. Keep sufficiency and provenance validators outside the model.
