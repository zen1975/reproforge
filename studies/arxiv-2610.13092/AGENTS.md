# Agent Guide — arXiv:2610.13092

## State
- Lifecycle: `HEAVY_COMPUTE_READY`
- Reproduction: `PARTIAL`
- Free/light phase: complete (provisional; see status.yaml `next_step`)
- Frozen: `jev-efficiency-transfer-audit-v1`; `jev-live-systemone-check-v1` (inputs frozen, NOT_RUN: needs `TYPESAFE_API_KEY`)

Read `status.yaml`, `report.md`, and `HANDOFF.md` first.

## Core boundary

Never equate a faster decision with a better agent.

Keep these levels separate:

`decision -> task attempt -> recovery/completion -> delivered success`

For ALFWorld, preserve the B/C/J interpretation:

- B-vs-C: candidate-interface effect;
- C-vs-J: decision-model effect under shared candidate interface;
- B-vs-J: system integration effect.

## License boundary

The paper is CC BY-NC-ND 4.0.

The linked anonymous experimental implementation has no independently verified code license in the accessible source. Do not copy or redistribute it.

## Local/heavy next step

The current local audit can verify accounting semantics and published aggregates. A real Jev/environment rerun belongs to the heavier/external-access continuation because it requires model-service access and benchmark environments.

## Real implementation direction

In production, treat a System One model as one bounded component of a larger state machine.

Externally measure and own:

- candidate construction;
- prerequisites;
- progress state;
- recovery state;
- completion verification;
- attempt-level resources;
- failed-attempt resources;
- cost/time per delivered success.

Do not optimize only the local selector metric.

## Scientific stop rule

Do not claim efficiency transfer when only decision-level cost/latency improves.

A positive transfer claim requires preserved completion and improved task-level or delivered-success resource use under an explicitly defined comparison.
