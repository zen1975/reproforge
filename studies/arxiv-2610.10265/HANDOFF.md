# arXiv:2610.10265 — Continuation Handoff

## State

- Lifecycle: `HEAVY_COMPUTE_READY`
- Reproduction: `PARTIAL`
- Free/light phase: complete

## Completed

- public paper protocol review;
- keyed-supersession invariant implementation;
- missed-merge and false-merge mechanism tests;
- current/stale/wrong-person/abstention/deadline metric implementation;
- frozen Qwen2.5-0.5B response-propagation analogue;
- frozen Qwen2.5-0.5B key-assignment analogue.

## Frozen evidence

- `memory-validity-mechanism-v1`
- `memory-qwen0.5b-response-propagation-v1-negative`
- `memory-qwen0.5b-key-assignment-v1-merge-collapse`

Do not retune these fixtures.

## Boundary results

Response propagation:

- 12/12 outputs contained the current value;
- 0/12 emitted the injected stale value;
- 0/12 emitted the same-name wrong-person value.

Key assignment:

- 12/12 valid classifications;
- all 12 were `MERGE`;
- merge recall 100%;
- false-merge rate 100%;
- accuracy 50%.

The reusable lesson is that memory safety cannot be summarized by merge recall or final answer accuracy alone.

## Local/heavy continuation

Next paper-relevant work should preserve distinct measurements for:

```text
missed merge
false merge
stale exposure
wrong-person exposure
abstention
clean retrieval
deadline
response propagation
```

Use public/protocol-comparable corpora and larger pinned models. Keep response generation downstream of the memory-state audit rather than using it as the only evaluator.
