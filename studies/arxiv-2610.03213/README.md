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

ReproForge then evaluated a generic off-the-shelf MiniLM CrossEncoder and found that generic semantic relevance alone was also insufficient. Finally, a task-specific supervised specialization experiment was run on deterministic synthetic data with family-disjoint train/dev/test splits. The held-out-family result improved from 80.56% accuracy / 69.57% F1 before specialization to 91.67% accuracy / 85.71% F1 after specialization, with 100% precision and 0% false-positive rate. This is meaningful evidence that task-specific supervision helps, but it still falls short of the paper's 95% accuracy/F1 target.

## Correction record

The original intake accidentally mapped this arXiv ID to an unrelated paper because of mixed search aggregation. That mapping was removed. The study is now verified directly from arXiv and the full PDF.

## Boundary

No paper PDF, figures, author dataset, author code, prompts, checkpoints, or weights are redistributed. The paper-linked code/data repository was not available through the current GitHub access path during this verification session, so ReproForge does not depend on it.

## Candidate capability

`agent.task-tool-relevance-classifier`

Status remains `experimental`. Reproduction is `PARTIAL` because only the interface/mechanism and an independent baseline have been implemented and measured.

## Next gate

The next meaningful step is protocol-equivalent server-disjoint data at larger scale, then a closer reproduction of the paper's Gemma 3 Base → GEPA → SFT → GRPO progression. The current specialized MiniLM experiment is useful mechanism evidence but must not be treated as a reproduction of the paper's reported model results.
