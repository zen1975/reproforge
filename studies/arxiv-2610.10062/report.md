# arXiv:2610.10062 — Verification Report

## Current verdict

**PARTIAL / PROTOCOL_VERIFIED**

The paper's fault taxonomy, measurement decomposition, released-data aggregation, and core injection/scoring semantics are now independently checked. The study is **not** reproduced at paper level because ReproForge has not independently generated comparable model trajectories.

## Source and provenance

- Paper: https://arxiv.org/abs/2610.10062
- Author repository: https://github.com/obadaKraishan/brittle-agents
- Pinned author commit: `7abc4bc26e29fa4d1e7799e94bc7c2a96ce3fc66`
- Author code license: MIT
- BFCL-derived released data: Apache-2.0
- BFCL dataset revision declared by author: `61fc0608cfd831fcfbbaa676ebdfef0ed963eeda`
- Gorilla environment commit declared by author: `6ea57973c7a6097fd7c5915698c54c17c5b1b6c8`

## Paper protocol captured

The design uses five conditions: clean, timeout, missing tool, schema drift, and silent corruption. Timeout, missing tool, and schema drift surface explicit errors; silent corruption returns a well-formed but wrong value.

The paper separates:

- detection;
- replanning;
- recovery relative to the same model's independent clean end state;
- repeated use of the same tool;
- effort relative to the model/task clean baseline.

## Official released-data audit

ReproForge re-aggregated the released `master_trials.csv` directly rather than trusting the paper tables or author analysis outputs.

Observed from 1,920 rows:

- clean target-success baseline detection: 82 / 306 = **26.797%**
- quiet silent-corruption detection: 220 / 374 = **58.824%**
- loud-fault detection: 855 / 936 = **91.346%**
- timeout: 347 / 379 = **91.557%**
- missing tool: 249 / 273 = **91.209%**
- schema drift: 259 / 284 = **91.197%**

Matched reasoning-vs-instruct audit:

- matched pairs: **450**
- pooled detection difference: **-9.333 percentage points**
- pooled replanning difference: **+10.444 percentage points**
- Claude detection difference: **-6.211 points**
- DeepSeek detection difference: **-3.968 points**
- Qwen detection difference: **-16.564 points**

These match the released paper results to displayed precision.

This is an **OFFICIAL_AUDIT**, not independent model reproduction.

## Independent synthetic mechanism verification

Experiment: `tool-fault-mechanism-synthetic-v1`

Verified:

- clean condition injects no fault;
- each non-clean condition fires exactly once;
- loud faults do not apply the underlying successful state mutation at the faulted call;
- silent corruption applies the successful underlying state transition;
- silent corruption alters the returned payload while preserving structure/type;
- replanning is triggered by tool or argument change;
- three consecutive same-tool calls satisfy the repetition rule;
- exact and partial state-agreement semantics execute as declared.

Result: **PASS**

## Remaining lightweight work

A real small-model analogue is still justified before this study can be closed at the current-environment boundary.

The next experiment must be frozen before execution and should compare at least:

- clean;
- one loud explicit-error condition;
- quiet well-formed corruption.

It should preserve raw model outputs and tool traces, and must not be prompt-tuned after observing whether a loud/quiet gap appears.

## What must not be claimed yet

Do not claim:

- paper-level reproduction;
- independent confirmation of the 91.3% vs 58.8% behavioral rates;
- confirmation that reasoning models generally detect less;
- confirmation of paper recovery effects.

Those require independently generated trajectories.
