# Agent Guide — arXiv:2610.22061

## Current state

- Study: `arxiv-2610.22061` (FAOPs: Normal Forms and an Algebra for AI Agent Workflows)
- Lifecycle: `MECHANISM_VERIFIED`
- Reproduction: `PARTIAL`
- Free/light phase complete: `false`
- Frozen: `faop-static-verifier-synthetic-v2`

Read `status.yaml`, `HANDOFF.md`, `manifest.yaml` and the frozen evidence first.

## Lightweight lane

Lightweight work remains and must be finished before any heavy promotion. `HANDOFF.md` lists it: declared-type checks, call-frame isolation, output guarantees, one semantics-preserving rewrite on a new frozen fixture, malformed/adversarial scope tests. All of it is deterministic CPU work.

## Local/heavy lane

None is currently required. The paper is theory-first and defers its empirical study, so there is no paper benchmark to scale. Only revisit if the authors publish a corpus or executor.

## Real implementation lane

Supports `capabilities/agent.faop-workflow-static-verifier`. Justified guarantees: deterministic checking of declared atomicity, dataflow, call acyclicity, tool scope and loop/time/cost declarations on the bounded IR. Not justified: runtime side-effect enforcement or equivalence with the paper's full formalism.

## Frozen / no-tune

`faop-static-verifier-synthetic-v2` (`fixtures/faop_static_v2.json`) is immutable. Changed fixtures or acceptance rules require a new evaluation id.

## Completion rule

Update `status.yaml`, `HANDOFF.md`, evidence, capability links and tests together when the boundary changes.
