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

## Pending frozen evaluation: `jev-live-systemone-check-v1` (NOT_RUN)

Real Jev (TypeSafe System One) live protocol check. Inputs are frozen; **no live run has happened** (no API key available at preparation time), so there is no result and nothing here counts as evidence.

- fixture: `experiments/jev_live_systemone_check_v1.fixture.json` (sha256 pinned in the runner; the runner refuses a modified fixture)
- runner: `experiments/run_jev_live_systemone_check.py` (stdlib only; prints `SKIPPED_NO_CREDENTIAL` and exits 0 without a key; writes no evidence when skipped)
- workflow: `.github/workflows/jev-live-systemone-check.yml` (`workflow_dispatch` only, to avoid repeated paid "first runs")
- API contract (official docs, retrieved 2026-10-14): `POST https://api.typesafe.ai/v1/systemone`, Bearer key, `model` pinned to `jev-1.13.0` (`jev-latest` only probed), Choice question with `criteria`; response has `model`, `answers`, `usage` (token counts only). **No latency or cost fields**: latency is client-side, cost is `input_tokens x $0.042/Mtok` (assumed price, source recorded in the fixture). No native abstention: an explicit `abstain` option is part of every Choice.
- Test A identity (models list, pinned + alias probes), Test B (12 cases x 3 repeats, six categories), Test C (8 deterministic workflows x 3 repeats with prerequisite errors, undo-based recovery and a Jev-answered completion-verification step), non-model reference policies for context.
- Metrics are kept at four levels: decision -> attempt -> recovery/completion -> delivered success (cost and time per delivered success, failures in the numerator).
- No LLM candidate-interface control in v1 (B-vs-C / C-vs-J not tested). A control, if added, must be its own experiment id, named "LLM candidate-interface control", never "Jev".
- Harness self-checks (`tests/test_jev_live_systemone_check.py`) use a local fake server and scripted selectors. They validate the harness only.

To run: `pbpaste | tr -d '\r\n' | gh secret set TYPESAFE_API_KEY -R zen1975/reproforge`, then `gh workflow run jev-live-systemone-check.yml -R zen1975/reproforge`. Persist the artifact unmodified; do not tune prompts, cases or thresholds after seeing it (changes => v2). Only after a successful run: set `free_light_phase_complete: false`, add the live check as a lightweight verification, re-evaluate. `reproduction_status` stays `PARTIAL` regardless: ALFWorld/AndroidWorld are not run.

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
