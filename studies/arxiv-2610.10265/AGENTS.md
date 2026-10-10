# Agent Guide — arXiv:2610.10265

## State
- Lifecycle: `HEAVY_COMPUTE_READY`
- Reproduction: `PARTIAL`
- Free/light phase: complete
- Frozen: `memory-validity-mechanism-v1`, `memory-qwen0.5b-response-propagation-v1-negative`, `memory-qwen0.5b-key-assignment-v1-merge-collapse`

Read `status.yaml` and `HANDOFF.md` first.

## Verified boundary

Independent verification covers:

- keyed supersession;
- history retention;
- missed merge;
- false merge;
- stale exposure;
- wrong-person exposure;
- abstention;
- deadline-clean retrieval.

Real 0.5B boundaries:

- response-propagation fixture: current value selected in all 12 clean/stale/wrong-person runs;
- key-assignment fixture: MERGE selected in all 12 pairs, giving 100% true-revision recall and 100% false merges.

Do not tune frozen fixtures.

## Local/heavy next step

Use protocol-comparable/public corpora and larger pinned models for key/identity evaluation, response propagation, and serving latency.

## Real implementation direction

Do not expose "memory accuracy" as one scalar.

Keep separate observable states:

```text
stored-state validity
slot/key identity
entity identity
answerability / abstention
retrieval result
deadline
generated response
```

A system can have perfect merge recall while corrupting memory through false merges.
