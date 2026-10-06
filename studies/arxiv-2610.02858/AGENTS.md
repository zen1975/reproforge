# Agent Guide — arXiv:2610.02858

## State
- Lifecycle: `HEAVY_COMPUTE_READY`
- Reproduction: `PARTIAL`
- Free/light phase: complete
- Capability: `training.harness-aware-action-distillation`

Read `status.yaml` and `HANDOFF.md` before running anything.

## Already verified
Do not repeat these merely to get a different number:
- HAD mechanism and validity masking;
- action-only preference loss;
- beta=0.5 and rho=0.5 gradient balancing;
- real Qwen2.5-0.5B LoRA path;
- student-visited-state collection;
- same Qwen2.5-1.5B teacher with/without-harness contrast;
- active-pair filtering;
- 3-seed distill-only vs HAD comparison on frozen unseen synthetic states.

The current lightweight evidence is directional, not a performance claim.

## Local/heavy next step
Move to a true interactive on-policy loop:

```text
student visits state
→ freeze student reasoning prefix
→ same teacher WITH harness
→ same teacher WITHOUT harness
→ validate preferred action
→ response-distillation + masked preference update
→ continue rollout
```

Recommended first local track:
- student: open model in the paper-relevant ~0.6B–1.7B class;
- teacher: meaningfully larger open model;
- one interactive benchmark/environment first;
- substantially more than the 8-step smoke;
- multiple seeds;
- task success + harness-utilization metrics, not margin alone.

Record GPU/VRAM, model revisions, trajectory hashes, beta/rho, gradient norms, lambda, seeds and exact prompts/config.

## Real implementation direction
Treat the small model as an operator and keep state/constraints/evidence in an external harness.

Separate:
- state/memory/evidence provider;
- harness validator;
- paired-teacher data generator;
- training primitive;
- runtime policy.

## Frozen / no-tune
Do not tune against any entry under `frozen_evaluations` in `status.yaml`. Create a new unseen state set/version for every new training decision.

## Promotion
Do not mark `REPRODUCED` until paper-scale or sufficiently equivalent on-policy benchmark evidence exists.
