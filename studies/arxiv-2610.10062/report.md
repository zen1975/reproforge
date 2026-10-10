# arXiv:2610.10062 — Verification Report

## Current verdict

**PARTIAL / HEAVY_COMPUTE_READY**

The current free/lightweight boundary is complete. ReproForge has independently checked the paper protocol and core fault semantics, re-aggregated the released 1,920-trial scored table, and executed a real pinned 0.5B model analogue.

This is **not** paper-level reproduction because comparable multi-turn model trajectories have not been independently regenerated.

## Source and provenance

- Paper: https://arxiv.org/abs/2610.10062
- Author repository: https://github.com/obadaKraishan/brittle-agents
- Pinned author commit: `7abc4bc26e29fa4d1e7799e94bc7c2a96ce3fc66`
- Author code license: MIT
- BFCL-derived released data: Apache-2.0
- BFCL dataset revision declared by author: `61fc0608cfd831fcfbbaa676ebdfef0ed963eeda`
- Gorilla environment commit declared by author: `6ea57973c7a6097fd7c5915698c54c17c5b1b6c8`

## Official released-data audit

Direct re-aggregation of the released `master_trials.csv` produced:

- clean baseline detection: **26.797%** (82 / 306)
- quiet silent-corruption detection: **58.824%** (220 / 374)
- loud-fault detection: **91.346%** (855 / 936)
- timeout: **91.557%**
- missing tool: **91.209%**
- schema drift: **91.197%**

Matched reasoning-vs-instruct audit:

- matched pairs: **450**
- pooled detection difference: **-9.333 pp**
- pooled replanning difference: **+10.444 pp**
- Claude detection difference: **-6.211 pp**
- DeepSeek detection difference: **-3.968 pp**
- Qwen detection difference: **-16.564 pp**

These match the released paper outputs to displayed precision.

This remains an **OFFICIAL_AUDIT**, not independently generated model behavior.

## Independent synthetic mechanism verification

Experiment: `tool-fault-mechanism-synthetic-v1`

Verified:

- one-shot fault firing;
- explicit-error loud faults;
- well-formed quiet corruption;
- quiet corruption preserves payload structure/type;
- quiet corruption keeps the underlying successful state mutation;
- replanning semantics;
- repetition threshold;
- exact and partial state-agreement semantics.

Result: **PASS**

## Real 0.5B model-backed boundary

Experiment: `tool-fault-qwen0.5b-analogue-v1`

Model:

`Qwen/Qwen2.5-0.5B-Instruct`

Resolved revision:

`7ae557604adf67be50417f59c2c2f167def9a775`

Environment:

- PyTorch `2.14.1+cpu`
- Transformers `4.57.6`
- GitHub Actions CPU runner

Frozen fixture:

- 6 tasks
- clean / loud / quiet
- 18 decisions total
- fixed ACCEPT / RETRY / VERIFY interface

Result:

- valid outputs: **18 / 18**
- clean: **VERIFY 6 / 6**
- loud: **VERIFY 6 / 6**
- quiet: **VERIFY 6 / 6**
- clean detection rate: **1.0**
- loud detection rate: **1.0**
- quiet detection rate: **1.0**
- loud - quiet: **0.0 pp**

Workflow: `38045644197`

Artifact: `11666539238`

Artifact digest:

`sha256:1b1640beb999e672af4c0617b09cb7efa18020754dc06cb42d26a7c6fcdd08a1`

Interpretation:

This is **negative boundary evidence**.

The model obeyed the decision interface but did not discriminate between normal results, explicit failures, and silent corruption. It collapsed to a conservative `VERIFY` policy for every case.

Therefore:

`valid decision interface != fault-type discrimination`

The frozen fixture must not be prompt-tuned to manufacture a loud/quiet effect.

## Current-environment closure

The remaining meaningful work is no longer another prompt variation on the 0.5B fixture.

The next step is independently generated, paper-relevant multi-turn trajectories using a legal BFCL-compatible environment and larger/comparable model execution.

Therefore the study is:

- `HEAVY_COMPUTE_READY`
- `free_light_phase_complete: true`
- `reproduction_status: PARTIAL`

## What must not be claimed

Do not claim:

- full paper reproduction;
- independent confirmation of the paper's 91.3% vs 58.8% behavioral gap;
- that 0.5B models reproduce the paper phenomenon;
- general reasoning-vs-instruct conclusions from the 0.5B analogue.

The 0.5B result is specifically a negative boundary result.
