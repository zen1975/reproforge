# ReproForge Agent Guide

This repository turns research into independently verified, reusable capabilities.

This file is the root operating contract for coding/research agents. A nearer `AGENTS.md` inside a study or capability adds more specific instructions and takes precedence for that subtree.

## Start here

Before changing anything:

```bash
python -m venv .venv
source .venv/bin/activate
make bootstrap
make verify
```

For study work:

```bash
reproforge study-status studies/<study-id>
cat studies/<study-id>/AGENTS.md
cat studies/<study-id>/HANDOFF.md
```

For capability work:

```bash
cat capabilities/<capability-id>/AGENTS.md
cat capabilities/<capability-id>/capability.yaml
```

## Choose the work lane

### Lane A — free/lightweight verification
Use GitHub Actions / CPU / small public models / synthetic or legally usable fixtures.

Goal:
- verify mechanism;
- reconstruct protocol;
- run boundary/negative tests;
- preserve evidence;
- make the experiment deterministic and forkable.

### Lane B — local/heavy verification
Use this when the study is `HEAVY_COMPUTE_READY` or its local `AGENTS.md` says the remaining step belongs on local compute.

Before running:
- inventory CPU, RAM, GPU/VRAM, disk and runtime;
- pin model/dataset revisions when possible;
- preserve exact commands/environment;
- use new unseen evaluation splits if prior held-out results were observed.

Heavy runs extend the evidence chain; they never overwrite lightweight evidence.

### Lane C — real implementation / operationalization
Productionization requires:
- stable I/O contract;
- explicit failure behavior;
- deterministic/fail-closed behavior where claimed;
- provider-neutral core;
- adapters kept separate;
- tests for operational guarantees;
- licensing/provenance recorded.

## Evidence rules
Always preserve model/provider/revision when known, seed, dataset/split/version, command/config, raw or minimally transformed outputs, evaluator version and hashes where practical.

Never invent unpublished coefficients, reward weights, prompts, seeds, mixture ratios, preprocessing, decoding parameters or hardware-equivalence claims. Unknown remains unknown.

## Frozen evaluation rule
Once a held-out/blind result is observed, do not tune against it under the same experiment version. Create a new experiment version and unseen split/state set; preserve the prior result.

## Claims
Lifecycle and reproduction verdict are separate. `HEAVY_COMPUTE_READY` means the free/lightweight phase is complete; it does not mean the paper is reproduced.

## Repository hygiene
Do not commit secrets/tokens, restricted datasets, model weights without redistribution permission, or paper artifacts without verified permission. Run `make verify` before handoff.
