# Task-Tool Relevance Classifier

Status: `experimental`  
Paper reproduction status: `NOT_RUN`

This capability represents the provider-neutral system idea extracted from arXiv:2610.03213: evaluate each candidate tool independently against the assigned task and emit a relevance signal before execution.

The included Python implementation is a deterministic lexical reference baseline only. It is intentionally not described as the paper's SLM method and does not reproduce the reported prompt-optimization, supervised-fine-tuning, or GRPO experiments.

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

Promotion to `verified` requires full-paper protocol extraction, protocol-equivalent evaluation data, an SLM-based implementation, comparison against the paper's metrics, and preserved machine-checkable evidence.
