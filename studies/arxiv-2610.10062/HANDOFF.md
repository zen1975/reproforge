# arXiv:2610.10062 — Continuation Handoff

## State

- Lifecycle: `PROTOCOL_VERIFIED`
- Reproduction verdict: `PARTIAL`
- Free/lightweight phase: **not complete**

## Completed

- authoritative arXiv review;
- full method/protocol extraction;
- author repository and license review;
- author repository pinned at `7abc4bc26e29fa4d1e7799e94bc7c2a96ce3fc66`;
- independent re-aggregation of the released 1,920-row scored table;
- headline RQ1 detection rates matched;
- pooled and per-family RQ2 matched-pair differences matched;
- independent synthetic one-shot fault injection test;
- independent replanning/repetition/state-agreement semantics test.

## Frozen evidence

Do not tune against:

- `official-master-trials-headline-audit-v1`
- `tool-fault-mechanism-synthetic-v1`

Released author data is audit evidence, not a dev set.

## Next required lightweight experiment

Run a real small open model behind a frozen tiny tool environment.

Minimum conditions:

1. clean;
2. loud explicit error;
3. quiet corruption with a valid-looking payload.

Requirements:

- pin model ID and immutable revision;
- freeze tasks/prompts before execution;
- preserve raw assistant messages and tool calls;
- use the same detection definition across conditions;
- report valid tool-call rate separately from detection;
- do not change prompts after seeing results;
- retain a negative/no-gap result if that is what occurs.

A Qwen2.5-0.5B-Instruct analogue is acceptable as a boundary experiment but must be labelled an analogue, not a reproduction of the paper's model panel.

## Paper-level continuation

Paper-level reproduction requires independently generating multi-turn trials with sufficiently comparable task environments, faults, and matched model conditions. The author's released trajectories can verify aggregation but cannot substitute for new trajectories.

## Source configuration captured

Author repository declares:

- 24 frozen BFCL tasks;
- 5 conditions;
- 2 repetitions per cell;
- max 15 tool calls;
- temperature 1.0;
- timeout / missing tool / schema drift as loud faults;
- silent corruption as quiet;
- repetition threshold: 3 consecutive same-tool calls;
- recovery against the same model/task clean end state.

Do not silently change these facts when making paper-comparable claims.
