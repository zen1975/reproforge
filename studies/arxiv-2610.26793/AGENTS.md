# Agent Guide — arXiv:2610.26793

## Current state

- Study: `arxiv-2610.26793` (SOMA metacognitive controller)
- Lifecycle: `PROTOCOL_VERIFIED`
- Reproduction: `PARTIAL`
- Free/light phase complete: `false`
- Capability candidate: `agent.soma-metacognitive-controller` (`capability-candidate.yaml`; not yet in `capabilities/` or the registry)
- Frozen: `soma-synthetic-calibration-v1`, `soma-synthetic-test-v1`, `soma-synthetic-mechanism-v1`

Read `status.yaml`, `HANDOFF.md`, `manifest.yaml`, `protocol.md` and the frozen evidence first.

## Lightweight lane

Remaining lightweight work: promote the capability candidate into `capabilities/` with registry entry and tests, then confirm GitHub Actions is green. No hosted monitor API, reasoning model or paper benchmark is needed for that.

## Local/heavy lane

Paper-level work needs authorized Jev API access, an 8B-class reasoning model with exact revisions taken from real metadata, legally accessible benchmarks with their scoring dependencies, and disjoint calibration/test splits. API keys stay local-only and never enter the repository or Actions secrets.

Do not invent missing paper parameters.

## Real implementation lane

Supports `agent.soma-metacognitive-controller`. Justified guarantees: deterministic log-odds accumulation, calibrated threshold selection, reminder-first intervention and recovery reset on synthetic probability streams. Not justified: any accuracy, token-saving or abstention claim.

## Frozen / no-tune

The three frozen evaluations above are immutable. Changed fixtures or thresholds require new evaluation ids.

## Completion rule

Update `status.yaml`, `HANDOFF.md`, evidence, capability links and tests together when the boundary changes.
