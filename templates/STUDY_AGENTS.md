# Study Agent Guide

Replace bracketed fields when creating a new study.

## Current state
- Study: `[study-id]`
- Lifecycle: `[lifecycle]`
- Reproduction: `[verdict]`
- Free/light phase complete: `[true|false]`

Read first:
1. `status.yaml`
2. `HANDOFF.md`
3. `manifest.yaml`
4. `claims.yaml` when present
5. existing evidence

## Lightweight lane
State exactly what remains possible on CPU/free infrastructure. If lightweight work remains, finish it before requesting heavy compute.

## Local/heavy lane
State recommended model/hardware class, exact next experiment, prerequisites, expected outputs, evaluation split/version and artifact/checkpoint footprint when known.

Do not invent missing paper parameters.

## Real implementation lane
State which reusable capability this study can support and which guarantees are currently justified.

## Frozen / no-tune
Copy frozen evaluations from `status.yaml` and treat them as immutable observations.

## Completion rule
Update `status.yaml`, `HANDOFF.md`, evidence, capability links and tests together when the boundary changes.
