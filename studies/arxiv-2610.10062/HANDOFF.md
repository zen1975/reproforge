# arXiv:2610.10062 — Continuation Handoff

## State

- Lifecycle: `HEAVY_COMPUTE_READY`
- Reproduction verdict: `PARTIAL`
- Free/lightweight phase: complete

## Completed

- authoritative arXiv review;
- full method/protocol extraction;
- author repository and license review;
- author repository pinned at `7abc4bc26e29fa4d1e7799e94bc7c2a96ce3fc66`;
- independent re-aggregation of the released 1,920-row scored table;
- headline RQ1 detection rates matched;
- pooled and per-family RQ2 matched-pair differences matched;
- independent synthetic one-shot fault injection test;
- independent replanning/repetition/state-agreement semantics test;
- real pinned Qwen2.5-0.5B-Instruct boundary run on a frozen clean/loud/quiet analogue.

## Real-model boundary result

Experiment:

`tool-fault-qwen0.5b-analogue-v1`

Model revision:

`7ae557604adf67be50417f59c2c2f167def9a775`

Observed:

- valid outputs: 18 / 18
- every output: `VERIFY`
- clean detection: 1.0
- loud detection: 1.0
- quiet detection: 1.0
- loud - quiet: 0.0 pp

This is negative boundary evidence.

Do not alter the frozen prompt/tasks to force a positive loud-vs-quiet gap.

## Frozen evidence

Do not tune against:

- `official-master-trials-headline-audit-v1`
- `tool-fault-mechanism-synthetic-v1`
- `tool-fault-qwen0.5b-analogue-v1-negative`

## Local/heavy continuation

The next meaningful step is independently generated multi-turn agent trajectories under paper-relevant conditions.

Preserve:

- legal dataset/environment provenance;
- exact environment revision;
- model ID and immutable revision/hash where available;
- clean/loud/quiet matched task identity;
- raw assistant messages;
- raw tool calls and tool results;
- fault markers;
- detection;
- replanning;
- recovery relative to an independent clean run;
- repetition metrics;
- seed and inference settings.

Do not use released author trajectories as a substitute for new behavioral evidence.

## Real implementation direction

The reusable result is not "always verify."

A production tool-fault auditor should preserve separate layers for:

```text
tool result validity
→ fault visibility
→ semantic suspicion
→ replanning
→ recovery
→ repetition / effort
```

A conservative response policy can make detection metrics look perfect while carrying no fault discrimination signal. Keep baseline false alarms visible.
