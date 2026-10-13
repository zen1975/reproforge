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

## Live Jev check (prepared, not run)

`jev-live-systemone-check-v1` is a frozen, key-gated live protocol check against the real Jev API (`jev-1.13.0`). **Status: NOT_RUN** - no `TYPESAFE_API_KEY` was available, so there are no live results, and the aggregate-audit close above remains provisional rather than superseded. The harness (fixture hash pin, state machine, metrics, CI wiring) is verified offline against a fake server only; that verifies the harness, not Jev.

Even after a successful run this would be an actual-Jev System One *protocol check on a toy workflow*: it cannot establish the paper's ALFWorld/AndroidWorld effect sizes, and `reproduction_status` stays `PARTIAL`. Results will be descriptive, reported at decision, attempt, recovery/completion and delivered-success levels, with failed and invalid attempts retained. See `HANDOFF.md` for how to run it.
