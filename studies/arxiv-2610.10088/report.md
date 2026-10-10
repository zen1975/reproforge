# arXiv:2610.10088 — Verification Report

## Current verdict

**PARTIAL / HEAVY_COMPUTE_READY**

The current free/lightweight boundary is complete.

ReproForge independently reconstructed the scenario-validity and paired verifier semantics, then executed two real Qwen2.5-0.5B-Instruct boundary experiments:

1. paired with-skill / without-skill execution;
2. frozen Proposer-style scenario generation.

The paper's full ALFWorld/WebShop pipeline is not reproduced.

## Mechanism verification

`skillsandbox-verifier-mechanism-v1` verifies:

- relevant + novel scenario validity;
- irrelevant scenario rejection;
- source-identical scenario rejection;
- executability gating;
- helpful/faster evidence → positive / KEEP;
- harmful/slower evidence → negative / REJECT;
- non-executable evidence → zero / REJECT.

Result: **PASS**

## Real 0.5B paired execution boundary

Experiment: `skillsandbox-qwen0.5b-paired-analogue-v1`

Model revision:

`7ae557604adf67be50417f59c2c2f167def9a775`

Six frozen scenarios were run with the same model and same scenario state, changing only whether a procedural skill was present.

Helpful skill:

- executability: **1.0**
- without-skill reward: **0.0**
- with-skill reward: **1.0**
- score: **1.0**
- verdict: **KEEP**

Harmful skill:

- executability: **0.5**
- without-skill reward: **0.0**
- with-skill reward: **0.5**
- score: **0.0**
- verdict: **REJECT**

Workflow: `38045966149`

Artifact: `11667209445`

Digest: `sha256:7583a39ccd196fc182a6f0150ddcd11fbe1fb3db2c79e7fc1a89e9918ab844b6`

This confirms that the external paired verifier can distinguish a genuinely useful procedural instruction from one that is not reliably executed or beneficial in the frozen small-model analogue.

It does **not** establish the paper's benchmark-level verifier accuracy.

## Real 0.5B Proposer boundary

Experiment: `skillsandbox-qwen0.5b-proposer-analogue-v1`

Six frozen applicability/source-detail prompts were used. Relevance, novelty, and format were scored by deterministic external validators.

Results:

- relevance: **3/6 = 50.0%**
- novelty: **5/6 = 83.3%**
- format validity: **4/6 = 66.7%**
- fully valid scenario: **2/6 = 33.3%**

Workflow: `38046125196`

Artifact: `11667224961`

Digest: `sha256:242d3de5989157ec28583960b0ffd99e1bbcf7a60c6bac5a46fed68af652514c`

Interpretation:

The small model was better at changing source-specific details than at preserving the target applicability condition while satisfying the output contract.

So the lightweight boundary suggests:

`novel generation != valid skill-relevant scenario synthesis`

This is retained as negative/partial evidence. The fixture is frozen and must not be prompt-tuned to manufacture a stronger result.

## Current-environment closure

Meaningful remaining work requires an executable Builder and multi-step agent environment, plus paper-relevant or comparable model rollouts.

Therefore:

- `HEAVY_COMPUTE_READY`
- `free_light_phase_complete: true`
- `reproduction_status: PARTIAL`

## What must not be claimed

Do not claim:

- ALFWorld/WebShop reproduction;
- paper downstream success-rate gains;
- paper verifier F1;
- that 0.5B scenario synthesis is generally poor;
- full SkillSandbox reproduction.
