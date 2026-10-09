# arXiv:2610.03315 — Continuation Handoff

## State

- Lifecycle: `HEAVY_COMPUTE_READY`
- Reproduction verdict: `PARTIAL`
- Free/lightweight phase: complete
- Frozen evaluations: `serializer-late-failure-stress-v1`, `litetraj-protocol-synthetic-v1`, `litetraj-qwen0.5b-judge-analogue-v1`, `litetraj-qwen0.5b-judge-analogue-v2`

## Completed lightweight verification

ReproForge now independently executes the paper's lightweight evaluation shape:

1. deterministic tier-aware budget allocation;
2. MMR-shaped intra-step evidence selection with injected similarity;
3. single-call judge input contract with trajectory + weak candidate regions;
4. structured judge-report validation;
5. Detection Rate;
6. group-level `Align.|Det.@1` and `Align.|Det.@3`;
7. failure/negative boundary tests;
8. CI on Python 3.11 and 3.12.\n9. real Qwen2.5-0.5B-Instruct single-call judge execution with resolved model revision `7ae557604adf67be50417f59c2c2f167def9a775`;\n10. 3/3 model-backed synthetic reports satisfied the structured contract, with Detection Rate = 1.0 and Align.|Det.@1/@3 = 1.0 on this tiny fixture.

The synthetic fixture uses Jaccard similarity as an explicit independent analogue. The paper specifies the MMR equation but does not fully specify the similarity backend, so ReproForge does not claim this as an exact hidden implementation detail.

## Not reproduced

- public Magentic-One-style and tau-retail benchmark results;
- paper-comparable rubric-guided judge quality on the public evaluation distribution;
- paper-level localization gains;
- paper-level token/cost/runtime comparisons;
- exact offline rule-generation LLM behavior.

## Next local/heavy work

The next meaningful step is no longer another synthetic judge run. Use a legally obtained failed-trajectory slice and a paper-comparable pinned judge model.

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

Do not tune against any frozen synthetic/model-backed fixture. The perfect localization values on the three-case 0.5B fixture are not evidence of paper-level judge quality; the metric also tolerates extra predicted steps when a reference group is hit.

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
