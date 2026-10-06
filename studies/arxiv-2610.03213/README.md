# Study: arXiv 2610.03213

**Paper:** Toward SLM-based agentic task-tool intent matching  
**arXiv:** https://arxiv.org/abs/2610.03213  
**Intake:** VERIFIED against authoritative arXiv metadata and full PDF  
**Reproduction:** PARTIAL

## Verified paper protocol

The paper formulates task-tool relevance as candidate-level binary classification: input is the task plus a candidate tool name and description; output is a structured relevance decision. It builds cross-MCP tasks with two or three required tools, one per represented server.

The full paper reports:

- 352 tools across 12 MCP servers;
- server-disjoint validation/test pools;
- Gemma 3 1B and 4B;
- sequential specialization: Base → GEPA → SFT → GRPO;
- a 95% operational target for accuracy and F1;
- held-out metrics including E2E accuracy, accuracy, precision, recall, F1, FPR, FNR, parse failures, and bootstrap confidence intervals.

## ReproForge evidence

ReproForge independently implements a transparent lexical reference classifier and now runs it on a 32-case hard synthetic candidate-level benchmark containing positive examples, wrong-tool negatives, semantic paraphrases, and lexical-overlap hard negatives.

Measured lexical baseline:

- accuracy: 50.0%
- precision: 47.83%
- recall: 73.33%
- F1: 57.89%
- FPR: 70.59%
- FNR: 26.67%

This does **not** reproduce the paper's SLM results. It establishes a reproducible reference floor and demonstrates that lexical matching alone is inadequate for the paper's 95% operational target.

ReproForge then evaluated a generic off-the-shelf MiniLM CrossEncoder and found that generic semantic relevance alone was also insufficient. A task-specific supervised specialization experiment on deterministic family-disjoint data improved the first held-out test from 80.56% accuracy / 69.57% F1 to 91.67% / 85.71%.

Because that first test had already been observed, ReproForge then froze an entirely new four-family blind benchmark before evaluation. On 144 unseen-family examples, the same recipe improved 85.42% accuracy / 78.79% F1 to 94.44% / 91.30%. The paired improvement was 13 corrected cases versus 0 regressions (exact McNemar p=0.000244), and the 95% bootstrap interval for accuracy was 90.28%–97.92%. This materially strengthens the specialization finding while still falling short of the paper's joint 95% accuracy/F1 target.

## Protocol-equivalent SLM progression

To move closer to the paper's actual model class and server-disjoint protocol without using unavailable author artifacts, ReproForge independently generated a 2,400-row protocol-equivalent synthetic dataset:

- 12 MCP-style servers;
- 8 train servers / 4 completely held-out test servers;
- N=2 and N=3 cross-server tasks;
- one grounding tool per represented server;
- candidate-level correct, wrong-same-server, and null-outside-task-server labels.

Using `Qwen/Qwen2.5-0.5B-Instruct` (Apache-2.0) only as an ungated SLM proxy, not as a Gemma substitute:

| Stage | Accuracy | F1 | Parse failures |
| --- | ---: | ---: | ---: |
| Initial Base prompt | 31.25% | 47.62% | 64/160 |
| Fixed-candidate prompt optimization analogue | 80.00% | 76.12% | 0/160 |
| LoRA SFT analogue v1 | 95.00% | 92.86% | 0/80 |

The prompt stage selected among three predeclared prompts using only train-pool dev rows; it is not GEPA. The LoRA stage updated 270,336 parameters on 96 train-pool examples. Its 80-row held-out slice is now frozen and will not be used for further tuning.

An SFT v2 protocol was committed before evaluation: identical model revision, prompt, LoRA hyperparameters, learning rate, and seed; only training examples increase from 96 to 192, and evaluation moves to untouched held-out rows 160–399.

## Paper-aligned SFT/GRPO reproduction harness

The paper's published optimization settings are now captured in `experiments/paper_protocol_config_v1.json` and guarded by tests.

For SFT, the paper specifies LoRA `r=32`, `alpha=64`, AdamW, peak learning rate `1.9e-4`, 10% warmup, 3 epochs, effective batch size 64, max sequence length 1024, bf16, response-only cross-entropy, 4,404 balanced training examples and 1,136 validation examples.

ReproForge can now independently prepare exactly 4,404 / 1,136 class-balanced protocol-shaped rows with the same structured `{"reasoning": ..., "appropriate": bool}` target. This is a shape/protocol reproduction only: the paper used ASTRA single-tool examples and the exact seed/GEPA prompt is not published.

The generic LoRA SFT harness was executed with a public Apache-2.0 135M surrogate to validate the training mechanics. With `r=32`, `alpha=64`, response-only prompt masking and the paper's peak learning rate, a 2-step CPU smoke run reduced loss from 3.0556 to 2.4013. This validates the code path, not the paper result.

For GRPO, ReproForge exposes the deterministic reward components stated in the paper—schema compliance, label correctness, excessive-reasoning penalty and invalid-output flag—but deliberately does not combine them into a scalar because the paper does not publish the weights. The same rule applies to the unpublished mixture ratios across single-tool, same-MCP and cross-MCP training examples.

### Current hard blockers

- Official `google/gemma-3-1b-it` access requires accepted Gemma terms and an authenticated HF token; the Actions preflight currently records `BLOCKED_MODEL_ACCESS`.
- The paper used a single H100 GPU for optimization; the current GitHub runner is CPU-only.
- The paper-linked author repository currently returns 404 through both the connected GitHub API and public search, so author data/code cannot yet be inspected.
- Exact seed prompt text, vLLM decoding settings, GRPO scalar reward weights and GRPO mixture ratios are not published in the paper and remain unknown.

## Exact Gemma gate

An authenticated Gemma 3 1B workflow is ready, but it fails closed without `HF_TOKEN` and prior acceptance of Google's Gemma license. Qwen/MiniLM evidence is never labeled as Gemma evidence.

The paper-linked author repository currently returns 404 through the available GitHub access path, so author code/data remain unavailable and their licenses remain UNKNOWN. No author code, dataset, or weights are redistributed.

## Correction record

The original intake accidentally mapped this arXiv ID to an unrelated paper because of mixed search aggregation. That mapping was removed. The study is now verified directly from arXiv and the full PDF.

## Boundary

No paper PDF, figures, author dataset, author code, prompts, checkpoints, or weights are redistributed. The paper-linked code/data repository was not available through the current GitHub access path during this verification session, so ReproForge does not depend on it.

## Candidate capability

`agent.task-tool-relevance-classifier`

Status remains `experimental`. Reproduction is `PARTIAL` because only the interface/mechanism and an independent baseline have been implemented and measured.

## Next gate

The next meaningful step is protocol-equivalent server-disjoint data at larger scale, then a closer reproduction of the paper's Gemma 3 Base → GEPA → SFT → GRPO progression. The current specialized MiniLM experiment is useful mechanism evidence but must not be treated as a reproduction of the paper's reported model results.
