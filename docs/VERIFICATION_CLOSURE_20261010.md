# ReproForge Verification Closure — 2026-10-10

This document records the current-environment closure state after the 2026-10-10 verification pass.

It does **not** mean that every paper has been fully reproduced.

The distinction is:

- **CURRENT-ENVIRONMENT COMPLETE**: no additional meaningful free/lightweight or ordinary CPU experiment is required to establish the study's present boundary.
- **REPRODUCED**: paper-level claims have been independently tested under protocol-equivalent conditions.

All active studies remain `reproduction_status: PARTIAL`.

## Active study matrix

| Study | Lifecycle | Free/light | Current-environment closure | Remaining primary work |
|---|---|---:|---|---|
| arXiv:2609.37590 — FOCUS | HEAVY_COMPUTE_READY | complete | CURRENT-ENVIRONMENT COMPLETE | paper-scale draft models and full agent benchmarks |
| arXiv:2609.38143 — Meta-Skills for Agent Harness Design | HEAVY_COMPUTE_READY | complete | CURRENT-ENVIRONMENT COMPLETE | held-out Builder/Target harness execution at paper-relevant scale |
| arXiv:2610.02858 — HAD | HEAVY_COMPUTE_READY | complete | CURRENT-ENVIRONMENT COMPLETE | long-horizon on-policy benchmark training with larger student/teacher |
| arXiv:2610.03213 — Task-Tool Relevance | HEAVY_COMPUTE_READY | complete | CURRENT-ENVIRONMENT COMPLETE | authorized Gemma 3 access, GPU LoRA SFT, then paper-scale GRPO |
| arXiv:2610.03315 — LiteTrajEval | HEAVY_COMPUTE_READY | complete | CURRENT-ENVIRONMENT COMPLETE | legal public failed trajectories, paper-comparable judge, cost/runtime comparison |
| arXiv:2610.06191 — Evidence-Aware Stopping | HEAVY_COMPUTE_READY | complete | CURRENT-ENVIRONMENT COMPLETE | independently regenerated 7B–32B trajectories |
| arXiv:2610.06354 — GraphDecide | HEAVY_COMPUTE_READY | complete | CURRENT-ENVIRONMENT COMPLETE | legal public graph slice and paper-relevant model/readout settings |
| arXiv:2610.07782 — Persistent Memory Ablation | HEAVY_COMPUTE_READY | complete | CURRENT-ENVIRONMENT COMPLETE | comparable serving hardware, persistent store and replicate campaign |
| arXiv:2610.10062 — Loud/Quiet Tool Failures | HEAVY_COMPUTE_READY | complete | CURRENT-ENVIRONMENT COMPLETE | independently generated paper-relevant multi-turn trajectories |
| arXiv:2610.10088 — SkillSandbox | HEAVY_COMPUTE_READY | complete | CURRENT-ENVIRONMENT COMPLETE | executable Builder environments and ALFWorld/WebShop or comparable rollouts |
| arXiv:2610.10265 — Personal Memory Before Generation | HEAVY_COMPUTE_READY | complete | CURRENT-ENVIRONMENT COMPLETE | controlled/public corpora, larger models and latency/identity evaluation |
| arXiv:2610.10507 — RECAST | HEAVY_COMPUTE_READY | complete | CURRENT-ENVIRONMENT COMPLETE | trained/larger RouterLM, CompilerLM/AnswerLM and benchmark environments |

## New boundary evidence closed on 2026-10-10

### arXiv:2610.10062 — Loud Failures, Quiet Failures

Released 1,920-trial data re-aggregation matched the paper headline rates:

- loud detection: **91.346%**
- quiet detection: **58.824%**
- clean baseline detection: **26.797%**
- matched reasoning-minus-instruct detection: **-9.333 pp**
- matched reasoning-minus-instruct replanning: **+10.444 pp**

This is an **OFFICIAL_AUDIT**, not independent behavioral reproduction.

A frozen real Qwen2.5-0.5B analogue produced valid outputs on all 18 decisions but collapsed to `VERIFY` under clean/loud/quiet:

- clean detection: 1.0
- loud detection: 1.0
- quiet detection: 1.0
- loud - quiet: **0.0 pp**

Boundary:

`valid decision interface != fault-type discrimination`

Negative evidence is retained.

### arXiv:2610.10088 — SkillSandbox

Independent mechanism verification passed for:

- scenario relevance + novelty;
- executability gating;
- paired utility;
- KEEP / REJECT logic.

Real Qwen2.5-0.5B paired analogue:

Helpful skill:
- executability: **1.0**
- without-skill reward: **0.0**
- with-skill reward: **1.0**
- score: **+1.0**
- verdict: **KEEP**

Harmful skill:
- executability: **0.5**
- score: **0.0**
- verdict: **REJECT**

Frozen 0.5B Proposer analogue:

- relevance: **3/6**
- novelty: **5/6**
- format validity: **4/6**
- fully valid scenarios: **2/6**

Boundary:

`novel generation != valid skill-relevant scenario synthesis`

### arXiv:2610.10265 — Stale, Misattributed, or Late

The paper's pre-generation metric separation is retained:

- current-value recall;
- stale exposure;
- wrong-person exposure;
- abstention;
- clean retrieval by deadline.

Independent mechanism verification covers keyed supersession and these separated metrics.

Real Qwen2.5-0.5B boundaries:

- response-propagation analogue retained the current value across clean/stale/wrong-person cases;
- key-assignment analogue collapsed to `MERGE` on all 12 pairs;
- merge recall: **100%**
- false-merge rate: **100%**

Boundary:

`high merge recall != valid slot assignment`

### arXiv:2610.07782 — Persistent Memory

The independent ablation-validity audit now distinguishes:

- actual component reachability from nominal configuration;
- single-axis ablations from contaminated-store or order-confounded tests;
- measurement-floor limits from meaningful null effects;
- recall reachability from useful shared-state recall.

No paper-scale serving or memory-efficiency claim is made.

### arXiv:2610.10507 — RECAST

The routing/state/provenance mechanism passes the frozen deterministic contract.

Real Qwen2.5-0.5B Router analogue:

- valid structured actions: **87.5%**
- routing accuracy: **12.5%**
- primitive-subtype accuracy: **0%**
- computed-evidence guard premature ACCEPT_CONTEXT: **100%**

The model collapsed toward ACCEPT on every parseable case.

Boundary:

`valid routing syntax != evidence-routing competence`

### arXiv:2609.38143 — Meta-Skills for Agent Harness Design

The deterministic bank mechanism passes:

- when / provide / use schema;
- evidence-grounded ADD/REVISE;
- one mutation per batch;
- freeze integrity;
- fixed top-k retrieval.

Real Qwen2.5-0.5B update-proposal analogue:

- schema-valid rate: **40%**
- decision accuracy: **40%**
- evidence grounding on expected mutations: **0%**
- skill-ID accuracy on expected mutations: **33.3%**

KEEP/REVISE cases largely collapsed toward ADD.

Boundary:

`model proposal != admissible bank mutation`

The external validator remains authoritative over evidence, schema, mutation count and bank state.

## Cross-study pattern

The new studies reinforce the same pattern already visible in GraphDecide:

- valid output format does not prove intended information use;
- conservative or collapsed policies can make superficial metrics look strong;
- retrieval or merge recall can hide destructive false positives;
- generation novelty does not prove scenario validity;
- model-generated state changes should remain proposals until externally validated.

ReproForge therefore keeps these layers separate:

```text
Protocol
→ Mechanism
→ Interface validity
→ Behavioral utilization
→ External validation
→ Paper-level reproduction
```

## Global closure rule

A study is CURRENT-ENVIRONMENT COMPLETE only when:

1. `free_light_phase_complete: true`;
2. lifecycle is `HEAVY_COMPUTE_READY` or later;
3. handoff is ready;
4. frozen evaluations are listed;
5. negative and null evidence are retained;
6. the next step is genuinely gated by data/model/compute/environment access;
7. CI is green.

At this closure point, all 12 active studies satisfy the study-level conditions above.

Global CI for the final study-state commit:

- run: `38048861861`
- result: **SUCCESS**

This document does not override study-specific `status.yaml`, `HANDOFF.md`, `AGENTS.md`, or evidence artifacts.
