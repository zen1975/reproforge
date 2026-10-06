# Studies

Each directory under `studies/` is an independent reproduction study for one paper, method, or research claim set.

Recommended layout:

```text
studies/<study-id>/
├── manifest.yaml
├── status.yaml
├── HANDOFF.md
├── claims.yaml
├── experiments/
├── evidence/
└── report.md
```

`status.yaml` is the machine-readable current state. `HANDOFF.md` is the human continuation contract.

Before changing a study:

```bash
reproforge study-status studies/<study-id>
```

Lifecycle:

```text
INTAKE_VERIFIED
    ↓
MECHANISM_VERIFIED
    ↓
PROTOCOL_VERIFIED
    ↓
HEAVY_COMPUTE_READY
    ↓
REPRODUCED
```

`BLOCKED` may be used when licensing, missing assets/specification, or access prevents defensible continuation.

`HEAVY_COMPUTE_READY` means the free/lightweight phase is complete. It does **not** mean the paper is reproduced. The reproduction verdict may still be `PARTIAL`.

A study must not silently inherit licensing assumptions, datasets, code, weights, or claims from another study. Shared reusable logic belongs in `capabilities/` only after promotion criteria are met.

Do not tune against an evaluation after its result has been observed. Create a new version/split and record the old one under `frozen_evaluations`.

See `docs/STUDY_COMPLETION_POLICY.md`.
