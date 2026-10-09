# Agent Guide — arXiv:2610.06354

## State
- Lifecycle: `HEAVY_COMPUTE_READY`
- Reproduction: `PARTIAL`
- Free/light phase: complete
- Working label: `GraphDecide`
- Frozen: `graphdecide-mechanism-v1`, `graphdecide-rq2-synthetic-v1`, `graphdecide-rq2-qwen0.5b-analogue-v1`, `graphdecide-rq2-qwen0.5b-analogue-v2`

Read `status.yaml` and `HANDOFF.md` first.

## Verified boundary

Lightweight verification covers RQ1/RQ3 mechanism contracts and the RQ2 matched-condition / paired-bootstrap protocol.

Verified readout modes:
- native selection;
- constrained generation;
- candidate scoring.

Evaluator truth, candidate identity, relation provenance and state transitions remain outside the model.

A real model-backed boundary run has also been executed:

- model: `Qwen/Qwen2.5-0.5B-Instruct`
- resolved revision: `7ae557604adf67be50417f59c2c2f167def9a775`
- matched items: 4
- conditions: T / G / TG / BAG / A
- valid candidate outputs: 20/20
- accuracy: 0.5 in every condition
- TG-BAG: 0 pp
- G-A: 0 pp
- observed behavior: the model emitted `c0` on all 20 decisions

This is negative boundary evidence. A valid decision interface does not imply that a 0.5B model is actually using graph evidence. Do not tune this frozen fixture to manufacture a graph effect.

The author repository has no declared repository license. Do not copy or redistribute it.

## Local/heavy next step

Run one paper-relevant pinned model/readout on one legal public-data slice first. Do not start broad model sweeps.

Record dataset/split, model/revision, readout mode, inference settings, raw outputs, invalid/unsupported outcomes, paired metrics and bootstrap results.

Do not retune against any frozen fixture.

## Real implementation direction

Treat graph/GNN representations as evidence or scoring inputs, never as silent owners of evaluator truth or the legal action space.

Preferred structure:

```text
Graph / Evidence / State / Candidate Set
→ replaceable decision model
→ Candidate ID
→ Validator / Evaluator
→ State transition
```
