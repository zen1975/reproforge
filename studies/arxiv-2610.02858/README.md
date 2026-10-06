# Study: arXiv 2610.02858

**Paper:** Harness-Aware Distillation for Small Language Model Agents  
**arXiv:** https://arxiv.org/abs/2610.02858  
**Lifecycle:** HEAVY_COMPUTE_READY  
**Reproduction:** PARTIAL

## Why this matters

This study is the highest-priority ReproForge small-model track because it separates what should remain in the external harness from what the student model should actually learn.

The reusable capability hypothesis is:

`training.harness-aware-action-distillation`

The central idea is to query the same teacher at the same student-visited state twice:

1. with harness information;
2. with that harness information stripped.

The harness-conditioned teacher action is treated as preferred, but only if it does not contradict the current harness records. Both actions are then scored under the same student reasoning prefix. This explicitly teaches the small model **how the harness should change its action**, rather than simply copying the teacher's whole response.

## Published protocol extracted

The current ReproForge protocol config records:

- action-only preference scoring;
- reference-free pairwise logistic loss;
- beta = 0.5;
- gradient contribution target rho = 0.5;
- response-distillation + masked preference objective;
- positive-action-only validity check;
- AdamW, weight decay 0.01;
- gradient clipping 1.0;
- learning rate 1e-5;
- cosine schedule with 15 warmup updates;
- effective batch size 60;
- 16 rollout tasks per round;
- two-policy-version staleness;
- rollout temperature 1.0;
- evaluation temperature 0.4;
- 250 updates on ALFWorld;
- 150 updates on WebShop / ScienceWorld.

For OPD-style token distributions, the paper uses the teacher's top 64 tokens at each position with renormalization.

## Conservative validity contract

The paper's practical checker rejects a positive teacher action when it:

- is not among the harness-listed admissible actions;
- uses an object the agent does not hold;
- repeats an action already reported to have had no effect at the same state.

The negative action is not filtered. A rejected preference pair is removed only from the preference term; response distillation remains active for that record.

## ReproForge verification

The independent synthetic protocol test currently passes **10 / 10** checks:

- harness-induced teacher action difference creates an active preference pair;
- identical actions contribute zero preference gradient;
- unavailable positive action is filtered;
- unheld-object positive action is filtered;
- repeated-no-effect positive action is filtered;
- action-only length-normalized log-probability margin;
- reference-free pairwise logistic loss;
- beta = 0.5 semantics;
- rho = 0.5 gradient balancing;
- zero preference gradient produces lambda = 0.

This verifies the published mechanism shape only.

## Qwen2.5-0.5B real training smoke

A real `Qwen/Qwen2.5-0.5B-Instruct` LoRA path was executed on CPU with the HAD action-only preference term.

The six-step v2 run exercises five valid preference examples and one invalid positive-action example.

At the invalid example:

- preference loss = 0
- preference gradient norm = 0
- lambda = 0
- response-distillation loss remains active

This verifies the paper's intended separation between response distillation and preference filtering in an actual trainable small language model path.

Frozen four-example held-out result:

```text
                    accuracy    mean-margin change
distill-only        75%         -0.002632
HAD                 75%         +0.003469
```

The difference is too small and the set too small for an efficacy claim. It is preserved as path evidence only.
## What is not yet reproduced

No student has yet been trained by this ReproForge study. In particular:

- no 0.6B / 1.7B student paper result has been reproduced;
- no 8B or 30B-A3B teacher has been run;
- ALFWorld / WebShop / ScienceWorld benchmark results are not reproduced;
- harness-utilization results are not reproduced;
- teacher-with/without-harness query statistics are not reproduced;
- the paper-reported performance gains remain paper claims.

## Next step

The free/lightweight phase is complete. The next step belongs on local compute: build the on-policy student-state → paired teacher query → validity mask → HAD update loop. See `HANDOFF.md`.

Compare:

```text
response distillation only
vs
response distillation + HAD preference
```

using the same small student and frozen held-out harness states.

The purpose is not to reproduce ALFWorld. It is to answer a narrower question:

> Can a ~0.5B student learn to change its action specifically when harness information changes the preferred decision?

If this path works, preserve the training/evaluation harness and hand off the larger 0.6B–1.7B / benchmark-scale runs to local compute.

## End-to-end lightweight HAD loop

The free/lightweight track now goes beyond fixed synthetic pairs.

### Real same-teacher contrast

A `Qwen2.5-0.5B-Instruct` student acted on harness-dependent states. The same `Qwen2.5-1.5B-Instruct` teacher was then scored twice at each state: with harness-only records and without them.

On the first simple environment, the teacher action changed on 0 / 3 states. This is preserved as negative evidence: redundant harness information produces no HAD preference signal.

On the second harness-dependent set, the teacher action changed on 2 / 4 states, and both changes were valid:

```text
API failure:
student / no-harness teacher   retry primary API
with-harness teacher           use cached backup

Missing approval:
student / no-harness teacher   send invoice
with-harness teacher           request approval
```

Thus the harness corrected the small student's action on 2 / 4 states without using task rewards, success labels, or future information.

### Train the 0.5B student from those real teacher-generated pairs

The two active valid pairs above were used as the only training pairs for a new 3-seed comparison on four unseen harness-dependent states.

All six runs completed:

```text
                     held-out accuracy   mean margin change
distill-only seed101       50%             +0.024662
distill-only seed202       50%             +0.023120
distill-only seed303       50%             +0.022994

HAD seed101                50%             +0.027695
HAD seed202                50%             +0.026290
HAD seed303                50%             +0.026688
```

Aggregate unseen-state margin shift:

```text
distill-only mean   +0.023592
HAD mean            +0.026891
HAD - distill       +0.003299
HAD > distill       3 / 3 seeds
```

Accuracy did not improve, so this is **not** evidence of task-performance superiority. It is consistent directional evidence that the HAD action-preference term changes the small model in the intended direction on unseen harness-dependent analogues.
