# arXiv:2610.10062 — Continuation Handoff

## State
MECHANISM_VERIFIED / PARTIAL. Free/light incomplete; handoff.ready=false.

## Completed
- Primary arXiv ID/title/submission and 8-page PDF reviewed.
- Author code MIT license verified; paper reuse rights not presumed.
- Independent 5-condition fault injector and three scripted policies.
- Local run: 15 synthetic trials, 12 faults fired, 9/9 loud detections, 1/3 quiet detections, 12/15 clean-state recoveries.
- 4/4 local pytest checks passed.
- Frozen `fault-synthetic-v1` (never tune this fixture).

## Not reproduced
- 24 BFCL multi-turn tasks, 1,920 trials, six real models, matched reasoning/instruct pairs;
- blinded detection judge/human agreement; task-clustered GEE and bootstrap;
- real replanning and post-fault repetition rates; clean-run stochasticity.
The synthetic results are properties of scripted policies, not estimates of model behavior.

## Next steps
1. Confirm legal rights for BFCL tasks and author data before downloading or redistributing.
2. Independently reconstruct paper's multi-turn 15-call cap, eligible fault timing and paired clean baseline.
3. Add model-neutral trajectory logger and evaluator for detection/replanning/recovery/repetition, with a fresh unseen split.
4. Execute a lightweight real-model analogue if authorized; preserve raw trajectories and negative outcomes.
5. Run `python studies/arxiv-2610.10062/experiments/run_fault_injection_synthetic.py`, `pytest tests/test_tool_fault_audit.py`, `reproforge validate-all-statuses`, and `make verify`.
6. Promote only after protocol/evidence/CI gates. Do not mark HEAVY_COMPUTE_READY while CPU/lightweight protocol work remains.

## Prerequisites and secrets
Current synthetic run needs no secrets. Future model access may require provider-specific API keys, names to be declared before use, never values.

## Expected outputs
- new `experiments/*` scripts and frozen versioned `evidence/*.result.json`;
- claim-level Evidence JSON, raw logs, pinned model/dataset revisions, CI URL/run ID.

## Known unknowns
Exact model-provider revisions and immutable BFCL task dataset rights; no values are invented.

## Promotion
PROTOCOL_VERIFIED: executable multi-turn evaluator + bounded protocol evidence.
HEAVY_COMPUTE_READY: all free/light work complete, negative cases preserved, CI green and handoff.ready=true.
REPRODUCED: paper-level acceptance criteria independently executed.
