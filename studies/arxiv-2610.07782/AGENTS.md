# Agent Guide — arXiv:2610.07782

## State
- Lifecycle: `MECHANISM_VERIFIED`
- Reproduction: `PARTIAL`
- Free/light phase: incomplete
- Frozen: `persistent-memory-ablation-audit-v1`

Read `status.yaml` and `HANDOFF.md` first.

## Verified boundary

The reusable target is an ablation-validity auditor:

```text
C1 component executed
C2 runs independent
C3 only named axis varied + order counterbalanced
C4 effect above replicate measurement floor
+ regime actually allows useful memory recall
```

## Local/heavy next step

After frozen audit execution, move to hardware/benchmark-scale reproduction only if no further free/lightweight verification remains.

## Real implementation direction

A memory feature should not receive credit from an ablation unless:

- the feature executed;
- evaluation state was clean before both arms;
- the arms differed only on that feature;
- run order is not confounded;
- the effect is resolvable above replicate variation;
- the benchmark regime contains genuinely reusable prior state.
