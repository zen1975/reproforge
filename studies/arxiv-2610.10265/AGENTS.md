# Agent Guide — arXiv:2610.10265

## State
- Lifecycle: `MECHANISM_VERIFIED`
- Reproduction: `PARTIAL`
- Free/light phase: incomplete
- Frozen: `memory-validity-mechanism-v1`

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

## Local/heavy next step

After the frozen 0.5B response-propagation analogue, use public/protocol-comparable corpora for key assignment and identity evaluation.

## Real implementation direction

Do not expose "memory accuracy" as one scalar.

Keep separate observable states:

```text
stored-state validity
identity resolution
answerability / abstention
retrieval result
deadline
generated response
```

Deletion is also separate from supersession/history retention.
