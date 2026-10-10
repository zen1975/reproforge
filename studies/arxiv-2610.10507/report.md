# arXiv:2610.10507 — Verification Report

## Current verdict

**PARTIAL / MECHANISM_VERIFIED**

RECAST treats context construction as a sequential evidence-building problem rather than retrieval alone.

RouterLM selects exactly one action per round:

- `CALL_PRIMITIVE`: lexical, semantic, or relational;
- `SYNTHESIZE`: request a custom deterministic computation from a frozen compiler;
- `ACCEPT_CONTEXT`: terminate evidence construction and hand retained evidence to a separate frozen answer model.

## Protocol captured

Key boundaries from the paper/published prompt:

- RouterLM prepares evidence; it does not answer the task;
- successful primitive execution does not imply evidence sufficiency;
- every evidence-producing operation returns evidence plus source IDs and diagnostics;
- execution outcomes enter interaction history;
- evidence is deduplicated;
- exact computed-answer tasks must not accept retrieved operands before the calculation is performed;
- CompilerLM does not see the original task, so synthesis specifications must repeat all constraints needed for correct implementation;
- AnswerLM is invoked only after context acceptance.

## Independent mechanism fixture

Experiment:

`recast-routing-mechanism-v1`

The frozen fixture verifies:

- structured action validation;
- primitive and synthesis required fields;
- explicit source provenance;
- failed operations recorded without adding evidence;
- evidence deduplication;
- premature ACCEPT blocked when only operands exist;
- ACCEPT allowed once required derived evidence exists;
- incomplete synthesis constraints rejected;
- unknown action rejected;
- missing provenance rejected.

The workflow result is still pending.

## Paper-scale claims not reproduced

The paper trains a Qwen3.5-9B RouterLM with SFT followed by GRPO and reports benchmark improvements across heterogeneous sources. Those training and benchmark claims are outside this mechanism fixture.

## Next lightweight work

After freezing the mechanism result, run one pinned small open model behind the frozen action contract.

The model may own only action selection/formulation. Evidence truth, primitive availability, execution result, provenance validation and context-sufficiency scoring remain external.

## What must not be claimed

Do not claim:

- paper benchmark reproduction;
- reproduction of SFT/GRPO gains;
- CompilerLM code-generation quality;
- that a 0.5B router has paper-level routing capability;
- the reported 75.6% or held-out 79.3% success rates.
