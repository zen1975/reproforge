# arXiv:2610.07782 — Verification Report

## Current verdict

**PARTIAL / MECHANISM_VERIFIED**

The paper separates two claims:

1. decomposing long-context inference across agents lowers the largest per-call KV working set;
2. a persistent cross-query trace-recall tier must be evaluated with an ablation that is actually capable of measuring memory efficacy.

ReproForge is currently verifying the second, reusable measurement protocol.

## Paper protocol captured

The paper reports that its persistent-memory arms are matched on dataset, sample count, seed, evidence scoping and endpoint, with traces reset between conditions and live isolation probes. It uses per-question pairing and bootstrap intervals, while also distinguishing paired sampling uncertainty from replicate-level run-to-run variation.

The four audit conditions are:

- **C1 — component executed:** a claimed component needs a non-zero execution counter;
- **C2 — runs independent:** pre-query the store with evaluation questions and reject pre-existing hits;
- **C3 — only named axis varied:** serialized requests should differ only on the ablation axis and execution order must be counterbalanced;
- **C4 — effect exceeds measurement floor:** replicate-derived variation must be estimated separately from a within-run bootstrap.

The paper further argues that on independent self-supplied single-question benchmarks, a correct reset removes self-recall and remaining cross-query traces are unrelated. In that regime the aggregate memory ablation may be correctly measured yet structurally uninformative about efficacy.

## Independent audit fixture

Experiment:

`persistent-memory-ablation-audit-v1`

The fixture independently constructs:

- a clean ablation satisfying C1-C4;
- an enabled-but-inert memory path;
- a contaminated pre-run store;
- a multi-axis + execution-order-confounded pair;
- an apparent effect below replicate-level measurement floor;
- an independent-item regime with reachable but irrelevant prior traces;
- a shared-state regime where prior state is actually relevant.

The audit is expected to accept the clean/shared-state cases and reject each defective case.

## Paper results not reproduced

The paper reports:

- peak KV per query of 14.3 MiB for its decomposed architecture versus 35.5 / 35.3 MiB baselines;
- persistent recall cost of +0.368 MiB;
- accuracy delta +0.015 with 95% CI [-0.011, +0.046];
- only about one question in four able to reach recall under the evaluated regime.

Those are hardware/model/benchmark measurements and are not outputs of this independent fixture.

## Remaining work

First freeze the audit-workflow result.

After that, paper-scale reproduction requires the serving stack, dataset cells, model endpoints, persistent store, and replicate execution needed to measure peak KV, latency and paired accuracy effects.

## What must not be claimed

Do not claim:

- reproduction of the 14.3 MiB peak-KV result;
- reproduction of the +0.015 accuracy effect;
- that persistent memory never helps;
- that the paper disproves persistent-memory efficacy.

The paper's own conclusion is narrower: under the tested independent-item regime, efficacy is structurally difficult to identify.
