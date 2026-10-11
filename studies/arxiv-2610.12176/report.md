# arXiv:2610.12176 — Verification Report

## Current verdict

**PARTIAL / HEAVY_COMPUTE_READY**

The current free/lightweight boundary is complete.

MASS is especially relevant because it closes an explicit recursive loop:

current model
→ workflow optimization with homogeneous model copies
→ self-evaluation
→ trajectory generation/ranking
→ task-solving post-training
→ updated model
→ updated model becomes executor/evaluator/optimizer
→ next cycle

ReproForge does not treat "RSI worked" as one claim. The loop is separated into workflow-search quality, self-evaluator quality, task-solving improvement, cross-role transfer, coordination internalization, recursive generation-to-generation improvement, and held-out external confirmation.

## Paper protocol captured

Within generation g:

- executor = evaluator = optimizer = L(g);
- every workflow proposal is executed;
- an incumbent changes only when the self-evaluator prefers the proposal;
- retained workflows generate candidate trajectories;
- pairwise self-evaluation becomes a task-local trajectory ranking;
- top trajectories are used for training and a separate trajectory for validation;
- optimized workflow text is removed from the SFT prompt;
- test tasks do not enter SFT;
- strong external judges remain outside the inner MASS loop;
- the updated model assumes executor/evaluator/optimizer roles in the next generation.

## Important paper-reported results

The paper reports:

- evaluator agreement with external judgments: **0.73 -> 0.91 -> 0.93**;
- synthetic test-task win rate vs L0: **53.9% after cycle 1**, **69.9% after cycle 2**;
- L1-generated workflows executed by fixed L0 beat L0 workflows in **64%** of comparisons;
- bare-prompt delegation: **1/110 -> 48/110 -> 87/110**;
- bare-prompt code handoff: **1/110 -> 42/110 -> 83/110**.

Those are paper-reported results only. ReproForge has not independently reproduced them.

The paper also contains an important causal limitation: some public-benchmark gains occur without observed delegation, so public transfer gains cannot simply be attributed to multi-agent delegation.

## Official-repository provenance boundary

Official repository: `SakanaAI/mass`

Pinned inspected revision:

`fb403581bed2c974b3f99e7236224169da643079`

The repository NOTICE states that MASS-specific code has no public open-source license. ReproForge therefore inspects it for provenance/protocol evidence but does not copy or redistribute it.

The official repository also documents reconstruction differences, including:

- a current RHI driver that uses a fixed bare-task reference before retained-champion comparison rather than exactly matching the paper's direct incumbent comparison;
- no complete historical run ledger;
- reconstructed second-cycle budget details;
- reconstructed tournament schedule/seeds.

These differences remain part of the claim boundary.

## 1. Independent RSI-loop mechanism

Experiment:

`mass-rsi-loop-mechanism-v1`

Verified:

- homogeneous executor/evaluator/optimizer roles within a generation;
- recursive model-generation transition;
- elite-one retention;
- losing/non-monotonic proposals are still executed;
- train/test isolation;
- task-local trajectory selection;
- train/validation separation;
- self-evaluation inside the loop;
- external evaluation held out from selection.

Result: **PASS**

This verifies the protocol contract only.

## 2. Real 0.5B workflow/evaluator boundary

Experiment:

`mass-qwen0.5b-workflow-eval-analogue-v1`

Model:

`Qwen/Qwen2.5-0.5B-Instruct`

Resolved revision:

`7ae557604adf67be50417f59c2c2f167def9a775`

Results:

### Self-evaluator

- cases: 6
- parseable CANDIDATE/INCUMBENT outputs: **6/6**
- valid rate: **100%**
- accuracy against frozen external truth: **50%**

### Workflow optimizer

- cases: 4
- structurally valid workflows: **1/4 = 25%**
- non-empty contract fields: **3/4 = 75%**

Observed structural failure modes included role/hop mismatch, non-role values in hop, and truncated/unparseable JSON.

Interpretation:

`valid evaluator interface != evaluator competence`

and

`workflow proposal != executable workflow`

Workflow run:

`38125113256`

Artifact:

`11696229955`

Digest:

`sha256:d3ffa2643580b09e81dcc1b43f1bc260b761338f3905182918a782272d8f4044`

## 3. Tiny one-cycle task-solving-only LoRA boundary

Experiment:

`mass-qwen0.5b-one-cycle-lora-v1`

The model was trained only on four coordination-rich **task-solving traces**.

It was **not** trained on:

- CANDIDATE/INCUMBENT evaluator labels;
- optimizer gold workflows;
- evaluator accuracy targets.

Training:

- examples: 4
- steps: 4
- learning rate: 2e-5
- LoRA: small CPU analogue
- model: Qwen2.5-0.5B-Instruct

Within the same run:

### Evaluator

Before: **50% accuracy**
After: **50% accuracy**
Delta: **0.0**

Valid output rate stayed 100%.

### Optimizer

Before valid-workflow rate: **0%**
After valid-workflow rate: **0%**
Delta: **0.0**

Therefore this frozen tiny analogue found **no cross-role transfer** from task-solving-only coordination traces into evaluator or optimizer competence.

This is negative/null boundary evidence.

It does **not** contradict the paper's large-model result: the analogue differs drastically in model scale, number and diversity of trajectories, training tokens, optimization duration, context length, multi-agent environment, and recursive cycles.

Workflow:

`38125358438`

Artifact:

`11697580235`

Digest:

`sha256:6134421ddd72c077a13b578748e6410ed19f39f7405b348fe46df3d3e0b93ae2`

### Baseline comparability warning

The standalone workflow/evaluator run measured optimizer valid-workflow rate at 25%, while the separate one-cycle run measured its own pre-training baseline at 0%.

These are separate executions and must not be merged into a single before/after series.

The one-cycle transfer conclusion therefore uses **only the paired before/after values from the same one-cycle run**:

- evaluator: 50% -> 50%;
- optimizer: 0% -> 0%.

No explanation for the between-run baseline difference is invented.

## Current-environment closure

The remaining scientifically meaningful step is no longer another prompt variation or a post-hoc increase of training steps on this frozen 0.5B fixture.

The next step requires a substantially more paper-relevant recursive training setup:

- larger/comparable model;
- real multi-agent task execution;
- workflow search;
- trajectory collection/ranking;
- model weight update;
- held-out optimizer/evaluator testing;
- ideally at least a second recursive cycle;
- external evaluation independent of the inner loop.

Therefore:

- `lifecycle: HEAVY_COMPUTE_READY`
- `free_light_phase_complete: true`
- `reproduction_status: PARTIAL`

## What must not be claimed

Do not claim:

- MASS paper reproduction;
- independent demonstration of RSI;
- independent reproduction of evaluator improvement;
- independent reproduction of optimizer improvement;
- that the null 0.5B result refutes MASS;
- that coordination is the causal mechanism behind all paper benchmark gains.

The verified lightweight conclusion is narrower:

**The MASS recursive protocol is reconstructable, but a real 0.5B model showed weak self-evaluation/workflow construction and no measurable cross-role transfer after a tiny task-solving-only LoRA cycle.**
