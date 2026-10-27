# Studies

Each directory under `studies/` is an independent reproduction study for one paper, method, or research claim set.

Recommended layout:

```text
studies/<study-id>/
├── AGENTS.md
├── manifest.yaml
├── status.yaml
├── HANDOFF.md
├── claims.yaml
├── experiments/
├── evidence/
└── report.md
```

`AGENTS.md` is the local-agent operating guide for lightweight, local/heavy, and real-implementation work. `status.yaml` is the machine-readable current state. `HANDOFF.md` is the human continuation contract.

Before changing a study:

```bash
cat studies/<study-id>/AGENTS.md
reproforge study-status studies/<study-id>
```

Lifecycle:

```text
INTAKE_VERIFIED
    ↓
MECHANISM_VERIFIED
    ↓
PROTOCOL_VERIFIED
    ↓
HEAVY_COMPUTE_READY
    ↓
REPRODUCED
```

`BLOCKED` may be used when licensing, missing assets/specification, or access prevents defensible continuation.

`HEAVY_COMPUTE_READY` means the free/lightweight phase is complete. It does **not** mean the paper is reproduced. The reproduction verdict may still be `PARTIAL`.

A study must not silently inherit licensing assumptions, datasets, code, weights, or claims from another study. Shared reusable logic belongs in `capabilities/` only after promotion criteria are met.

Do not tune against an evaluation after its result has been observed. Create a new version/split and record the old one under `frozen_evaluations`.

## Study index

`status.yaml` is authoritative; `tests/test_study_index.py` fails if this table drifts from it.

| Study | Topic | Lifecycle | Reproduction | Free/light |
|---|---|---|---|---|
| [`arxiv-2609.37590`](arxiv-2609.37590/) | FOCUS | `HEAVY_COMPUTE_READY` | `PARTIAL` | complete |
| [`arxiv-2609.38143`](arxiv-2609.38143/) | Meta-Skills for Agent Harness Design | `HEAVY_COMPUTE_READY` | `PARTIAL` | complete |
| [`arxiv-2610.02858`](arxiv-2610.02858/) | Harness-Aware Distillation (HAD) | `HEAVY_COMPUTE_READY` | `PARTIAL` | complete |
| [`arxiv-2610.03213`](arxiv-2610.03213/) | Task-Tool Relevance | `HEAVY_COMPUTE_READY` | `PARTIAL` | complete |
| [`arxiv-2610.03315`](arxiv-2610.03315/) | LiteTrajEval | `HEAVY_COMPUTE_READY` | `PARTIAL` | complete |
| [`arxiv-2610.06191`](arxiv-2610.06191/) | Evidence-Aware Stopping | `HEAVY_COMPUTE_READY` | `PARTIAL` | complete |
| [`arxiv-2610.06354`](arxiv-2610.06354/) | GraphDecide | `HEAVY_COMPUTE_READY` | `PARTIAL` | complete |
| [`arxiv-2610.07782`](arxiv-2610.07782/) | Persistent Memory Ablation | `HEAVY_COMPUTE_READY` | `PARTIAL` | complete |
| [`arxiv-2610.10062`](arxiv-2610.10062/) | Loud/Quiet Tool Failures | `HEAVY_COMPUTE_READY` | `PARTIAL` | complete |
| [`arxiv-2610.10088`](arxiv-2610.10088/) | SkillSandbox | `HEAVY_COMPUTE_READY` | `PARTIAL` | complete |
| [`arxiv-2610.10265`](arxiv-2610.10265/) | Personal Memory Before Generation | `HEAVY_COMPUTE_READY` | `PARTIAL` | complete |
| [`arxiv-2610.10507`](arxiv-2610.10507/) | RECAST | `HEAVY_COMPUTE_READY` | `PARTIAL` | complete |
| [`arxiv-2610.12176`](arxiv-2610.12176/) | MASS Recursive Self-Improvement | `HEAVY_COMPUTE_READY` | `PARTIAL` | complete |
| [`arxiv-2610.13092`](arxiv-2610.13092/) | Jev Efficiency Transfer | `HEAVY_COMPUTE_READY` | `PARTIAL` | complete |
| [`arxiv-2610.13152`](arxiv-2610.13152/) | TQS Trajectory Structure | `MECHANISM_VERIFIED` | `PARTIAL` | open |
| [`arxiv-2610.22061`](arxiv-2610.22061/) | FAOPs Workflow Normal Forms | `MECHANISM_VERIFIED` | `PARTIAL` | open |
| [`arxiv-2610.22466`](arxiv-2610.22466/) | Harness-Delta Attribution | `MECHANISM_VERIFIED` | `PARTIAL` | open |
| [`arxiv-2610.26793`](arxiv-2610.26793/) | SOMA Metacognitive Monitoring | `PROTOCOL_VERIFIED` | `PARTIAL` | open |
| [`arxiv-2610.32770`](arxiv-2610.32770/) | On-Policy Self-Training (OPST) | `MECHANISM_VERIFIED` | `PARTIAL` | open |

See `docs/STUDY_COMPLETION_POLICY.md`.
