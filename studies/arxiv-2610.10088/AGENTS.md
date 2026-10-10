# Agent Guide — arXiv:2610.10088

## State
- Lifecycle: `HEAVY_COMPUTE_READY`
- Reproduction: `PARTIAL`
- Free/light phase: complete
- Frozen: `skillsandbox-verifier-mechanism-v1`, `skillsandbox-qwen0.5b-paired-analogue-v1`, `skillsandbox-qwen0.5b-proposer-analogue-v1`

Read `status.yaml` and `HANDOFF.md` first.

## Verified boundary

Mechanism:
- scenario relevance + novelty;
- executability gating;
- paired external utility;
- KEEP iff score > 0.

Real 0.5B paired execution:
- helpful skill: score 1.0 / KEEP;
- harmful skill: score 0.0 / REJECT.

Real 0.5B Proposer:
- only 2/6 outputs fully satisfied frozen relevance + novelty + format checks.

Do not prompt-tune frozen fixtures.

## Local/heavy next step

Move to an executable Builder and paper-relevant ALFWorld/WebShop or protocol-comparable agent environment.

## Real implementation direction

Keep the boundary explicit:

```text
Skill
→ applicability condition
→ Proposer
→ deterministic validity checks
→ Builder / executable environment
→ paired +skill / -skill execution
→ external verifier
→ KEEP / REJECT
```

Novel output alone is not a valid verification scenario.
