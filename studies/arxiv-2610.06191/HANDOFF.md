# arXiv:2610.06191 — Continuation Handoff

## State

- Lifecycle: `HEAVY_COMPUTE_READY`
- Reproduction verdict: `PARTIAL`
- Free/lightweight phase: complete

The repository already contains the deterministic five-consecutive-USELESS stopping gate, an independent implementation of the paper-defined time-matched contrast Δ, synthetic mechanism/protocol tests, and pinned audits against every released episode cell currently present in the official repository.

## Already executed

- authoritative arXiv intake and full-paper review;
- license/access review;
- deterministic harness stopping gate;
- frozen synthetic stopping-gate benchmark;
- independent time-matched contrast Δ implementation;
- synthetic protocol semantics test;
- pinned official-data audit at commit `2e6404e542b4afdafa3d54d9b18eb1c28c2bafc8`;
- Δ and 95% CI: 43 / 43 released cells exact;
- mean6: 43 / 43 released cells exact;
- answer-after-five-useless summaries: 43 / 43 exact against the pinned official toolkit;
- CI on Python 3.11 / 3.12.

## Not reproduced

ReproForge has **not** independently regenerated the paper's agent trajectories.

The following remain outside the free/lightweight phase:

- original open-model inference runs for Qwen2.5-7B-Instruct;
- original open-model inference runs for Llama-3.1-8B-Instruct;
- original open-model inference runs for Qwen3-8B;
- original Qwen3-32B runs;
- all-condition multi-model sweeps;
- side-channel judgment generation / judge replay from newly generated trajectories;
- Claude API runs;
- exact hardware-equivalence claims;
- any unpublished model-weight revision not explicitly recorded by the paper repository.

Therefore `REPRODUCED` is not yet justified.

## Frozen evaluations — do not tune against

Do not tune implementation or stopping parameters against:

- `stopping-gate-synthetic-v1`;
- `time-matched-contrast-synthetic-v1`;
- released `test300` episodes;
- released `fresh300` episodes;
- `official-episodes-delta-audit-v2-all-released`;
- `official-episode-summary-audit-v1`.

The released data is now audit evidence, not a tuning set.

If a new intervention needs tuning, create a new dev split/version and keep test300/fresh300 frozen.

## Pinned official source

Repository:

```text
https://github.com/bennidict23/judged-useless-queried-anyway
```

Pinned commit:

```text
2e6404e542b4afdafa3d54d9b18eb1c28c2bafc8
```

Licensing recorded by this study:

- official code: MIT
- released episodes: CC BY 4.0
- paper: CC BY 4.0

Do not silently move to a later author commit for a reproduction run. If a newer commit is used, record it as a new experiment version.

## Published execution configuration captured from the pinned repository

Open-model paths expected by the author harness:

- `models/Qwen2.5-7B-Instruct`
- `models/Llama-3.1-8B-Instruct`
- `models/Qwen3-8B`
- `models/Qwen3-32B`

Published experiment configuration includes:

- max agent steps: 8
- max generation tokens: 400
- questions: 300
- batch size: 32
- temperature: 0.0
- seed: 42
- default vLLM tensor parallelism: 1
- Qwen3-32B example: tensor parallel over 4 GPUs
- shuffled-observation mode: `per_question`
- shuffle salt: `shuffled-v2`

Do not invent an exact model-weight revision if it is not explicitly specified by the source.

## External prerequisites

### Open-model regeneration

A fork needs local authorized copies of the relevant model weights and a GPU environment able to run vLLM.

The smallest practical continuation is one open model and two conditions first, for example Qwen3-8B:

- unaided: `--arm none`
- enforced rule: `--arm rule_k5_side`

Large sweeps, especially Qwen3-32B, belong on suitable local GPU hardware.

### Optional Claude replication

The author harness also supports official Anthropic API models.

Secret name:

```text
ANTHROPIC_API_KEY
```

Never commit the value. Claude replication is optional and may incur API cost; it is not required for the free/open-model continuation path.

## Local continuation

Clone the pinned author repository separately rather than vendoring it into ReproForge:

```bash
git clone https://github.com/bennidict23/judged-useless-queried-anyway.git
cd judged-useless-queried-anyway
git checkout 2e6404e542b4afdafa3d54d9b18eb1c28c2bafc8
pip install -e ".[experiments]"
```

Place authorized model weights in the paths expected by `experiments/core/config.py`.

Start with Qwen3-8B:

```bash
cd experiments
python run_gate2.py --arm none --model qwen3-8b --split test300 --gpu 0
python run_gate2.py --arm rule_k5_side --model qwen3-8b --split test300 --gpu 0
```

For unaided trajectories, generate/replay judgments as required by the official protocol:

```bash
python run_judge_replay.py --run-dir results_v2/<unaided-run-dir> --gpu 0
python evaluate.py results_v2/<unaided-run-dir> --judgments results_v2/<replay-dir>
```

For the enforced rule condition:

```bash
python evaluate.py results_v2/<enforced-run-dir>
```

## ReproForge verification entrypoints

The free/lightweight audit remains runnable via:

```text
.github/workflows/stopping-contrast-audit.yml
```

Key ReproForge implementations:

```text
capabilities/agent.evidence-aware-stopping-gate/gate.py
capabilities/agent.evidence-aware-stopping-gate/contrast.py
capabilities/agent.evidence-aware-stopping-gate/summary.py
```

## Expected continuation evidence

For each newly generated model/condition run, preserve:

- model name and exact immutable weight revision/hash if available;
- model license/access source;
- GPU model/count;
- CUDA/vLLM/Python versions;
- source repository commit;
- seed;
- split;
- arm/condition;
- exact command;
- trajectory artifact hash;
- judgment/replay artifact hash where applicable;
- success by regime;
- mean6;
- Δ and 95% CI;
- answer-after-five-useless summary;
- comparison with the released paper value;
- deviations from published configuration.

Store immutable derived evidence under:

```text
studies/arxiv-2610.06191/evidence/
```

Do not commit restricted model weights or secrets.

## Promotion

Do not promote to `REPRODUCED` because the released episodes match.

Promotion requires independently executing sufficiently equivalent model trajectories and meeting the study's declared paper-level acceptance criteria.

Until then keep:

```text
lifecycle: HEAVY_COMPUTE_READY
reproduction_status: PARTIAL
```
