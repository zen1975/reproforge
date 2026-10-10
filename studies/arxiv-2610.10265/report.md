# arXiv:2610.10265 — Verification Report

## Current verdict

**PARTIAL / HEAVY_COMPUTE_READY**

The current free/lightweight boundary is complete.

The paper evaluates personal memory before generation rather than hiding retrieval failures inside final-answer accuracy. ReproForge independently reconstructed the state and metric semantics, then executed two frozen Qwen2.5-0.5B-Instruct boundary experiments.

This is not paper-level reproduction.

## Independent mechanism verification

Experiment: `memory-validity-mechanism-v1`

Verified:

- keyed serial supersession leaves at most one active value for a correct key;
- superseded facts remain available as history;
- missed merge can leave stale and current values simultaneously active;
- false merge can close an unrelated current value;
- wrong-person exposure is distinct from staleness;
- unanswerable/abstention behavior is independently measurable;
- prompt cleanliness is distinct from meeting a serving deadline.

Result: **PASS**

## Real 0.5B response-propagation boundary

Experiment: `memory-qwen0.5b-response-propagation-v1`

Model revision:

`7ae557604adf67be50417f59c2c2f167def9a775`

Four frozen cases were evaluated under:

- clean current-only memory;
- current + stale memory;
- current + same-name wrong-person memory.

Across all 12 generations:

- current-value rate: **1.0**
- stale-value rate: **0.0**
- wrong-person-value rate: **0.0**

Workflow: `38046223429`

Artifact: `11667709358`

Digest: `sha256:63e1aedd8d8b34931f168a3521388c9ef499ebd21e7bb1c81dff6a1e298195f2`

Interpretation:

This frozen 0.5B analogue did **not** reproduce prompt-error propagation. The model consistently selected the explicitly current fact even when stale or same-name wrong-person facts were co-injected.

This is negative boundary evidence and the fixture must not be rewritten after seeing the result.

## Real 0.5B key-assignment boundary

Experiment: `memory-qwen0.5b-key-assignment-v1`

Twelve frozen observation pairs:

- 6 true same-slot revisions;
- 6 same-entity but different-slot pairs.

Results:

- valid MERGE/SPLIT output: **12/12**
- true-revision merge recall: **100%**
- false-merge rate: **100%**
- accuracy: **50%**
- raw behavior: **MERGE on all 12 pairs**

Workflow: `38046345308`

Artifact: `11668015059`

Digest: `sha256:7696b991362f5bfd1bac93346ab6b1d75ecb3c32a43d062bc3b0fd01e23a1e0a`

Interpretation:

The model avoided missed merges only by merging everything. This destroys slot specificity and creates the opposite failure mode.

So:

`high merge recall != correct memory identity`

and:

`valid MERGE/SPLIT interface != usable key assignment`

This collapse is retained as negative evidence.

## Paper results not independently reproduced

The paper reports, on its controlled benchmark, that active-only keyed retrieval removed observed stale exposure while the keyless store exposed superseded values frequently. It also reports that response-level contamination can propagate with larger frozen models, and that serving latency/pre-fill cost is a separate systems dimension.

Those paper-scale rates and serving measurements are outside the current lightweight boundary.

## Current-environment closure

Remaining meaningful work now requires one or more of:

- controlled/protocol-comparable benchmark generation;
- LongMemEval or LoCoMo-style public-corpus evaluation;
- larger/comparable frozen models;
- serving latency/prefill measurements.

Therefore:

- `HEAVY_COMPUTE_READY`
- `free_light_phase_complete: true`
- `reproduction_status: PARTIAL`

## What must not be claimed

Do not claim:

- reproduction of the paper's stale-exposure rates;
- reproduction of LongMemEval/LoCoMo results;
- confirmation that prompt contamination never propagates;
- confirmation that all small models over-merge;
- full paper reproduction.
