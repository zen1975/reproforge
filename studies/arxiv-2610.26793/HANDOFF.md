# Continuation Handoff — arXiv 2610.26793

Lifecycle: PROTOCOL_VERIFIED. Reproduction: PARTIAL. Capability registry registration remains incomplete.

## Completed
- Verified arXiv metadata and reviewed the full HTML protocol and license.
- Implemented the independent log-odds controller and threshold-selection rule.
- Prepared a deterministic synthetic fixture, benchmark runner, and Evidence JSON.
- Added tests for reminder-first behavior, recovery reset, calibration, and evidence consistency.

## Not reproduced
No hosted monitor API call, 8B model trajectory, or paper benchmark result was generated. Paper-reported accuracy, token, and abstention results remain unverified.

## Frozen evaluations
soma-synthetic-calibration-v1; soma-synthetic-test-v1; soma-synthetic-mechanism-v1. Do not retune these inputs after observing results.

## External prerequisites
Authorized Jev API access; exact S2 model revisions from actual metadata; legal access to each benchmark and scoring dependency; disjoint calibration/test splits. Record only secret names in deployment documentation, never values in this repository.

## Next commands
python studies/arxiv-2610.26793/experiments/run_soma_synthetic.py  
pytest tests/test_soma_controller.py -q  
reproforge validate-candidates candidates/queue.yaml  
reproforge study-status studies/arxiv-2610.26793  
reproforge validate-all-statuses

## Known unknowns and promotion
Model revisions, hosted monitor serving revision/cost, and dataset-specific licenses remain unknown. Keep the capability experimental and reproduction PARTIAL until registry registration, CI, authorized model-backed evaluation, disjoint splits, matched baselines, and machine-checkable paper-level evidence are complete. Synthetic PASS is not paper reproduction.
