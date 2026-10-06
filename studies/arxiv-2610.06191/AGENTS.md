# Agent Guide — arXiv:2610.06191

## State
- Lifecycle: `HEAVY_COMPUTE_READY`
- Reproduction: `PARTIAL`
- Free/light phase: complete
- Capability: `agent.evidence-aware-stopping-gate`

## Already verified
Completed lightweight work includes the deterministic stopping mechanism, time-matched Δ protocol, mean6 calculation, answer-after-five summaries, and audits of released author episodes.

These audits do not equal independent regeneration of the original trajectories.

## Local/heavy next step
Regenerate trajectories independently.

Preferred first run:
- Qwen3-8B;
- test300;
- unaided condition;
- enforced-rule condition;
- pinned author harness where legally/technically available.

Then compare mean6, Δ, confidence intervals, answer-after-five, tool-call counts, and failure modes.

Do not infer immutable model revisions that the authors did not publish. Optional API replication is separate and may incur cost.

## Real implementation direction
Keep the stopping gate deterministic and independent of the model providing the USEFUL/USELESS judgment.

Production architecture:
```text
evidence/tool result
→ usefulness judge
→ deterministic consecutive-useless state
→ force-answer gate
```

The gate must expose its state and reason for stopping.
