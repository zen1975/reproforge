# arXiv:2610.07782 — Verification Report

## Current verdict

**PARTIAL / HEAVY_COMPUTE_READY**

The current free/lightweight boundary is complete.

The paper's reusable contribution for ReproForge is not a claim that persistent memory never helps. It is a protocol for determining whether a memory ablation actually measures memory at all.

## Independent C1-C4 audit

Experiment: `persistent-memory-ablation-audit-v1`

Workflow: `38046596329`

Artifact: `11668225187`

Digest:

`sha256:2338d3b42a145913416a0e5191de7c20799b69fe3c133727dc8b2fc195c9a31e`

Result: **ALL PASS**

The clean fixture passed:

- C1: claimed memory write/recall path executed;
- C2: no pre-run store contamination;
- C3: arms differed only in `kv_enabled` and order was counterbalanced;
- C4: a deliberately large effect exceeded the replicate-derived measurement floor.

Injected defects were all detected:

- C1 inert recall path: rejected;
- C2 pre-existing evaluation hits: rejected;
- C3 endpoint/parser changes plus one-sided run order: rejected;
- C4 effect 0.02 below replicate-derived approximate 95% band ±0.08536: marked unresolvable.

## Structural applicability boundary

The fixture also separates **recall reachability** from **useful memory efficacy**.

Independent-item regime:

- recall reachable: 37.5%;
- useful prior-state recall: 0%;
- efficacy testable: **false**.

Shared-state regime:

- recall reachable: 75%;
- useful prior-state recall: 75%;
- efficacy testable: **true**.

So:

`memory path reachable != memory efficacy testable`

This is the core lightweight boundary.

## Paper measurements not reproduced

The paper's hardware/benchmark results include:

- decomposed peak KV ≈ 14.3 MiB versus 35.5 / 35.3 MiB baselines;
- persistent-recall peak-KV cost +0.368 MiB;
- accuracy effect +0.015 with 95% CI [-0.011, +0.046];
- recall reachable for only a minority of questions in the independent-item regime.

Those require the serving stack, model geometry, persistent store, datasets and replicate campaign. They are not outputs of this independent audit fixture.

## Current-environment closure

No further prompt-level or CPU-only analogue would materially test the paper's remaining hardware/benchmark claims.

Therefore:

- `HEAVY_COMPUTE_READY`
- `free_light_phase_complete: true`
- `reproduction_status: PARTIAL`

## What must not be claimed

Do not claim:

- full paper reproduction;
- reproduction of peak-KV/latency numbers;
- reproduction of the paper accuracy CI;
- that persistent memory has zero value;
- that independent-item benchmarks can prove persistent-memory efficacy merely because recall sometimes fires.
