# arXiv:2610.06354 — Continuation Handoff

## State

- Lifecycle: `HEAVY_COMPUTE_READY`
- Reproduction verdict: `PARTIAL`
- Free/lightweight phase: complete
- Frozen evaluations: `graphdecide-mechanism-v1`, `graphdecide-rq2-synthetic-v1`, `graphdecide-rq2-qwen0.5b-analogue-v1`, `graphdecide-rq2-qwen0.5b-analogue-v2`

## Completed lightweight verification

ReproForge independently verifies:

1. evaluator-owned candidate identities and reference truth;
2. all six RQ1 structural task contracts;
3. invalid vs unsupported handling;
4. RQ3 model-induced sequential state and completion/quality separation;
5. RQ2 matched T/G/TG/BAG/A condition construction;
6. identical item/query/candidate identity across matched conditions;
7. held-out truth exclusion from model input;
8. BAG removes explicit edges;
9. anchor-only condition removes entity text/edges;
10. native selection, constrained generation and candidate scoring map back to the same candidate contract;
11. paired accuracy differences;
12. paper-declared 1,000-resample paired target bootstrap with seed `20261001` and endpoints 24/974.
13. real Qwen2.5-0.5B-Instruct revision `7ae557604adf67be50417f59c2c2f167def9a775` executed across T/G/TG/BAG/A on four independent matched items;
14. model output validity was 1.0, but it selected `c0` for every decision: all condition accuracies = 0.5, TG-BAG = 0 pp, G-A = 0 pp.

## Not reproduced

- public ogbn-arxiv / STaRK-Prime model results;
- fourteen paper model-interface configurations;
- paper-level paired deltas;
- public RQ3 optimization results.

The synthetic paired differences are protocol diagnostics only. The 0.5B model-backed result is deliberately preserved as negative evidence: a model can satisfy the candidate contract while failing to use the graph evidence at all.

## Licensing boundary

The author repository currently has no declared repository license. Do not copy, vendor or redistribute author code/assets unless that changes and is independently verified.

## Next local/heavy work

The next meaningful step is a legal public-data slice with a paper-relevant supported model/readout mode; do not tune the frozen 0.5B fixture to manufacture a graph effect.

Preserve:
- exact dataset/split;
- candidate construction;
- model/revision;
- native/generation/scoring mode;
- inference settings;
- raw outputs;
- invalid/unsupported counts;
- accuracy and paired contrasts;
- bootstrap configuration and results.

## Real implementation direction

Keep graph state, relations, provenance, legal candidates, reference objectives and state transitions outside the learned model.

Small LLMs, GNNs, classifiers and scoring models are replaceable decision layers behind the same evaluator-owned contract.

## Promotion

Do not promote to `REPRODUCED` until public-data/model execution tests the paper-level claims. The current state justifies `HEAVY_COMPUTE_READY`, not benchmark reproduction.
