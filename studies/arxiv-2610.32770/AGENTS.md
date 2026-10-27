# Agent Guide — arXiv:2610.32770

## Current state

- Study: `arxiv-2610.32770` (On-Policy Self-Training, OPST)
- Lifecycle / reproduction: see `status.yaml` (authoritative)
- Frozen: `opst-objective-semantics-v1`, `opst-sample-selection-v1`, `opst-ema-loss-semantics-v1`

Read `status.yaml`, `HANDOFF.md`, `manifest.yaml`, `source_metadata.yaml` and `report.md` first.

## Lightweight lane

Done: deterministic objective, sample-selection, EMA and loss-aggregation checks (standard library only, run in CI via `tests/test_opst_mechanism.py`).

Remaining lightweight work is a small-model analogue on GitHub Actions CPU (e.g. Qwen2.5-0.5B-Instruct), pre-registered under a new evaluation id before it runs. `HANDOFF.md` lists the candidate designs and every value that must be labeled a ReproForge choice.

## Local/heavy lane

Paper-level claims (C5) need Gemma 4 E2B/E4B (gated) or Qwen3-4B-Base, 7 rounds x 285 samples with on-policy rollouts and an EMA teacher, then lm-evaluation-harness scoring on MMLU/GPQA/GSM8K/HellaSwag and OOD ARC-Challenge/MATH-500/Winogrande. This is outside the GitHub-only scope of this repository's daily workflow.

Do not invent missing paper parameters (lr, optimizer, batch, steps, G, T_gen, LoRA vs full, topic lists). The TeX source has commented-out hyperparameter lines; they are not published values and must not be used.

## Real implementation lane

Candidate capability: `training.privileged-self-distillation-gate` (not yet promoted). Justified so far: the GKD-consistent bounded objective, the dedupe -> pseudo-verification -> consensus-gate decision rule, and EMA-teacher bookkeeping. Not justified: any self-improvement or robustness claim.

## Objective form

Use `d_alpha_consistent` (GKD-consistent mixture) for any analogue and label it a ReproForge interpretation. The printed Sec. 3.5 mixture does not satisfy the paper's own stated properties (C1); keep `d_alpha_printed` only as the recorded comparison.

## Frozen / no-tune

The three frozen evaluations and `fixtures/opst_selection_v1.json` are immutable. Changed fixtures, probes or criteria need new evaluation ids.

## Completion rule

Update `status.yaml`, `HANDOFF.md`, evidence, the study index in `studies/README.md`, capability links and tests together when the boundary changes.
