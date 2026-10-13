# arXiv:2610.13092 — Verification Report

## Current verdict

**PARTIAL / MECHANISM_VERIFIED**

The paper asks a more useful question than whether Jev is individually fast:

> Do local decision savings survive the surrounding agent workflow and reduce the resources required to deliver successful tasks?

ReproForge therefore treats decision efficiency and successful-delivery efficiency as separate layers.

## Protocol decomposition

The paper evaluates five agent families across ALFWorld and AndroidWorld and uses three configuration concepts:

- **B**: original baseline decision strategy;
- **J**: Jev replaces action selection;
- **C**: an LLM uses the same candidate list and selection instruction as Jev.

For ALFWorld, B-vs-C isolates much of the candidate-interface change, while C-vs-J isolates the decision-model change under a shared candidate interface.

That distinction is frozen in this study. A B-vs-J delta must not automatically be attributed entirely to Jev.

## Paper-reported boundary

The paper reports Jev decision-level reductions of roughly:

- **66.1–78.4% lower decision cost**
- **73.9–81.5% lower decision time**

Yet task-level value varies sharply because the rest of the workflow still runs.

Examples:

- ReAct preserves most of the savings because action selection dominates baseline runtime.
- T3A adds auxiliary generation and loses completion rate.
- FastAgent makes more decisions and uses longer interaction sequences.

The most important successful-delivery example is T3A:

- mean cost per attempt falls from 39.48 to 32.73 mUSD;
- success falls from 200/348 to 154/348;
- cost per delivered success therefore rises from about 68.70 to 73.97 mUSD.

So:

**lower cost per attempt != lower cost per successful outcome**

FastAgent exposes the same issue in time:

- mean task time is nearly unchanged;
- success falls from 174/348 to 111/348;
- time per delivered success rises from about 239.4 to 377.8 seconds.

## Recovery boundary

The paper's Reflexion result is especially important.

Across the three runs:

- Baseline first-trial success: 376/402
- Jev first-trial success: 383/402

Jev is initially better.

But recovery among initial failures is:

- Baseline: 25/26
- Jev: 11/19

Final success becomes:

- Baseline: 401/402
- Jev: 394/402

Therefore:

**better initial selection != better final reliability**

The workflow must preserve the ability to detect a mistaken premise, recover, and verify completion.

## Failure taxonomy

The paper codes seven overlapping failure/behavior categories:

1. target identification;
2. prerequisite violation;
3. failed recovery;
4. premature completion;
5. ineffective search;
6. execution granularity;
7. output/state mismatch.

In persistent Jev-loss pairs, failed recovery and ineffective search are especially prominent. The paper also gives a Wi-Fi case where the agent selects an ambiguously labeled switch and terminates while the requested state is still unmet.

This supports a practical architecture boundary:

**fast bounded selection is safest when state, prerequisites, candidate semantics and completion criteria are explicit.**

## Independent published-aggregate audit

Experiment:

`jev-efficiency-transfer-audit-v1`

The independent audit encodes only published aggregate table values and recomputes:

- decision cost reduction;
- decision latency reduction;
- task cost/time deltas;
- cost per delivered success;
- time per delivered success;
- transfer classification.

Rounded table values reproduce the paper's successful-delivery figures within a fixed rounding tolerance and recover the reported decision-savings ranges.

This is an **aggregate arithmetic audit**, not an independent trajectory rerun.

## Independent mechanism fixture

The same audit contains synthetic workflow cases that deliberately separate:

- direct transfer;
- overhead absorption;
- delivery paradox;
- recovery loss after better initial success.

Required classifications:

`TRANSFERRED`

`OVERHEAD_ABSORPTION`

`DELIVERY_PARADOX`

The recovery fixture also verifies that a system can have higher first-pass success and still lower final success if correction is worse.

## Provenance / license boundary

Paper license:

**CC BY-NC-ND 4.0**

The paper links experimental code at:

`https://anonymous.4open.science/r/jev-emp-5BF4/`

A code license could not be independently verified through the accessible source, so ReproForge does not copy or redistribute that implementation.

## What is not yet reproduced

Do not claim:

- independent Jev benchmark reproduction;
- independent ALFWorld or AndroidWorld trajectory reproduction;
- independent confirmation of the reported Jev-vs-LLM effect sizes;
- independent trace-label reproduction;
- paper-level reproduction.

The current result verifies the evaluation contract and published aggregate arithmetic.

## Scientific interpretation

For System One insertion, the correct objective is not:

`decision latency`

or even:

`cost per attempt`

in isolation.

The operational chain is:

`decision efficiency -> workflow overhead -> recovery -> completion -> resource per delivered success`

A local optimizer is only useful when the final delivered outcome improves on the metric the system actually cares about.

## Frozen CI audit result

The machine-run audit completed successfully.

- workflow: `38431488012`
- artifact: `11831980273`
- digest: `sha256:ce25ab6a5af50d10821a5e874b4bba34d7c0e38817cfdb02e1c2f7e1f37b5750`
- result: **PASS**

Recomputed from published rounded aggregates:

- decision-cost reduction range: **66.03–78.44%**
- decision-time reduction range: **73.85–81.49%**
- all published successful-delivery values matched within fixed rounding tolerance.

The independent fixture also correctly detected direct transfer, overhead absorption, delivery paradox, and a recovery case where better initial success still produced worse final success.

No further meaningful free/lightweight experiment should replace the actual Jev/environment rerun. Therefore the study is now **HEAVY_COMPUTE_READY / PARTIAL** with `free_light_phase_complete: true`.

## Live Jev check (run locally, ceiling result)

`jev-live-systemone-check-v1` was run once against the real Jev API (`jev-1.13.0`, resolved for both the pinned ID and the `jev-latest` alias) on 2026-10-14. The key was used only in a local environment and never stored in GitHub; the sanitized result (sha256 `35fa635c0d8b9b97a6eea34ef3fdf1643340bed493d6370dbe3cee400d325fdd`) is committed unmodified and CI verifies its integrity.

| Level | Result |
|---|---|
| Decision (Test B, 36 decisions, 6 categories) | 36/36 valid and exact; 0 abstentions; mean 0.19 s/call, p95 0.26 s |
| Attempt (Test C, 24 attempts, 8 workflows x 3) | initial choice correct 24/24; prerequisite-valid 24/24 |
| Recovery / completion | 0 deviations, so recovery rate undefined; 0 premature completions; verification correct throughout |
| Delivered success | 24/24; about 0.74 s and $7.8e-05 (assumed $0.042/Mtok input) per delivered success |

**Interpretation boundary.** Everything is at ceiling, so this check shows only that the real API responds as documented and handles this small, explicit-state fixture correctly. It cannot show that faster decisions do or do not make better agents: no first-decision error, recovery or premature completion ever occurred live, and there was no control, so the paper's decision-vs-delivered-success gap and B/C/J separation remain untested with real Jev. Descriptive only; a harder v2 fixture would be needed. It is not an ALFWorld/AndroidWorld reproduction, `reproduction_status` stays `PARTIAL`, and no claim is made about the paper's effect sizes.

## Live Jev stress test v2 (run locally, frozen and pre-registered)

`jev-live-systemone-check-v2` compares real Jev (`jev-1.13.0`) with a separately named **LLM candidate-interface control (claude-haiku-5-5, not Jev)** on 9 generated families (neutral `anchor` + 8 stressors on Jev's documented weak spots), 3 candidate orders, natural and forced-trap episodes (648 episodes per arm). The generator was frozen after two pilots and pre-registered (pin `f76ba2b6...`, commit before the run), then run once per arm on never-seen seeds. Both arms completed (648/648, no infrastructure failures); spend US$0.09 + US$0.38. Sanitized evidence is committed unmodified and CI verifies integrity (`evidence/jev_v2_test_*.json`); keys stayed local.

| Pre-registered endpoint | Jev | Control | Difference (control - Jev) |
|---|---|---|---|
| **Primary: forced-trap recovery, recoverable families** | 87.2% | 97.2% | +10.1 pt, 95% CI [3.5, 17.4], exact McNemar p=4.9e-06 |
| Initial choice correct, stress natural | 79.9% | 95.5% | +15.6 pt, CI [8.7, 22.9] |
| Final success, stress natural | 84.0% | 98.6% | +14.6 pt, CI [7.6, 21.9] |
| `anchor` / `irreversible` negative control | 100% / 0% | 100% / 0% | non-discriminating / as designed |
| Decision latency per call | 0.19 s | 1.52 s | reference only (different providers) |
| Time / cost per delivered success (natural) | 1.10 s / $1.5e-04 | 6.34 s / $5.6e-04 | reference only |

**Interpretation boundary.** On this stress fixture Jev is about 85% faster per decision but **not** better on delivered success: the speed advantage did not become an agent advantage, consistent with (but not a test of) the paper's caution. The success gap is concentrated in the `injected` family (Jev 14-19% vs 97%) plus `numeric` initial choices; excluding `injected`, forced-trap recovery is 96.8% vs 97.2%, and `indirection` favours Jev. The control stayed outside the pre-registered difficulty window (disclosed before the run), `order_decoy`/`premature`/`anchor` did not discriminate, the control is stochastic with one run, and statistics are descriptive. This is **not** an ALFWorld/AndroidWorld reproduction and says nothing about the paper's effect sizes; `reproduction_status` stays `PARTIAL`. B arm and auxiliary-overhead mechanisms (T3A/FastAgent-type) are untested.
