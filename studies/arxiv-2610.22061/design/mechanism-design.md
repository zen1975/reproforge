# Independent FAOP-like verifier — mechanism design

## Source-derived contract

The paper defines four progressive normal forms: atomic leaves (FNF-1), explicit dataflow/type checks (FNF-2), canonical procedure factoring with an acyclic call graph (FNF-3), and least-privilege scope confinement (FNF-4). It separately describes verified termination (+V) and time/cost bounds (+B). The paper states that its theory/toolchain demonstration is theory-first and defers a full empirical study.

## Independent subset

Input is a list of registry records. Each record declares id, inputs, outputs, scope, and steps. Supported node kinds are action, value, call, interrupt, checkpoint, if, and loop. This is a small, explicitly documented IR rather than a parser for the paper's full grammar.

| Check | Mechanism | Intentionally not claimed |
|---|---|---|
| FNF-1 | Leaf effect cardinality; value leaves cannot declare effects | Truth of effect labels against code |
| FNF-2 | Read-before-produce; branch guaranteed-output intersection; loop outputs not propagated | Full type unification, SAT reachability, proof of output contract |
| FNF-3 | Unique ids, resolved calls, DFS cycle detection | Full registry impact analysis or normalization |
| FNF-4 | Tool membership and callee-scope subset checks | Enforcement by a real executor |
| +V | Optional positive integer loop cap | Proof that a loop terminates for the intended semantic reason |
| +B | Optional non-negative numeric time/cost declarations | Measured or enforced runtime bounds |

## Evaluation protocol

The fixed evaluation faop-static-verifier-synthetic-v2 has 14 cases: two valid workflows and twelve invalid or boundary cases. Expected codes are recorded before running the verifier. The shape-only baseline checks only required top-level fields and intentionally represents a minimal structural baseline. It is not intended as a strong competing analyzer.

The test suite and evidence are frozen. Any changes to implementation or expected behavior require a new evaluation identifier and new fixtures; do not retune the frozen evaluation.

## Promotion boundary

The capability remains experimental. Before advancing to PROTOCOL_VERIFIED, add explicit declared-type checks, call-frame input/output isolation, procedure output guarantees, and at least one semantics-preserving rewrite with before/after trace equivalence. HEAVY_COMPUTE_READY is not appropriate while lightweight protocol work remains.
