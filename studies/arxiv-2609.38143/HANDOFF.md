# arXiv:2609.38143 — Continuation Handoff

## State
- Lifecycle: `HEAVY_COMPUTE_READY`
- Reproduction: `PARTIAL`
- Free/light phase: complete

## Completed
- public protocol review;
- deterministic when/provide/use bank mechanism;
- evidence-grounded ADD/REVISE contract;
- one-mutation-per-batch guard;
- frozen-bank integrity;
- full-bank and fixed top-k selection;
- real pinned Qwen2.5-0.5B update-proposal analogue.

## Frozen evidence
- `meta-skill-bank-mechanism-v1`
- `meta-skill-qwen0.5b-update-analogue-v1-negative`

The 0.5B run produced 40% schema validity, 40% decision accuracy, 0% evidence grounding on expected mutations and 33.3% skill-ID accuracy on expected mutations.

Do not retune this fixture.

## Local/heavy continuation

Run Builder harness construction and Target execution over held-out benchmark tasks with a frozen meta-skill bank.

Preserve:

- execution evidence IDs;
- exact model/revision;
- bank snapshot/hash;
- selected meta-skills;
- generated harness;
- Target outcome;
- update prohibition during held-out evaluation;
- per-task budget and seeds.

Model-generated bank updates remain proposals only; external validation owns bank integrity.
