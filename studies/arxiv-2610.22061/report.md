# Results — FAOP-like static verifier

## Result

The frozen synthetic mechanism suite executed successfully: 14/14 expected case outcomes. It contains two valid workflows and twelve negative/boundary cases covering multi-effect leaves, unproduced fields, unresolved calls, recursive call graphs, out-of-scope tools, callee scope escalation, unbounded loops, missing time/cost bounds, branch output guarantees, duplicate ids, missing call inputs, and loop outputs that are not guaranteed after zero or more iterations.

The shape-only baseline accepted 14/14 structurally shaped registries and falsely accepted all 12 invalid cases. This baseline only checks required top-level fields; the result demonstrates the need for semantic checks beyond object shape, not superiority over a full static analyzer.

## Interpretation boundary

These results establish only that the independent implementation satisfies its frozen synthetic acceptance criteria. They are not results reported by the paper, do not reproduce the author's SkillBase compiler/executor, and do not verify runtime enforcement or real-world effect labels. The paper's own evaluation section states that the work is theory-first and defers a full empirical study.

## Lifecycle

MECHANISM_VERIFIED / PARTIAL. Further lightweight protocol-equivalence work remains; HEAVY_COMPUTE_READY is not claimed.
