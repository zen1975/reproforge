# arXiv:2610.12176 — Continuation Handoff

## State

- Lifecycle: `HEAVY_COMPUTE_READY`
- Reproduction: `PARTIAL`
- Free/light phase: complete

## Completed

- full public paper protocol review;
- CC BY 4.0 paper license verification;
- official `SakanaAI/mass` provenance review and revision pin;
- official code-license restriction recorded;
- paper-vs-public-repository protocol differences recorded;
- independent RSI-loop mechanism verification;
- real Qwen2.5-0.5B optimizer/self-evaluator analogue;
- tiny task-solving-only one-cycle LoRA transfer analogue.

## Frozen evidence

- `mass-rsi-loop-mechanism-v1`
- `mass-qwen0.5b-workflow-eval-analogue-v1`
- `mass-qwen0.5b-one-cycle-lora-v1-null-transfer`

Do not tune these fixtures after observing their results.

## Real-model boundary

Standalone 0.5B analogue:

- evaluator output validity: 100%
- evaluator accuracy: 50%
- workflow structural validity: 25%

One-cycle within-run transfer:

- evaluator: 50% -> 50%
- optimizer valid workflow: 0% -> 0%

No cross-role improvement was observed.

The standalone 25% optimizer baseline and the one-cycle run's 0% pre-training baseline come from separate executions and must not be treated as the same baseline.

## Local/heavy continuation

The next meaningful experiment requires an actual successor model generation under a more protocol-comparable setup.

Minimum continuation contract:

1. use a substantially larger pinned open model;
2. execute real task-solving trajectories rather than four authored responses;
3. generate/rank training trajectories with train/test isolation;
4. train a successor model;
5. evaluate executor, evaluator, and optimizer roles separately on held-out cases;
6. preserve an independent external evaluator;
7. record the exact model revision, dataset/trajectory lineage, training manifest, checkpoint, seeds, and environment;
8. if feasible, repeat for a second generation to test recursion rather than one-shot transfer.

A positive task-solving delta alone is not enough for an RSI claim.

The key test is:

`task-solving supervision -> model update -> held-out optimizer/evaluator improvement -> better next-cycle self-supervision`
