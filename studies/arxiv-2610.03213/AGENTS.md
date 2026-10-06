# Agent Guide — arXiv:2610.03213

## State
- Lifecycle: `HEAVY_COMPUTE_READY`
- Reproduction: `PARTIAL`
- Free/light phase: complete
- Capability: `agent.task-tool-relevance-classifier`

## Already verified
Free/light work includes lexical/generic semantic baselines, task-specific MiniLM SFT, frozen blind-family evaluation, local classifier runtime, Qwen2.5-0.5B progression, paper-sized SFT data preparation, GRPO component decomposition, generic LoRA SFT harness smoke and Gemma access preflight.

Do not retune against frozen translate/database or blind-family results.

## Local/heavy next step
1. obtain authorized Gemma access;
2. pin the accessible model revision;
3. run the prepared Gemma 3 1B base path;
4. run paper-aligned LoRA SFT locally;
5. only after SFT evidence is stable, attempt larger GRPO/on-policy work.

Do not invent unpublished reward weights, mixture ratios, seeds, GEPA prompt or fixed vLLM decoding.

Track GPU/VRAM, model revision, train/val hashes, parse failures, accuracy/precision/recall/F1/FPR/FNR, bootstrap intervals and exact checkpoint chosen.

## Real implementation direction
Target a pre-execution task→tool relevance gate.

Production constraints:
- candidate-level classification;
- provider-neutral input contract;
- calibrated threshold;
- fail closed or defer on parser/model uncertainty;
- keep tool execution outside the classifier;
- adapters must not change classifier semantics.

Do not silently substitute a generic semantic model for a task-specific classifier.
