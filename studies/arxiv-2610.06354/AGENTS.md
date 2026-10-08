# Agent Guide — arXiv:2610.06354

## State
- Lifecycle: `HEAVY_COMPUTE_READY`
- Reproduction: `PARTIAL`
- Free/light phase: complete
- Working label: `GraphDecide`
- Frozen: `graphdecide-mechanism-v1`, `graphdecide-rq2-synthetic-v1`

Read `status.yaml` and `HANDOFF.md` first.

## Verified boundary

Lightweight verification covers RQ1/RQ3 mechanism contracts and the RQ2 matched-condition / paired-bootstrap protocol.

Verified readout modes:
- native selection;
- constrained generation;
- candidate scoring.

Evaluator truth, candidate identity, relation provenance and state transitions remain outside the model.

The author repository has no declared repository license. Do not copy or redistribute it.

## Local/heavy next step

Run one pinned model/readout on one legal public-data slice first. Do not start broad model sweeps.

Record dataset/split, model/revision, readout mode, inference settings, raw outputs, invalid/unsupported outcomes, paired metrics and bootstrap results.

Do not tune against either frozen synthetic fixture.

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
