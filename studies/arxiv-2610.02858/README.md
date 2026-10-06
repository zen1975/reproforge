# Study: arXiv 2610.02858

**Paper:** Harness-Aware Distillation for Small Language Model Agents  
**arXiv:** https://arxiv.org/abs/2610.02858  
**Lifecycle:** PROTOCOL_VERIFIED  
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

## What is not yet reproduced

No student has yet been trained by this ReproForge study. In particular:

- no 0.6B / 1.7B student paper result has been reproduced;
- no 8B or 30B-A3B teacher has been run;
- ALFWorld / WebShop / ScienceWorld benchmark results are not reproduced;
- harness-utilization results are not reproduced;
- teacher-with/without-harness query statistics are not reproduced;
- the paper-reported performance gains remain paper claims.

## Next step

The next free/lightweight step is a small Qwen training analogue using a frozen synthetic harness dataset.

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
