# Agent Guide — arXiv:2609.38143

## State
- Lifecycle: `MECHANISM_VERIFIED`
- Reproduction: `PARTIAL`
- Free/light phase: incomplete
- Frozen: `meta-skill-bank-mechanism-v1`

Read `status.yaml` and `HANDOFF.md` first.

## Verified boundary

```text
Target execution evidence
→ Builder reflection
→ at most one KEEP / ADD / REVISE
→ external evidence/schema validator
→ meta-skill bank
→ freeze
→ full-bank or fixed top-k selection
→ fresh test-task harness construction
```

The model must not directly own bank integrity.

## Local/heavy next step
After a frozen small-model update analogue, paper-level evaluation requires Builder/Target harness execution on held-out tasks.

## Real implementation direction
Meta-skills are support-design rules, not direct answers. Preserve Target responsibility in the `use` field and keep dev evidence separate from held-out evaluation.
