# arXiv:2610.12176 — Verification Report

## Current verdict

PARTIAL / MECHANISM_VERIFIED

MASS closes an RSI loop by alternating workflow optimization and model post-training.

Scientific decomposition:
1. workflow-search improvement;
2. self-evaluator improvement;
3. task-solving improvement;
4. transfer from task-solving-only SFT to optimizer/evaluator roles;
5. coordination/information-routing internalization;
6. recursive improvement across generations;
7. external held-out confirmation.

## Paper protocol captured

Within generation g:
- executor = evaluator = optimizer = L(g);
- each task maintains an independent workflow search;
- every workflow proposal is executed;
- incumbent changes only when the self-evaluator prefers the proposal;
- the retained workflow is best under sequential self-comparisons, not a certified global optimum;
- retained workflows generate multiple candidate trajectories;
- pairwise self-evaluation becomes a trajectory ranking;
- top trajectories train the model and a separate trajectory is reserved for validation;
- optimized workflow text is removed from prompts used for SFT construction;
- test tasks do not enter SFT;
- external strong judges are held out from the MASS loop and used for final evaluation.

The updated model assumes all three roles in the next generation.

## Important paper-reported results

The paper reports evaluator agreement with external judgments rising 0.73 -> 0.91 -> 0.93 and synthetic test-task win rate against the base model rising from 53.9% after cycle 1 to 69.9% after cycle 2.

It also reports that workflows produced by L1, when executed by the fixed base model, beat L0 workflows in 64% of comparisons. This is stronger evidence that the workflow optimizer itself improved rather than only the executor.

Behavioral audits under bare prompts report delegation rising 1/110 -> 48/110 -> 87/110 and code handoffs 1/110 -> 42/110 -> 83/110 across L0/L1/L2.

These are paper-reported results, not independently reproduced by ReproForge.

## Official-repository provenance boundary

Official repository: SakanaAI/mass
Pinned inspected revision: fb403581bed2c974b3f99e7236224169da643079

The repository NOTICE says no public open-source license has been assigned to MASS-specific code. ReproForge does not copy or redistribute it.

The official repository also documents important reconstruction differences:
- current RHI driver uses a fixed bare-task reference before retained-champion comparison, while the paper algorithm compares proposals directly with retained best output;
- complete historical run ledger is unavailable;
- second-cycle budget is a reconstruction choice;
- exact historical tournament ledger is unavailable.

## Independent mechanism verification

Experiment: mass-rsi-loop-mechanism-v1

Verified:
- homogeneous executor/evaluator/optimizer identity within generation;
- recursive model transition between generations;
- elite-one incumbent retention;
- execution of losing/non-monotonic proposals;
- train/test task isolation;
- task-local ranking;
- training/validation trajectory separation;
- self-evaluation inside the loop;
- external evaluation held out from selection.

Result: PASS

## Remaining lightweight work

Before closing the CPU/lightweight boundary, test a real small model on frozen analogues of:
1. workflow proposal generation;
2. self-evaluation of candidate vs incumbent;
3. evaluator agreement with external deterministic truth;
4. separation between proposal quality and evaluator quality.

No prompt tuning after observing frozen results.

## Heavy boundary

Paper-level reproduction requires Qwen3.6-27B or comparable larger model, multi-agent coding-agent execution, recursive generations, trajectory collection/ranking, long-context LoRA training, held-out benchmark runs, independent external evaluation, and behavioral lineage.

## Do not claim yet

Do not claim MASS paper reproduction, independently demonstrated RSI, reproduced evaluator improvement, reproduced real-model workflow improvement, or independently demonstrated coordination internalization.
