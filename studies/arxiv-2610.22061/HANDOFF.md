# Continuation handoff — arXiv:2610.22061

## Current state

- Lifecycle: MECHANISM_VERIFIED
- Reproduction status: PARTIAL
- Free/light phase complete: false
- Handoff ready: false

This handoff is intentionally not ready for a heavy-compute promotion. Lightweight protocol work remains.

## Completed

- arXiv identity, 28-page PDF, and CC BY 4.0 paper license verified;
- the paper's four normal forms and optional termination/bounds contracts extracted;
- independent bounded static verifier implemented;
- frozen synthetic mechanism suite run (14/14 expected outcomes);
- result and Evidence JSON saved;
- capability contract registered as experimental in the proposed branch.

## Frozen evaluation

- Evaluation id: faop-static-verifier-synthetic-v2
- Fixture: studies/arxiv-2610.22061/fixtures/faop_static_v2.json
- Result: studies/arxiv-2610.22061/evidence/faop_static_verifier_v2.result.json
- Evidence: studies/arxiv-2610.22061/evidence/faop_static_verifier_v2.evidence.json

Do not change this fixture or tune expected codes against it. Create a new evaluation version for any further changes.

## Next lightweight work

1. Add explicit declared-type checks and a field-type environment.
2. Model procedure call frames so callee locals do not leak and only declared outputs return.
3. Check declared procedure outputs are guaranteed by every path.
4. Add one rewrite transformation and compare deterministic before/after traces on a new frozen fixture.
5. Add malformed-input and adversarial scope tests.
6. Run make verify on the full repository and ensure GitHub Actions is green before advancing lifecycle.

## Commands

    python studies/arxiv-2610.22061/experiments/run_static_verifier.py
    python -m pytest -q tests/test_faop_static_verifier.py
    reproforge validate studies/arxiv-2610.22061/manifest.yaml
    reproforge validate-candidates candidates/queue.yaml
    reproforge study-status studies/arxiv-2610.22061
    make verify

## External prerequisites and secrets

No API keys, secrets, model weights, external datasets, or author code are required for the current mechanism tests. No secret names are required for the next declared lightweight steps.

## Known unknowns

- The paper body does not link the author SkillBase compiler/executor source.
- The paper does not report a full empirical evaluation or a public benchmark with measured acceptance criteria.
- The implementation checks declarations; it does not inspect real external side effects or enforce permissions at runtime.
- The supported IR is intentionally smaller than the paper's complete formalism.

## Promotion conditions

Do not advance to PROTOCOL_VERIFIED until the type/call-frame/output guarantees and rewrite-preservation tests are implemented. Do not advance to HEAVY_COMPUTE_READY while any practical lightweight validation remains.
