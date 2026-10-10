# arXiv:2610.10088 — Continuation Handoff

## State

- Lifecycle: `MECHANISM_VERIFIED`
- Reproduction: `PARTIAL`
- Free/light phase: incomplete

## Completed

- arXiv identity and paper license reviewed;
- Proposer / Builder / Verifier roles extracted;
- scenario relevance/novelty contract reconstructed;
- executability-weighted discounted utility scoring reconstructed;
- Keep/Reject boundary reconstructed;
- independent synthetic mechanism test passed.

## Frozen evidence

- `skillsandbox-verifier-mechanism-v1`

Do not retune against this fixture.

## Next lightweight experiment

Run one pinned open small model on a tiny paired skill-use analogue.

Required separation:

```text
Scenario truth / success criterion
Scenario construction
Skill text
Model execution
Executability marker
Verifier score
```

Only the model execution is model-owned. Ground truth, matching, scoring, and verdict logic remain deterministic.

Preserve raw outputs for both with-skill and without-skill runs.

## Paper-level continuation

Paper-scale reproduction requires dynamic scenario construction and paired agent rollouts on ALFWorld/WebShop or a protocol-comparable environment, with evaluation of downstream skill-library effects.
