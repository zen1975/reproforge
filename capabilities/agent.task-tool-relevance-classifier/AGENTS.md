# Capability Agent Guide — Task-Tool Relevance Classifier

- Status: experimental
- Source study: `studies/arxiv-2610.03213`

## Contract
Given one task and one candidate tool name/description, return relevance score/decision/method. Do not execute the tool.

## Lightweight checks
Preserve deterministic lexical fallback, parser/structured-output checks, frozen benchmark-family boundaries, and threshold provenance.

## Heavy/local work
Model training and paper-scale SFT/GRPO belong in the source study. Link accepted Evidence back into `capability.yaml`.

## Real implementation
Operational priority is safe tool mediation:
- score before execution;
- defer/fail closed on invalid model output;
- keep calibration explicit;
- separate provider adapters from classifier semantics.

Do not silently substitute a generic semantic model for a task-specific classifier.
