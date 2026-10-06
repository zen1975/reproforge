# Contributing to ReproForge

ReproForge is designed so a fork can continue a study without reconstructing its history from chat logs or private context.

## Start here

```bash
git clone <your-fork>
cd reproforge
python -m venv .venv
source .venv/bin/activate
make bootstrap
make verify
```

Then inspect the study you want to continue:

```bash
reproforge study-status studies/<study-id>
```

Read both:

- `studies/<study-id>/status.yaml`
- `studies/<study-id>/HANDOFF.md`

before changing experiments.

## Study lifecycle

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

Use `BLOCKED` only for a genuine hard blocker such as unavailable licensing, missing specification, inaccessible assets, or another condition that prevents defensible progress.

`HEAVY_COMPUTE_READY` is the standard free/lightweight completion point. It means the study is ready to hand to local/GPU compute. It does not mean the paper is reproduced.

## Before adding a result

1. Define or reuse an acceptance criterion before looking at the result.
2. Keep author-reported numbers separate from reproduced measurements.
3. Record external model/data/code provenance and access/license status.
4. Freeze held-out/blind evaluations after observing them.
5. Never fill unpublished parameters with guessed values.
6. Save machine-checkable Evidence.
7. Update `status.yaml` only after the lifecycle gate is actually met.
8. Update `HANDOFF.md` whenever the next executable step changes.

## Heavy-compute work

When continuing a `HEAVY_COMPUTE_READY` study:

- do not modify frozen evaluation splits;
- record hardware and dependency versions;
- pin model/data revisions where possible;
- preserve seeds and exact configs;
- save checkpoint/data hashes rather than committing large weights by default;
- put secrets only in environment variables / secret stores;
- create a new evidence run rather than editing old evidence.

## New study minimum files

A new study should converge toward:

```text
studies/<study-id>/
├── manifest.yaml
├── source-metadata.json
├── status.yaml
├── HANDOFF.md
├── README.md
├── experiments/
└── evidence/
```

Use:

- `templates/study-status.example.yaml`
- `templates/HEAVY_COMPUTE_HANDOFF.md`

as starting points.

## Verification

Before a PR or push intended as a stable checkpoint:

```bash
make verify
```

This checks lint, tests, manifest validation, study lifecycle files, and handoff consistency.

## Evidence language

Use precise wording:

- "paper reports" for author results;
- "ReproForge measured" for executed results;
- "protocol-equivalent" for structurally similar independent experiments;
- "analogue" for substituted model/data/optimization methods;
- "NOT_RUN" when an experiment was not executed;
- "BLOCKED_MODEL_ACCESS" or similarly explicit status for access failures.

Do not use "reproduced" as shorthand for "implemented".
