# arXiv:2610.02858 — Continuation Handoff

## State

- Lifecycle: `HEAVY_COMPUTE_READY`
- Reproduction verdict: `PARTIAL`
- Free/lightweight phase: complete

ReproForge independently implements the Harness-Aware Distillation (HAD) mechanism described in arXiv:2610.02858 and has executed both deterministic protocol checks and a real Qwen2.5-0.5B LoRA training smoke.

## Already executed

- authoritative arXiv intake and full 28-page paper/appendix review;
- paper protocol configuration capture;
- same-teacher with-harness / without-harness preference abstraction;
- positive-action validity masking;
- action-only length-normalized preference margin;
- reference-free logistic preference loss with beta=0.5;
- minibatch gradient balancing with rho=0.5;
- fail-safe lambda=0 when preference gradient is zero;
- synthetic protocol verification: 10 / 10 checks PASS;
- real Qwen2.5-0.5B-Instruct LoRA training path;
- distillation-only and HAD comparison on the same frozen synthetic harness set;
- six-step HAD run including an invalid preferred action;
- invalid preferred action produced preference loss=0, preference grad=0, lambda=0 as intended;
- CI on Python 3.11 / 3.12.

## Real 0.5B smoke result

The six-step synthetic comparison is intentionally too small for an efficacy claim.

Both paths remained at 75% accuracy on the four-example frozen held-out set.

Mean action-margin change:

```text
distill-only   -0.002632
HAD            +0.003469
difference     +0.006101
```

This direction is recorded only as a smoke result. It is not statistical evidence that HAD outperforms response distillation.

## What is not reproduced

ReproForge has not reproduced the paper's benchmark-scale training or reported performance gains.

Remaining paper-scale work includes:

- on-policy student trajectory collection;
- same-teacher paired queries at student-visited states;
- full response distillation rather than the minimal synthetic positive-action analogue used in the smoke;
- paper-scale students in the approximately 0.6B–1.7B range;
- larger teacher models;
- ALFWorld;
- WebShop;
- ScienceWorld;
- 150–250 update training runs;
- effective batch size 60;
- exact harness-utilization evaluation;
- paper-reported task performance;
- multi-seed robustness.

Therefore `REPRODUCED` is not justified.

## Frozen evaluations — do not tune against

Do not tune against:

- `had-synthetic-protocol-v1`;
- `had-qwen0.5b-distill-only-smoke-v2`;
- `had-qwen0.5b-had-smoke-v2`;
- the four-example frozen held-out harness set embedded in the v2 smoke.

For new prompt/data/training choices, create a new version and unseen held-out harness states.

## Published protocol currently captured

```text
beta                         0.5
rho                          0.5
optimizer                    AdamW
learning rate                1e-5
weight decay                 0.01
gradient clipping            1.0
schedule                     cosine to 0
warmup                       15 updates
effective batch size         60
rollout tasks / round        16
staleness                    2 policy versions
rollout temperature          1.0
evaluation temperature       0.4
ALFWorld updates             250
WebShop updates              150
ScienceWorld updates         150
OPD teacher top-k tokens     64
```

No unpublished coefficients, seeds, prompts, dataset details, or model revisions should be invented.

## Recommended local continuation

The next useful step is not a larger synthetic smoke. Build the on-policy data-generation loop:

```text
student visits state
        ↓
capture student reasoning prefix
        ↓
teacher WITH harness → a+
teacher WITHOUT harness → a-
        ↓
validate a+ against harness records
        ↓
response-distillation record
+
masked action-preference record
        ↓
student update
```

Start with one small open student and one open teacher before attempting all paper environments.

A practical first local track is:

1. Qwen-family student around 0.6B–1.7B;
2. one larger open teacher;
3. one simple interactive environment or a legally usable synthetic harness environment;
4. distill-only versus HAD with frozen unseen evaluation states;
5. multiple seeds before any performance claim.

## ReproForge entrypoints

```text
capabilities/training.harness-aware-action-distillation/had.py
studies/arxiv-2610.02858/experiments/run_had_synthetic.py
studies/arxiv-2610.02858/experiments/run_qwen0.5b_had_smoke.py
.github/workflows/had-synthetic.yml
.github/workflows/had-qwen0.5b-smoke.yml
```

## Expected continuation evidence

Preserve student/teacher model revisions, licenses, harness state, student reasoning prefix, paired teacher actions, validity result, beta/rho, losses, gradient norms, lambda, optimizer/schedule, seeds, trajectory hashes, held-out definitions, task success where available, multi-seed variance, and explicit differences from the paper.

Do not commit model weights, secrets, restricted benchmark data, or paper artifacts without verified permission.

## Promotion

Do not promote to `REPRODUCED` because the Qwen2.5-0.5B smoke executes.

Promotion requires a sufficiently equivalent on-policy teacher/student training experiment and benchmark evidence supporting the declared paper-level claims.

Until then:

```text
lifecycle: HEAVY_COMPUTE_READY
reproduction_status: PARTIAL
```
