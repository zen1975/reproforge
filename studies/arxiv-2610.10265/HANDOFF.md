# arXiv:2610.10265 — Continuation Handoff

## State

- Lifecycle: `MECHANISM_VERIFIED`
- Reproduction: `PARTIAL`
- Free/light phase: incomplete

## Completed

- full public HTML protocol review;
- arXiv license captured;
- keyed-supersession state invariant independently implemented;
- missed-merge and false-merge failure modes independently exercised;
- prompt-level current/stale/wrong-person/abstention/deadline metrics implemented;
- deterministic mechanism fixture passed.

## Frozen evidence

- `memory-validity-mechanism-v1`

Do not tune against this fixture.

## Next lightweight experiment

Use one pinned small open model with fixed prompts where only the memory block changes:

1. clean current fact;
2. current + stale fact;
3. current + same-name wrong-person fact.

Keep target truth, memory labels, and scoring outside the model.

Record whether generated text copies:

- current value;
- stale value;
- wrong-person value;
- none/abstention.

A negative/null propagation result must be retained.

## Local/heavy continuation

After the response-level boundary, paper-scale work can test:

- noisy key assignment;
- controlled benchmark rates;
- LongMemEval merge recall;
- LoCoMo same-name identity ambiguity;
- latency/prefill measurements.

Do not collapse these into one memory-accuracy score.
