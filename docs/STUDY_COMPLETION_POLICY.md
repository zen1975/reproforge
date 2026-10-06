# Study Completion Policy

ReproForge separates **research completion** from **compute completion**.

A study is allowed to stop at the free/lightweight boundary when it has produced enough evidence, code, and handoff material for another contributor to continue the expensive stages without reconstructing the work from scratch.

## Lifecycle states

Every study MUST declare exactly one lifecycle state in `status.yaml`:

1. `INTAKE_VERIFIED`
   - canonical paper/source identity verified;
   - licensing/access assumptions recorded;
   - no reproduction claim yet.

2. `MECHANISM_VERIFIED`
   - at least one independent executable mechanism test exists;
   - measurable result and evidence are preserved;
   - result is explicitly bounded from paper-level reproduction.

3. `PROTOCOL_VERIFIED`
   - paper evaluation/training structure is reconstructed as far as published information allows;
   - protocol-equivalent data/evaluator/harness exists;
   - unknown paper details remain explicitly unknown.

4. `HEAVY_COMPUTE_READY`
   - the free/lightweight phase is complete;
   - expensive model training, GPU evaluation, private/large datasets, or gated assets are the remaining primary blockers;
   - a reproducible handoff describes exactly how to continue.

5. `REPRODUCED`
   - the declared paper-level acceptance criteria were executed with sufficiently equivalent data/model/protocol/compute;
   - machine-checkable evidence supports the result.

6. `BLOCKED`
   - progress cannot defensibly continue because of missing license permission, unavailable artifacts, missing specification, inaccessible data/model, or another hard blocker that cannot be bypassed without changing the claim.

Lifecycle state and reproduction verdict are separate. A study can be `HEAVY_COMPUTE_READY` while its reproduction verdict remains `PARTIAL`.

## Free/lightweight completion gate

A study MAY be marked `HEAVY_COMPUTE_READY` only when all applicable checks below are true:

- authoritative intake is verified;
- claims and acceptance criteria are explicit;
- external assets and license/access status are recorded;
- an independent mechanism implementation exists;
- a lightweight executable evaluation has run;
- raw/derived Evidence is preserved;
- the paper protocol has been reconstructed as far as the primary source permits;
- published hyperparameters are captured without inventing unpublished values;
- protocol-equivalent evaluator/data/harness exists where practical;
- deterministic seeds or frozen splits are declared;
- at least one negative/boundary result is preserved when observed;
- CI is green;
- remaining blockers are predominantly heavy compute, gated assets, unavailable author artifacts, or deliberately deferred large-scale execution;
- `HANDOFF.md` gives a third party the next commands, prerequisites, expected outputs, frozen inputs, and no-tune boundaries.

This is the default stopping point for the daily ReproForge workflow.

## Heavy compute boundary

Examples that normally belong after `HEAVY_COMPUTE_READY`:

- multi-billion-parameter full/fine-tuning runs;
- H100/A100-class training;
- large GRPO/RL runs with many generations per prompt;
- multi-seed large benchmark sweeps;
- very large licensed/private datasets;
- long-running local simulations.

These are not required for the free/lightweight phase to be considered complete.

## No fabrication rule

Unknown paper details MUST remain unknown.

Do not invent:

- reward weights;
- hidden prompts;
- dataset mixture ratios;
- decoding parameters;
- unpublished preprocessing;
- hardware-equivalence claims;
- missing author data.

A fork may choose an independent substitute, but it must be labeled as an analogue or protocol-equivalent experiment, never as exact reproduction.

## Frozen evaluation rule

Once a held-out or blind evaluation result has been observed, that split MUST NOT be used for further tuning under the same experiment version.

Create a new version/split instead.

## Fork handoff rule

Every `HEAVY_COMPUTE_READY` or `BLOCKED` study MUST include:

- `status.yaml`
- `HANDOFF.md`
- executable scripts or workflow entrypoints;
- exact known dependencies/configuration;
- explicit secrets/credentials names, never values;
- open gaps;
- expected artifacts/evidence paths;
- commands for local continuation;
- a warning against tuning on frozen test data.

A contributor should be able to fork the repository, run the standard checks, read two files, and know what to do next.

## Standard continuation flow

```text
fork / clone
    ↓
make bootstrap
    ↓
make verify
    ↓
reproforge study-status studies/<study-id>
    ↓
read studies/<study-id>/HANDOFF.md
    ↓
satisfy external prerequisites
    ↓
run the declared next command/workflow
    ↓
save new Evidence
    ↓
advance lifecycle state only when its gate is met
```
