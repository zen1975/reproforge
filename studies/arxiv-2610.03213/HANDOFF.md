# arXiv:2610.03213 — Continuation Handoff

## State

- Lifecycle: `HEAVY_COMPUTE_READY`
- Reproduction verdict: `PARTIAL`
- Free/lightweight phase: complete

The repository already contains independent mechanism tests, protocol-equivalent data, paper-style metrics, frozen held-out evaluations, a callable model-backed runtime path, paper-sized SFT data preparation, a LoRA response-only training harness, and a Gemma access/evaluation workflow.

## Already executed

- authoritative arXiv intake and full-paper protocol extraction;
- lexical and generic semantic baselines;
- MiniLM task-specific specialization;
- frozen unseen-family blind evaluation with paired statistics;
- protocol-equivalent 12-server / 8-train-pool / 4-held-out-server structure;
- Qwen 0.5B Base/prompt/SFT proxy progression;
- paper-sized SFT preparation: 4,404 balanced train / 1,136 balanced validation rows;
- LoRA harness smoke with published SFT values `r=32`, `alpha=64`, peak LR `1.9e-4`, response-only masking;
- Gemma 3 1B workflow preflight, which currently stops at authenticated model access.

## Not reproduced

- exact Gemma 3 1B Base paper benchmark;
- Gemma 3 1B paper SFT on equivalent author data;
- paper-scale GRPO;
- Gemma 3 4B progression;
- author dataset/code execution;
- exact paper-level final metrics.

## Frozen evaluations — do not tune against

Do not modify training/prompt parameters using results from:

1. `task_tool_specialized_minilm_sft_v1` held-out `translate/database` families;
2. `task-tool-specialized-minilm-blind-v1` blind `commerce/documents/identity/notifications`;
3. Qwen SFT v1 frozen held-out slice;
4. Qwen SFT v2 held-out rows `160–399`.

If further tuning is needed, create a new version and a new unseen evaluation split.

## External prerequisites

### Gemma access

1. Accept the Google Gemma usage terms for `google/gemma-3-1b-it`.
2. Create a Hugging Face read token.
3. For GitHub Actions, add repository secret:
   - name: `HF_TOKEN`
   - value: do not commit it.

### Heavy local training

Recommended: CUDA-capable GPU with enough VRAM for Gemma 3 1B LoRA/bf16 or an equivalent local GPU environment. The paper reports a single H100 for optimization; exact hardware equivalence is not required for an independent reproduction, but differences must be recorded.

## GitHub Base evaluation

After `HF_TOKEN` is configured:

```text
Actions → Gemma 3 1B protocol reproduction → Run workflow
```

Workflow source:

```text
.github/workflows/gemma3-1b-protocol.yml
```

## Local paper-aligned SFT preparation

```bash
python studies/arxiv-2610.03213/experiments/prepare_sft_protocol_data.py
```

Expected generated inputs:

```text
studies/arxiv-2610.03213/experiments/generated/sft_train_4404.jsonl
studies/arxiv-2610.03213/experiments/generated/sft_validation_1136.jsonl
studies/arxiv-2610.03213/experiments/generated/sft_protocol_summary.json
```

## Local Gemma LoRA SFT harness

After authorized Gemma weights are locally accessible, use the generic harness as the implementation entrypoint:

```bash
python studies/arxiv-2610.03213/experiments/run_lora_sft_harness.py \
  --model-id google/gemma-3-1b-it \
  --train-jsonl studies/arxiv-2610.03213/experiments/generated/sft_train_4404.jsonl \
  --epochs 3 \
  --learning-rate 0.00019 \
  --warmup-fraction 0.1 \
  --batch-size 4 \
  --gradient-accumulation 16 \
  --max-length 1024 \
  --lora-r 32 \
  --lora-alpha 64 \
  --dtype bfloat16
```

Record actual hardware, dependency versions, batch/accumulation changes, model revision, and model/checkpoint hashes.

## GRPO boundary

The paper publishes the broad GRPO configuration but not every scalar needed for exact replay. ReproForge intentionally does not invent:

- reward component weights;
- single-tool / same-MCP / cross-MCP mixture ratios;
- exact seed/GEPA prompt text;
- exact fixed vLLM decoding configuration.

`grpo_reward_components.py` exposes only the published reward components. Any independently selected weights must be labeled as an analogue, not exact reproduction.

## Expected continuation evidence

A successful continuation should add new immutable result/evidence files under:

```text
studies/arxiv-2610.03213/evidence/
```

At minimum preserve:

- model ID + immutable revision;
- dataset hash;
- environment/hardware;
- seed;
- exact training configuration;
- raw/derived metrics;
- parse failures;
- Accuracy / Precision / Recall / F1 / FPR / FNR / E2E Accuracy;
- checkpoint hash if a checkpoint is created;
- explicit comparison with the paper target;
- clear boundary if protocol/data/hardware differ.

## Promotion

Do not move the study to `REPRODUCED` merely because Gemma runs.

Promotion requires execution sufficiently close to the declared paper-level acceptance criteria and machine-checkable Evidence. Otherwise keep `HEAVY_COMPUTE_READY` + `PARTIAL`, or create a new independent analogue result.
