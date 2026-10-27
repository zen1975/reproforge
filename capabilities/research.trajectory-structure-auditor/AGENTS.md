# Capability Agent Guide — research.trajectory-structure-auditor

## Capability

- ID: `research.trajectory-structure-auditor`
- Status: `experimental`
- Source studies: `studies/arxiv-2610.13152`

Read `capability.yaml` and `studies/arxiv-2610.13152/AGENTS.md` before changing behavior.

## Lightweight verification

Keep the deterministic feature path (`run_structural_audit.py:features`) and `tests/test_trajectory_structure_audit.py` as the contract smoke path. Frozen synthetic fixtures must not be tuned.

## Local/heavy verification

Corpus ranking, SFT and benchmark evaluation belong in the supporting study, not here. Link resulting evidence back into `capability.yaml`.

## Real implementation

The implementation still lives in the study's `experiments/`; move it into this directory behind a stable contract before any operational use. Preserve a provider-neutral core. Do not claim full TQS, paper-level reproduction or performance transfer.
