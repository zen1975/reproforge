# Capability Agent Guide — Evidence-Aware Stopping Gate

- Status: experimental
- Source study: `studies/arxiv-2610.06191`

## Contract
The gate converts a stream of USEFUL/USELESS judgments into explicit stopping state. It does not itself decide semantic usefulness.

## Lightweight checks
Test consecutive-useless counter, reset behavior, exact threshold transition, repeated calls after forced stop, and invalid judgment handling.

## Heavy/local work
Trajectory regeneration and model usefulness judges belong in the source study.

## Real implementation
Expose current counter, threshold, force-answer flag, and reason. Do not let provider/model adapters mutate the deterministic transition rules.
