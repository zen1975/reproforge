# Agent Guide — arXiv:2610.10062

## State
- Lifecycle: `PROTOCOL_VERIFIED`
- Reproduction: `PARTIAL`
- Free/light phase: incomplete
- Frozen: `official-master-trials-headline-audit-v1`, `tool-fault-mechanism-synthetic-v1`

Read `status.yaml` and `HANDOFF.md` first.

## Verified boundary

The paper protocol, author-code/data licensing, released-data headline aggregation, and independent typed-fault semantics have been verified.

The released 1,920-trial table is audit evidence only. It does not independently reproduce model behavior.

## Local/heavy next step

After the frozen 0.5B analogue, paper-level work requires independently generated multi-turn trajectories with comparable fault conditions and model families.

Do not tune prompts or task fixtures against frozen results.

## Real implementation direction

Treat tool-fault detection as an external observability layer around agent execution:

```text
Agent action
→ Tool boundary
→ typed one-shot fault injection / observation
→ detection
→ replanning
→ recovery comparison
→ repetition audit
```

Keep detection, replanning, recovery, and repetition separate. A valid tool result or valid output format does not imply semantic correctness.
