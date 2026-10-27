# Agent Guide — arXiv:2610.13152

## Current state

- Study: `arxiv-2610.13152` (TQS trajectory quality / structural components)
- Lifecycle: `MECHANISM_VERIFIED`
- Reproduction: `PARTIAL`
- Free/light phase complete: `false`
- Frozen: `tqs-structural-components-synthetic-v1`

Read `manifest.yaml`, `status.yaml`, `HANDOFF.md` and `report.md` first.

## Lightweight lane

Lightweight work remains: implement the remaining published TQS components (IAC, PSN, DPI) and source-aligned parsers, run paired failure/success and ranking baselines on a licensed public corpus slice, and add a new unseen frozen evaluation. All of this is CPU work. Keep unknown IAC/PSN/DPI details explicitly unknown.

## Local/heavy lane

Paper-level claims need lawful CoderForge-Preview access, Qwen3-Coder-30B-A3B-scale SFT compute and SWE-Bench Verified evaluation. Do not start before the lightweight lane is exhausted.

Do not invent missing paper parameters.

## Real implementation lane

Supports `capabilities/research.trajectory-structure-auditor`. Justified guarantees: deterministic OEC/TTE/SCP/PED features on supplied step traces. Not justified: full weighted TQS, data-curation benefit or performance transfer.

## Frozen / no-tune

`tqs-structural-components-synthetic-v1` is immutable. Do not tune on the two observed traces; create new unseen fixtures under a new version. The author repository is MIT-licensed but is not used; no author assets are copied.

## Completion rule

Update `status.yaml`, `HANDOFF.md`, evidence, capability links and tests together when the boundary changes.
