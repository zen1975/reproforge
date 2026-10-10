# arXiv:2610.07782 — Continuation Handoff

## State

- Lifecycle: `MECHANISM_VERIFIED`
- Reproduction: `PARTIAL`
- Free/light phase: incomplete

## Completed

- full 13-page PDF reviewed;
- CC BY 4.0 paper license verified;
- C1-C4 ablation-validity conditions extracted;
- independent deterministic audit implementation added;
- structural distinction between independent-item and shared-state regimes encoded.

## Frozen evaluation

- `persistent-memory-ablation-audit-v1`

The fixture is frozen before workflow execution. Do not modify it after observing results merely to force PASS.

## Required current step

Execute the workflow and retain:

- result JSON;
- workflow run ID;
- artifact ID/digest;
- any negative evidence.

## Local/heavy continuation

Paper-scale reproduction requires:

- comparable model-serving architecture;
- per-call token/KV accounting;
- persistent trace store and live recall probe;
- paired dataset arms;
- trace reset/isolation;
- order counterbalancing;
- replicate campaigns;
- paired and cluster bootstrap analysis.

Keep **memory efficacy** separate from **decomposition working-set benefit**.
