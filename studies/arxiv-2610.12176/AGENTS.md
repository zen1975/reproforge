# Agent Guide — arXiv:2610.12176

State:
- Lifecycle: MECHANISM_VERIFIED
- Reproduction: PARTIAL
- Free/light phase: incomplete
- Frozen: mass-rsi-loop-mechanism-v1

Verified boundary:
workflow proposal -> execution -> self-evaluation -> elite retention -> trajectory generation -> self-ranking -> SFT -> new model generation -> same new model becomes executor/evaluator/optimizer.

External evaluation is not part of the inner improvement loop.

License boundary:
The paper is CC BY 4.0. The official SakanaAI/mass repository is inspectable, but its NOTICE says MASS-specific code has no public open-source license. Do not copy or redistribute it.

Next lightweight step:
Use a pinned small open model only for proposal/self-evaluation analogues. External code owns structural validity, state transitions, and held-out truth.

Scientific stop rule:
Do not call a result recursive self-improvement unless an independently updated model improves a later improvement role under held-out evidence. Interface validity or one-generation prompt search is insufficient.

## Local/heavy next step

Paper-level work requires at least one real next-generation model update followed by held-out tests of executor, optimizer, and evaluator improvement. The lightweight analogue must not be promoted into an RSI claim without that weight-update boundary.

## Real implementation direction

Treat MASS as a gated state machine: model proposals and self-judgments are evidence inputs, while generation transitions, split isolation, checkpoint selection, external evaluation, and promotion to a new model generation remain externally auditable state changes. A successor model is not accepted as recursively improved until held-out role-specific evidence supports the transition.
