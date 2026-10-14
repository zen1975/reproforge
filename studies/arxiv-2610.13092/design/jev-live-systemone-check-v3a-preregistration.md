# Pre-registration: jev-live-systemone-check-v3a (test phase)

Committed **before** any v3a test run. Pins: v3a code `c7ac3d0e61a40f0b7d31d56ea31b0c61f095e50b68d2a46134002b496cdbe60a` (`jev_v3_arms.py`, `jev_v3_run.py`, `jev_v3_analysis.py`; see `experiments/jev_v3a_freeze.json`) and the unchanged v2 pin `f76ba2b61a5814d82b487861f0c01cfc2375af91d125704365bce3e142fd951f` (core, generator g2, arms, run, analysis). Both are enforced by the runner, the verifier and unit tests. Any change to a pinned file => new experiment id. v1, v2 and the v3a pilot are untouched. Design: `design/jev-live-systemone-check-v3.md`.

## What is frozen
Frozen generator **g2** on fresh test seeds **4000-4011** (pilots used 1000-1003 (g1), 1100-1103, 5000-5003; v2 test used 3000-3011): 108 instances (9 families x 12) x 3 order indices x {natural, forced_trap} = 648 episodes per arm. Three arms, each in its own process, run **once**, never re-run on bad outcomes:
- **J**: Jev `jev-1.13.0` (Choice question), unchanged from v2.
- **C**: LLM candidate-interface control `claude-haiku-5-5` (forced enum tool call, effort `low`), unchanged from v2.
- **B**: LLM free-generation baseline **analogue** (same model; fixed alphabetical command reference with descriptions, no abstain token, short rationale then `ACTION: <command>`, strict parser, unparsable => invalid response and a consumed step; `max_tokens` 400, effort `low`). **Not the paper's B** (its prompt is unavailable); named as an analogue everywhere. B's prompt does not depend on `order_idx`: its three rows per instance are independent stochastic replicates.
Sampling parameters are omitted (the model rejects non-default values), so B and C are stochastic; one run per arm, run-to-run variability not estimated. Per-arm spend caps: Jev US$0.5, C US$1.5, B US$3.0 (US$5 total; pilot measured about US$0.03 / 0.13 / 0.13 per 216 episodes).

## Framing (binding)
A three-arm contrast on the frozen v2 stress fixture (stressors chosen from Jev 1.13's documented weak spots plus a neutral anchor). **Not** an ALFWorld/AndroidWorld reproduction, **not** an estimate of the paper's effect sizes, no auxiliary overhead (so `OVERHEAD_ABSORPTION` and the C2/C3 delivery-paradox mechanisms are not tested here; that is v3b). `reproduction_status` stays `PARTIAL` whatever the outcome.

## Endpoints
Contrasts are paired on identical (instance, order_idx, episode type) units; instance-cluster bootstrap 95% CIs (seed 20261014, 2000 resamples) and exact McNemar, as computed by the frozen analysis code. Descriptive: no multiplicity adjustment, no causal claim.
- **P1 interface effect (paper C4a)**: C - B on final success of `forced_trap` episodes in the eight recoverable families; companion C - B on initial-choice correctness and final success on natural stress-family episodes.
- **P2 decision-model effect and replication (paper C4b)**: C - J on the same endpoints. **Replication rule, fixed now:** the v2 primary (control better on forced-trap recovery; v2 diff +10.1 pt, CI [3.5, 17.4]) is "replicated" only if the v3a C - J diff is > 0 and its cluster-bootstrap 95% CI excludes 0; otherwise reported as "not replicated". The v2 values are read from the committed v2 analysis (sha256 pinned in the code).
- **Secondary**: J - B combined contrast (never attributed to Jev alone); decision latency per call, input/output tokens per call, cost and time per delivered success (failures stay in the numerator); B invalid-response rate; per-family breakdowns; order effects for C and J; transfer classification of each pair (reference only).

## Interpretation rules (fixed in advance)
1. A decision-level advantage (speed, tokens, cost per call) is **not** an agent advantage unless delivered-success metrics agree.
2. A contrast whose two cells are both near 0% or 100% is reported as **non-discriminating**, not as support for either side.
3. Speed and cost compare different providers; they are reference values, not a controlled efficiency comparison. Jev cost = tokens x an assumed US$0.042/Mtok.
4. Incomplete runs (spend cap, errors, interruption) are labelled and not analysed as complete. All outcomes, including Jev better/equal/worse, are committed as sanitized evidence and reported.

## Known limitations, disclosed now
- **Likely low power for P1.** In the pilot B and C were both at or near ceiling on natural episodes (B 100%, C 100% final success; initial 100% vs 94.8%), so the B-vs-C interface effect may be non-discriminating at this n. This is disclosed rather than corrected; no parameter was tuned after seeing the pilot.
- B has no abstain token; in the `irreversible` negative-control family it can only produce invalid responses (34 in the pilot). The negative control is expected to be 0% for all arms.
- The v2 generator's non-discriminating families (`anchor`, `order_decoy`, `premature`) are kept unchanged; the control stays outside the v2 difficulty window.
- The B analogue is an interpretation of the paper's description; amendments before this pre-registration (descriptions added to B's command reference) are documented in design section 4 and happened before any result.
- Arms run sequentially on one machine; latency is client-side wall clock including network.

## Run procedure
Keys only from the macOS Keychain into the process environment (`SSL_CERT_FILE=/etc/ssl/cert.pem` for Jev); the existing keys are reused (user decision), local-only, never in GitHub. Order: J, C, B, each `--phase test`. Then `jev_v3_analysis.py` over the three evidence files; commit the four sanitized files unmodified; CI verifies integrity only. Rotation of both keys and Keychain deletion after v3a/v3b.
