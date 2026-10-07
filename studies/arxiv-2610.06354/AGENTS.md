# Agent Guide — arXiv:2610.06354

## State
- Lifecycle: `INTAKE_VERIFIED`
- Reproduction: `NOT_RUN`
- Free/light phase: NOT complete
- Working label: `GraphDecide`

Read `status.yaml` first. This study is still at intake; do not jump to heavy/local compute.

## Verified boundary
Only the primary arXiv identity and the current licensing boundary are verified.

The author repository currently has no declared repository license. Do not copy, vendor, redistribute, or treat author code/assets as reusable implementation material unless that licensing state changes and is verified.

## Lightweight next step
Remain in the CPU/lightweight lane:
1. independently reconstruct the paper's graph-decision problem and evaluation contracts from primary sources;
2. define a provider-neutral mechanism interface;
3. build a small synthetic graph-decision fixture;
4. verify core decision behavior, boundary cases, and failure semantics;
5. create machine-checkable evidence before promoting any capability;
6. only then decide whether model-backed or heavy evaluation is justified.

Do not invent unpublished graph construction rules, coefficients, prompts, model revisions, seeds, evaluator settings, or dataset transformations.

## Local/heavy guidance
No heavy run is justified yet.

A future move to local/GPU compute requires at minimum:
- mechanism verification;
- reconstructed evaluation protocol;
- explicit model/data requirements;
- a frozen lightweight baseline;
- an updated `status.yaml` boundary.

## Real implementation direction
If the paper yields a reusable graph-decision capability, keep graph state/evidence construction separate from any learned decision model.

Prefer an architecture where graph facts, relations, provenance and constraints remain inspectable, while model inference is a replaceable decision layer.

Do not create or register a production capability until the contract and evidence are explicit.

## Frozen / no-tune
There are currently no frozen evaluations. Once any held-out result is observed, version it and do not tune against it under the same experiment version.
