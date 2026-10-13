# arXiv:2610.13092 — Continuation Handoff

## State
- Lifecycle: `HEAVY_COMPUTE_READY`
- Reproduction: `PARTIAL`
- Free/light phase: complete

## Completed
- full arXiv protocol and appendices reviewed;
- paper license verified as CC BY-NC-ND 4.0;
- anonymous experimental-code provenance recorded;
- code-license uncertainty recorded;
- B/C/J causal-comparison contract frozen;
- published decision-level reduction ranges independently recomputed;
- resource-per-delivered-success arithmetic independently reconstructed;
- synthetic transfer/recovery semantics frozen;
- CI artifact persisted.

## Frozen evaluation
- `jev-efficiency-transfer-audit-v1`

Workflow run:

`38431488012`

Artifact:

`11831980273`

Digest:

`sha256:ce25ab6a5af50d10821a5e874b4bba34d7c0e38817cfdb02e1c2f7e1f37b5750`

## Verified lightweight boundary

Published aggregate audit:

- decision cost reduction range: **66.03–78.44%**
- decision time reduction range: **73.85–81.49%**
- rounded successful-delivery table reconstruction: **PASS**

Key transfer classifications:

- ReAct: cost/time **TRANSFERRED**
- Reflexion: cost/time **TRANSFERRED**
- T3A: cost/time **DELIVERY_PARADOX**
- AutoDroid: cost **TRANSFERRED**, time **DELIVERY_PARADOX**
- FastAgent: cost **TRANSFERRED**, time **OVERHEAD_ABSORPTION**

T3A is the clearest paradox:

- task cost per attempt: about **-17.1%**
- cost per delivered success: about **68.70 -> 73.96 mUSD**

FastAgent exposes time overhead:

- task time: roughly unchanged/slightly worse
- time per delivered success: about **239.4 -> 377.8 s**

## Local/heavy continuation

The next scientifically valid step is a real-system rerun.

Minimum contract:

1. Jev access matching `jev-1.13.0` or explicitly documented divergence;
2. GPT-5.6 Luna or a declared substitute for decision/auxiliary LLM calls;
3. ALFWorld valid_unseen tasks;
4. AndroidWorld fixed task instances/device environment;
5. B/J and applicable C controls;
6. three repeated runs on fixed tasks;
7. task-cluster paired uncertainty;
8. complete decision, auxiliary, environment and failed-attempt resource accounting;
9. recovery and completion traces;
10. cost/time per delivered success.

Do not substitute a generic small LLM for Jev and call that a reproduction of the core empirical claim.
