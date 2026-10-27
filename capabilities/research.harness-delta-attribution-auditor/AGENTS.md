# Capability Agent Guide — research.harness-delta-attribution-auditor

## Capability

- ID: `research.harness-delta-attribution-auditor`
- Status: `experimental`
- Source studies: `studies/arxiv-2610.22466`

Read `capability.yaml` and `studies/arxiv-2610.22466/AGENTS.md` before changing behavior.

## Lightweight verification

Keep `attribution.py:attribute_gains` deterministic; `tests/test_hda_attribution.py` is the contract smoke path.

## Local/heavy verification

Benchmark-scale harness evolution runs belong in the supporting study, not here. Link resulting evidence back into `capability.yaml`.

## Real implementation

Preserve a provider-neutral core that consumes score vectors. Benchmark runners and model providers are adapters. Do not strengthen the contract beyond attribution arithmetic on supplied scores.
