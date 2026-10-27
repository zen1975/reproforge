# Agent Guide — arXiv:2610.22466

## Current state

- Study: `arxiv-2610.22466` (Harness-Delta Attribution: Dissecting Gains From Harness Evolution)
- Lifecycle: `MECHANISM_VERIFIED`
- Reproduction: `PARTIAL`
- Free/light phase complete: `false`
- Frozen: `hda-synthetic-v1`

Read `status.yaml`, `HANDOFF.md`, `manifest.yaml`, `design/mechanism-design.md` and the frozen evidence first.

## Lightweight lane

Lightweight work remains: a protocol-equivalent evaluator on an independently licensed small benchmark or trace fixture, with asset license verified first. Score vectors in `hda-synthetic-v1` are declared, not measured.

## Local/heavy lane

Paper-level reproduction needs 11 executor models, three harness-evolution frameworks and four benchmark families, plus task-specific compute-matched and shortcut-neutralized variants with human review. Do not start it before the lightweight evaluator exists.

Do not invent missing paper parameters.

## Real implementation lane

Supports `capabilities/research.harness-delta-attribution-auditor`. Justified guarantees: conservation of the O/T/G decomposition, the significance/positive-gain gate and share caps on supplied score vectors. Not justified: any claim about real harness evolution gains.

## Frozen / no-tune

`hda-synthetic-v1` (`fixtures/hda_synthetic_v1.json`) is immutable. The author repository has no identified license; inspect only, never copy.

## Completion rule

Update `status.yaml`, `HANDOFF.md`, evidence, capability links and tests together when the boundary changes.
