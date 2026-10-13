# Pre-registration: jev-live-systemone-check-v2 (test phase)

Committed **before** any test-phase run. Pinned code/generator/analysis hash: `f76ba2b61a5814d82b487861f0c01cfc2375af91d125704365bce3e142fd951f` (see `experiments/jev_v2_freeze.json`; enforced by the runner, the verifier and a unit test). Any change to the pinned files => new experiment id (v3). v1 and both pilots are untouched.

## What is frozen
Generator version **g2** (`jev_v2_generator.py`), test seeds **3000-3011** (never run before this pin; pilots used 1000-1003 (g1) and 1100-1103 (g2)), workflow core, arm adapters and prompts, runner, and the analysis/verification code (`jev_v2_analysis.py`). 108 instances (9 families x 12) x 3 candidate orders x {natural, forced_trap} = 648 episodes per arm. Arms: Jev `jev-1.13.0` (Choice question) and **LLM candidate-interface control `claude-haiku-5-5`** (forced enum tool call, effort `low`, sampling parameters omitted, stochastic). One run per arm, each in its own process with its own key, run **once**; no re-runs on bad outcomes. Spend cap US$5 total.

## Framing (binding)
A stress test on Jev 1.13's documented weak spots plus a neutral `anchor` family, with a paired comparison against a named control. **Not** an ALFWorld/AndroidWorld reproduction, **not** an estimate of the paper's effect sizes, and a control advantage on the stressor families is read as "Jev is weaker where its vendor says it is weaker". `reproduction_status` stays `PARTIAL` whatever the outcome.

## Questions and endpoints
Primary (C5, recovery): paired difference (control - Jev) in final success on `forced_trap` episodes of the eight recoverable families (the harness forces the same wrong first action for both arms; `irreversible` is a negative control and is excluded; it must be 0% for both).
Secondary: (1) initial-choice correctness and final success on natural stress-family episodes; (2) `anchor` family as the neutral check; (3) cost and time per delivered success (failures stay in the numerator), decision latency per call; (4) the transfer classification (decision -> task -> delivered time); (5) order sensitivity (trap-first / truth-first / neither); (6) abstention (Jev can abstain; counted as an incorrect first decision but also reported separately); (7) per-family breakdowns.
Statistics: instance-cluster bootstrap 95% intervals (seed 20261014, 2000 resamples) and exact McNemar for paired binary outcomes, all as computed by the frozen analysis code. Descriptive only: no multiplicity adjustment, no causal claim.

## Interpretation rules (fixed in advance)
1. A Jev decision/speed advantage is **not** an agent advantage unless delivered-success metrics agree; report cost and time per delivered success next to success rate.
2. Outcomes at floor or ceiling for both arms are reported as non-discriminating, not as support for either side.
3. Speed and cost compare different providers and API conditions; they are reference values, not a controlled efficiency comparison.
4. Whatever happens (including Jev better, equal, or worse; incomplete runs; infrastructure failures) is committed as sanitized evidence and reported. Incomplete runs are labelled and not analysed as complete.

## Deviations and known limitations, disclosed now
- **Difficulty window not met by the control.** The pre-registered window was an initial-error rate of 10-60% for each arm on the stress families. Pilot 1 (g1): Jev 30.2% (inside), control 6.3% (outside). After one calibration iteration (g2), pilot 2: Jev 22.9% (inside), control **2.1%** (outside; harder-for-Jev stressors did not make the control err). The user chose to freeze g2 and proceed with disclosure rather than a further calibration round. Consequence: natural control errors will be rare, so the **forced-trap probes are the primary evidence for recovery**, and natural-episode comparisons mostly measure Jev's errors.
- `injected` is near the floor for Jev in pilot 2 (100% initial error, 8% final success) and `premature` does not discriminate (no premature completions in either arm); both are reported as such.
- The control is stochastic (the model rejects non-default sampling); Jev appears near-deterministic. One run per arm, so control run-to-run variability is not estimated.
- Arms are run sequentially on one machine; latency is client-side wall clock including network. Retries are logged separately from latency.
- Pilot data informed difficulty and the premature redesign (g1 -> g2) but test seeds were never run.

## Run procedure
Keys only from the macOS Keychain into the process environment (never in GitHub); `SSL_CERT_FILE=/etc/ssl/cert.pem` for the Jev (urllib) process. Order: Jev arm, then control arm, each `--phase test`. Then `jev_v2_analysis.py` over the two evidence files; commit the three sanitized files unmodified; CI verifies integrity only. Rotate both keys afterwards.
