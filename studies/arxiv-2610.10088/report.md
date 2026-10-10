# arXiv:2610.10088 — Verification Report

## Current verdict

**PARTIAL / MECHANISM_VERIFIED**

SkillSandbox verifies a distilled skill by constructing scenarios that are both skill-relevant and novel, then comparing the same executor with and without the skill. The paper scores retained aligned step pairs using executability-weighted discounted utility and keeps a skill only when the empirical reusability score is positive.

## Paper mechanism captured

The inspected paper specifies:

- Proposer: preserve the skill's applicability condition while changing source-specific details;
- Builder: instantiate an executable task/environment and reject invalid or duplicate scenarios until five valid scenarios are obtained;
- Verifier: compare with-skill and without-skill trajectories in the same scenario;
- aligned evidence: identical pre-action observations, temporal order preserved;
- executability: only observed skill-implementing actions contribute;
- utility/efficiency: terminal reward discounted by remaining actions;
- verdict: `KEEP` iff `R(k) > 0`, otherwise `REJECT`.

The paper also explicitly distinguishes Recovery from Regression and evaluates held-out utility rather than assuming every distilled skill is beneficial.

## Independent synthetic mechanism verification

Experiment:

`skillsandbox-verifier-mechanism-v1`

Verified:

- relevant + novel scenario → valid;
- novel but irrelevant scenario → rejected;
- relevant but source-identical scenario → rejected;
- helpful/faster skill evidence → positive score / KEEP;
- harmful/slower skill evidence → negative score / REJECT;
- no executability evidence → zero contribution / REJECT.

Result: **PASS**

A gamma of 0.9 is used only as an analogue parameter. The inspected public HTML states `0 < gamma < 1` but does not expose a numeric value; therefore no exact paper-gamma claim is made.

## Remaining lightweight work

A small real-model paired analogue is still justified.

The next frozen experiment should:

1. use independently authored structured scenarios;
2. run the same pinned small model with and without one procedural skill;
3. preserve identical initial scenario state;
4. keep success truth and score calculation outside the model;
5. record raw model decisions;
6. retain negative or null skill effects without prompt tuning.

## What must not be claimed

Do not claim:

- ALFWorld/WebShop reproduction;
- the paper's downstream SR gains;
- the paper's verdict F1;
- that scenario synthesis is already superior to source/random task verification.

Those claims require model-backed benchmark evidence.
