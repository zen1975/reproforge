# Agent Guide — arXiv:2610.10507

## State
- Lifecycle: `MECHANISM_VERIFIED`
- Reproduction: `PARTIAL`
- Free/light phase: incomplete
- Frozen: `recast-routing-mechanism-v1`

Read `status.yaml` and `HANDOFF.md` first.

## Verified boundary

Target architecture:

```text
Task + source profile + evidence + history
→ Router action
   ├─ CALL_PRIMITIVE
   ├─ SYNTHESIZE
   └─ ACCEPT_CONTEXT
→ external executor / validator
→ evidence + provenance + feedback
→ next round
→ frozen AnswerLM only after ACCEPT
```

RouterLM does not own source truth, operation execution truth or final sufficiency truth in ReproForge evaluation.

## Local/heavy next step

After mechanism execution and frozen small-model router analogue, training-scale SFT/GRPO requires heavy compute.

## Real implementation direction

Never equate "tool executed successfully" with "evidence sufficient." Preserve operation provenance and block ACCEPT until the task-specific evidence contract is satisfied.
