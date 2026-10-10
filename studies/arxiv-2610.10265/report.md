# arXiv:2610.10265 — Verification Report

## Current verdict

**PARTIAL / MECHANISM_VERIFIED**

The paper evaluates memory before generation rather than hiding retrieval failures inside final-answer accuracy. It separates current-value recall, stale exposure, wrong-person exposure, abstention, and clean retrieval by a serving deadline.

The current ReproForge study independently verifies the state and metric semantics only.

## Protocol captured

The paper defines a personal fact with:

- prompt-ready text;
- normalized entities;
- participants;
- optional mutable-slot key;
- active interval;
- last-observed time.

A serial atomic update sharing a key closes the previous active value while retaining it as history. This guarantees at most one active value per key, but not semantic correctness if key assignment or arrival order is wrong. citeturn749291view0

The paper explicitly separates:

- current-value recall;
- stale exposure;
- wrong-person exposure;
- abstention;
- clean retrieval;
- clean retrieval before deadline.

## Independent mechanism verification

Experiment: `memory-validity-mechanism-v1`

Verified:

- correct keyed revision → one active value, old value retained as history;
- missed merge → stale and current values can both remain active;
- false merge → unrelated current value can be silently removed;
- same-name wrong-person exposure is distinct from staleness;
- controlled identity filtering removes the wrong-person fact;
- an unanswerable request is clean only when no relevant fact is injected;
- prompt cleanliness and deadline success are separate dimensions.

Result: **PASS**

## Paper results not reproduced yet

The paper reports zero observed stale exposure for keyed active-only retrieval in its controlled benchmark, versus 70.3% stale exposure in the keyless store, and finds that once active-store and participant information are fixed, participant-aware BM25 is equivalent to the reference ranker within a prespecified ±0.02 margin. citeturn749291view0

Those are paper benchmark rates, not results of the current independent synthetic experiment.

## Next lightweight work

Run a frozen real-model response-propagation analogue:

- clean memory block;
- current + stale co-injection;
- same-name wrong-person injection.

Ground-truth memory labels remain external. The model only generates the completion.

## What must not be claimed

Do not claim:

- reproduction of the paper's 0% / 70.3% stale-exposure rates;
- LongMemEval or LoCoMo reproduction;
- replication of model key-assigner behavior;
- response-level propagation until the frozen model experiment is executed.
