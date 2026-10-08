# arXiv:2610.03315 — Continuation Handoff

## State

- Lifecycle: `HEAVY_COMPUTE_READY`
- Reproduction verdict: `PARTIAL`
- Free/lightweight phase: complete
- Frozen evaluations: `serializer-late-failure-stress-v1`, `litetraj-protocol-synthetic-v1`

## Completed lightweight verification

ReproForge now independently executes the paper's lightweight evaluation shape:

1. deterministic tier-aware budget allocation;
2. MMR-shaped intra-step evidence selection with injected similarity;
3. single-call judge input contract with trajectory + weak candidate regions;
4. structured judge-report validation;
5. Detection Rate;
6. group-level `Align.|Det.@1` and `Align.|Det.@3`;
7. failure/negative boundary tests;
8. CI on Python 3.11 and 3.12.

The synthetic fixture uses Jaccard similarity as an explicit independent analogue. The paper specifies the MMR equation but does not fully specify the similarity backend, so ReproForge does not claim this as an exact hidden implementation detail.

## Not reproduced

- public Magentic-One-style and tau-retail benchmark results;
- actual rubric-guided judge quality;
- paper-level localization gains;
- paper-level token/cost/runtime comparisons;
- exact offline rule-generation LLM behavior.

## Next local/heavy work

Use a legally obtained failed-trajectory slice and one pinned judge model first.

Preserve:
- dataset/split identity and hash;
- exact judge model/revision/provider;
- complete serialized judge input;
- complete raw and parsed judge output;
- rubric version;
- token usage;
- latency;
- cost;
- Detection Rate;
- Align.|Det.@1/@3;
- parse/validation failures.

Do not tune against either frozen synthetic fixture.

## Real implementation direction

Keep the production stack layered:

```text
trajectory
→ deterministic normalization/status hints
→ evidence selection
→ deterministic budget allocation
→ one structured judge call
→ evaluator
```

The serializer remains usable without an LLM. Judge disagreement must not be conflated with serializer failure.

## Promotion

Do not promote to `REPRODUCED` until a legal benchmark-equivalent trajectory set has been independently evaluated with a pinned judge and the declared paper-level claims are tested.
