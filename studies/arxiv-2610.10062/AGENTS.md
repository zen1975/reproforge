# Agent Guide — arXiv:2610.10062

## State
- Lifecycle: `HEAVY_COMPUTE_READY`
- Reproduction: `PARTIAL`
- Free/light phase: complete
- Frozen: `official-master-trials-headline-audit-v1`, `tool-fault-mechanism-synthetic-v1`, `tool-fault-qwen0.5b-analogue-v1-negative`

Read `status.yaml` and `HANDOFF.md` first.

## Verified boundary

The paper protocol, licensing, released-data aggregation, typed-fault semantics, and a real 0.5B model-backed analogue have been executed.

The 0.5B analogue is negative evidence:

- 18 / 18 valid decisions;
- clean / loud / quiet all collapsed to `VERIFY`;
- loud-vs-quiet discrimination: 0 pp.

Do not prompt-tune this fixture after observing the result.

## Local/heavy next step

Independently generate paper-relevant multi-turn trajectories with legal BFCL-compatible data/environment and larger/comparable model execution.

Released author trajectories are audit evidence only.

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

Keep baseline false alarms explicit. A valid interface or an always-VERIFY policy does not demonstrate fault discrimination.
