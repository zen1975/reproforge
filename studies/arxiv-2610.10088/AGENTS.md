# Agent Guide — arXiv:2610.10088

## State
- Lifecycle: `MECHANISM_VERIFIED`
- Reproduction: `PARTIAL`
- Free/light phase: incomplete
- Frozen: `skillsandbox-verifier-mechanism-v1`

Read `status.yaml` and `HANDOFF.md` first.

## Verified boundary

ReproForge independently implements:

- skill-relevant + novel scenario validity;
- executability gating;
- discounted with-skill vs without-skill utility;
- Keep iff score > 0.

No author implementation code is copied.

## Local/heavy next step

After a frozen small-model paired analogue, move to legal benchmark-scale trajectories only if the lightweight boundary is closed.

## Real implementation direction

Keep the architecture separated:

```text
Skill
→ structured applicability condition
→ scenario constructor
→ paired execution (+skill / -skill)
→ deterministic verifier
→ KEEP / REJECT
```

Do not allow the model to own success truth or rewrite verifier criteria after seeing outcomes.
