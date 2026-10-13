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

## Frozen evaluation: `jev-live-systemone-check-v1` (RUN locally 2026-10-14, LIVE_CHECK_PASS at ceiling)

Real Jev (TypeSafe System One) live protocol check, run once locally. Evidence: `evidence/jev_live_systemone_check_v1.result.json` (sha256 `35fa635c0d8b9b97a6eea34ef3fdf1643340bed493d6370dbe3cee400d325fdd`), committed unmodified; CI verifies integrity only.

Result (descriptive): resolved model `jev-1.13.0` (pinned and `jev-latest` alias both); Test B 36/36 exact, 36/36 valid, 0 abstain; Test C 24/24 final success, initial choice correct 24/24, 0 deviations, 0 premature completions, 0 infrastructure failures; mean decision latency about 0.19 s/call (p95 0.26 s); about 0.74 s and $7.8e-05 (assumed price) per delivered success; total spend about $0.0026. **Ceiling effect**: because nothing went wrong, recovery, premature completion and better-first-but-worse-final were not exercised live (they are verified only in the offline harness with scripted selectors), and there was no control, so no interface-vs-model separation. `models_list` returned only aliases (`jev-latest`, `jev-preview`), as documented.

Provenance: executed locally at git head `1f2be8f` with the then-uncommitted runner whose sha256 equals the runner committed immediately afterwards (`dirty: true` in the evidence is genuine). First attempts hung/aborted before producing any result because this Mac's Python lacked a CA bundle (TLS errors were retried as transient); the runner was then changed to fail fast, and the run needs `SSL_CERT_FILE=/etc/ssl/cert.pem` on this machine. Those aborted attempts produced no evidence.

- fixture: `experiments/jev_live_systemone_check_v1.fixture.json` (sha256 pinned in the runner; the runner refuses a modified fixture)
- runner: `experiments/run_jev_live_systemone_check.py` (stdlib only; **local execution only**; on this macOS prefix the command with `SSL_CERT_FILE=/etc/ssl/cert.pem`; prints `SKIPPED_NO_CREDENTIAL` and exits 0 without a key; writes no evidence when skipped)
- CI: `.github/workflows/jev-live-evidence-verify.yml` runs `experiments/verify_jev_live_evidence.py` only: integrity of the committed sanitized result vs the frozen fixture (hashes, row/aggregate recomputation, header allowlist, credential patterns). No key, no network, no secrets. It checks integrity, not Jev quality; poor or failing results verify fine and must be kept.
- API contract (official docs, retrieved 2026-10-14): `POST https://api.typesafe.ai/v1/systemone`, Bearer key, `model` pinned to `jev-1.13.0` (`jev-latest` only probed), Choice question with `criteria`; response has `model`, `answers`, `usage` (token counts only). **No latency or cost fields**: latency is client-side, cost is `input_tokens x $0.042/Mtok` (assumed price, source recorded in the fixture). No native abstention: an explicit `abstain` option is part of every Choice.
- Test A identity (models list, pinned + alias probes), Test B (12 cases x 3 repeats, six categories), Test C (8 deterministic workflows x 3 repeats with prerequisite errors, undo-based recovery and a Jev-answered completion-verification step), non-model reference policies for context.
- Metrics are kept at four levels: decision -> attempt -> recovery/completion -> delivered success (cost and time per delivered success, failures in the numerator).
- No LLM candidate-interface control in v1 (B-vs-C / C-vs-J not tested). A control, if added, must be its own experiment id, named "LLM candidate-interface control", never "Jev".
- Harness self-checks (`tests/test_jev_live_systemone_check.py`) use a local fake server and scripted selectors. They validate the harness only.

Key policy: `TYPESAFE_API_KEY` is **never** stored in the GitHub repository or Actions secrets (public repo); it was used only in a local process environment. Rotate it. v1 inputs and evidence must not be edited; any change (harder cases, thresholds, prompts) is `jev-live-systemone-check-v2`. `reproduction_status` stays `PARTIAL`: ALFWorld/AndroidWorld are not run.

Next lightweight experiment (steps 1-2 implemented and offline-tested; pilot/test NOT run): `design/jev-live-systemone-check-v2.md` (Jev vs a named LLM candidate-interface control on a stressor fixture, pilot/test split, pre-registered rules).

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
