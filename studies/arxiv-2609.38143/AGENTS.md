# Agent Guide — arXiv:2609.38143

## State
- Lifecycle: `HEAVY_COMPUTE_READY`
- Reproduction: `PARTIAL`
- Free/light phase: complete
- Frozen: `meta-skill-bank-mechanism-v1`, `meta-skill-qwen0.5b-update-analogue-v1-negative`

Read `status.yaml` and `HANDOFF.md` first.

## Verified boundary

```text
Target execution evidence
→ Builder reflection / model proposal
→ external evidence + schema validator
→ at most one KEEP / ADD / REVISE
→ meta-skill bank
→ freeze
→ full-bank or fixed top-k selection
→ fresh test-task harness construction
```

The 0.5B model-backed update analogue is negative boundary evidence: proposal formatting and mutation choice are not reliable enough to own the bank.

## Local/heavy next step

Paper-level evaluation requires Builder/Target harness execution on held-out tasks with the bank frozen.

## Real implementation direction

Keep model reflection separate from authoritative state mutation. Meta-skills are support-design rules, not direct answers, and the Target retains final judgment.
