# Task-Tool Relevance Classifier

Status: `experimental`  
Paper reproduction status: `PARTIAL`

This capability represents the provider-neutral system idea extracted from arXiv:2610.03213: evaluate each candidate tool independently against the assigned task and emit a relevance signal before execution.

The included Python implementation is a deterministic lexical reference baseline only. It is intentionally not described as the paper's SLM method and does not reproduce the reported GEPA, SFT, or GRPO experiments.

## Independent hard synthetic benchmark

ReproForge now includes a 32-case candidate-level benchmark with positive, wrong-tool, paraphrase, and lexical-overlap hard-negative examples.

Measured result for `lexical-overlap-reference-v1`:

- accuracy: 50.0%
- precision: 47.83%
- recall: 73.33%
- F1: 57.89%
- false-positive rate: 70.59%
- false-negative rate: 26.67%

The paper defines an operational target of 95% accuracy and 95% F1. The lexical baseline fails that target by a wide margin. That is useful evidence: keyword overlap is not sufficient for intent-aware tool-call oversight.

This benchmark is independent synthetic mechanism evidence, not the paper's held-out server-disjoint dataset. The paper's Gemma 3 Base → GEPA → SFT → GRPO results remain unreproduced.

## Contract

Input:
- `task`
- `tool_name`
- `tool_description`

Output:
- `relevance_score`
- `relevant`
- `method`

## Promotion gate

Promotion to `verified` requires a semantic-model implementation, protocol-equivalent server-disjoint data, comparison against the paper's accuracy/F1/E2E metrics, and preserved machine-checkable evidence.
