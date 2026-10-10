# Agent Guide — arXiv:2610.07782

## State
- Lifecycle: `HEAVY_COMPUTE_READY`
- Reproduction: `PARTIAL`
- Free/light phase: complete
- Frozen: `persistent-memory-ablation-audit-v1`

Read `status.yaml` and `HANDOFF.md` first.

## Verified boundary

The frozen audit independently enforces:

```text
C1 claimed component actually executes
C2 no pre-run evaluation contamination
C3 exactly one ablation axis + counterbalanced order
C4 effect exceeds replicate-level measurement floor
C5 benchmark regime contains useful prior state
```

It detects all four injected measurement defects and rejects an independent-item regime where recall is reachable but prior traces are not useful.

## Local/heavy next step

Only move to paper-scale measurement with comparable serving/model geometry, datasets, persistent store and replicate execution.

## Real implementation direction

Never report a memory gain without separate evidence that:

- memory executed;
- evaluation state was clean;
- only memory changed;
- temporal order was controlled;
- the effect is above the reproducibility floor;
- memory had something relevant to remember.
