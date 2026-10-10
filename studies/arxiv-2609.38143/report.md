# arXiv:2609.38143 — Verification Report

## Current verdict

**PARTIAL / MECHANISM_VERIFIED**

The paper studies fixed-weight Builder and Target models where the Builder accumulates reusable support principles from Target execution feedback and uses a frozen bank to construct new task-specific harnesses.

The current ReproForge target is the reusable meta-skill bank/update contract, not the paper benchmark score.

## Protocol captured

Each meta-skill contains:

- `when`: observable conditions that call for support;
- `provide`: capability/resource the environment should supply;
- `use`: how the Target should use that support and which judgments remain the Target's responsibility.

During development, the Builder reviews execution evidence and makes at most one evidence-grounded update per batch/task: add, revise, or keep unchanged.

Before held-out evaluation, the bank is frozen. Test-time Builder access is either full-bank or fixed relevance retrieval, while the Builder constructs a fresh harness for each task.

## Independent mechanism fixture

`meta-skill-bank-mechanism-v1` verifies:

- required structured fields;
- evidence-grounded ADD;
- evidence-grounded REVISE;
- at most one mutation per batch;
- rejection of evidence references not present in the current batch;
- fixed top-k relevance selection;
- mutation rejection after freeze;
- frozen-bank read integrity.

Workflow execution evidence is pending.

## Paper-scale claims not reproduced

The paper reports Builder meta-skill gains on Harness-Bench and NewtonBench and finds that Builder enactment can outperform direct delivery of the same meta-skill bank to the Target.

Those claims require task-specific harness construction and full Target execution under paper/protocol-comparable budgets. They are outside this deterministic fixture.

## Next lightweight work

After the deterministic fixture is frozen, run a pinned small model on synthetic execution-feedback batches. The model may propose KEEP/ADD/REVISE plus a structured skill, but external code owns:

- evidence membership;
- one-mutation-per-batch rule;
- skill ID existence;
- schema validity;
- bank mutation;
- freeze state.

## What must not be claimed

Do not claim:

- Harness-Bench/NewtonBench reproduction;
- the paper's +8.95 or +12.02 point gains;
- Builder enactment superiority from mechanism tests alone;
- that every refinement improves the bank.
