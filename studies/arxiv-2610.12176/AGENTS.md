# Agent Guide — arXiv:2610.12176

## State

- Lifecycle: `HEAVY_COMPUTE_READY`
- Reproduction: `PARTIAL`
- Free/light phase: complete
- Frozen: `mass-rsi-loop-mechanism-v1`, `mass-qwen0.5b-workflow-eval-analogue-v1`, `mass-qwen0.5b-one-cycle-lora-v1-null-transfer`

Read `status.yaml` and `HANDOFF.md` first.

## Verified boundary

MASS is treated as a gated recursive state machine:

`workflow proposal -> execution -> self-evaluation -> elite retention -> trajectory generation -> self-ranking -> task-solving training -> successor model -> successor becomes executor/evaluator/optimizer`

External evaluation stays outside the inner improvement loop.

The 0.5B evidence is negative/partial:

- evaluator syntax valid but accuracy only 50%;
- standalone workflow structural validity 25%;
- tiny task-solving-only LoRA produced evaluator 50% -> 50% and within-run optimizer validity 0% -> 0%.

Do not retune frozen fixtures to manufacture cross-role transfer.

## License boundary

The paper is CC BY 4.0.

The official `SakanaAI/mass` repository is inspectable for provenance, but its NOTICE says MASS-specific code has no public open-source license. Do not copy or redistribute it.

## Local/heavy next step

Run at least one protocol-comparable successor-model generation with real trajectories and held-out executor/evaluator/optimizer tests. Prefer a second generation if resources permit, because one-shot post-training is not enough to establish recursion.

## Real implementation direction

Model proposals and self-judgments are evidence inputs, not authoritative state transitions.

Externally own and log:

- task split;
- workflow incumbent mutation;
- trajectory ranking manifest;
- train/validation membership;
- checkpoint selection;
- model-generation promotion;
- external evaluation;
- evidence lineage.

A successor model is not accepted as recursively improved until held-out role-specific evidence supports the transition.

## Scientific stop rule

Do not call a result recursive self-improvement unless an independently updated model improves a later improvement role under held-out evidence. Better task solving alone, interface validity, or one-generation prompt search is insufficient.
