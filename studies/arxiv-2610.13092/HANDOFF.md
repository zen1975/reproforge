# arXiv:2610.13092 — Continuation Handoff

## State
- Lifecycle: `MECHANISM_VERIFIED`
- Reproduction: `PARTIAL`
- Free/light phase: incomplete

## Completed
- full arXiv HTML protocol and appendix review;
- paper license verified as CC BY-NC-ND 4.0;
- anonymous experimental-code provenance recorded;
- code-license uncertainty recorded;
- B/C/J causal comparison contract frozen;
- successful-delivery accounting reconstructed independently;
- recovery/completion contract reconstructed independently;
- deterministic aggregate/mechanism audit added.

## Frozen evaluation
- `jev-efficiency-transfer-audit-v1`

## Next lightweight step

Run the deterministic audit in CI and freeze the artifact.

Then stop unless a genuinely new free/lightweight source becomes available.

Do not replace a Jev rerun with a generic small LLM and call it equivalent. The paper's core empirical claim concerns actual Jev integration.

## Local/heavy continuation

A protocol-relevant continuation requires:

1. Jev API/model access matching or documenting divergence from `jev-1.13.0`;
2. the paper's LLM decision/auxiliary model or a declared comparable substitute;
3. ALFWorld valid_unseen execution;
4. AndroidWorld fixed task instances/device environment;
5. B/J and, where applicable, C controls;
6. repeated runs on fixed tasks;
7. task-cluster paired uncertainty;
8. full cost/time accounting including failures;
9. completion and recovery traces.

The primary acceptance metric is not local decision speed. It is resources per delivered successful outcome while preserving task success.
