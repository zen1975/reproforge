# Capability Agent Guide — agent.faop-workflow-static-verifier

## Capability

- ID: `agent.faop-workflow-static-verifier`
- Status: `experimental`
- Source studies: `studies/arxiv-2610.22061`

Read `capability.yaml` and `studies/arxiv-2610.22061/AGENTS.md` before changing behavior.

## Lightweight verification

Keep `verifier.py:verify_registry` deterministic and dependency-free; `tests/test_faop_static_verifier.py` is the contract smoke path.

## Local/heavy verification

None is currently applicable. Any corpus-scale evaluation belongs in the supporting study; link its evidence back into `capability.yaml`.

## Real implementation

Preserve a provider-neutral core. Put workflow-format parsers and runtime/tool enforcement behind adapters. The verifier checks declarations only; do not advertise runtime side-effect guarantees.
