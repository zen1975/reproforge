# arXiv:2610.22061 — FAOPs: Normal Forms and an Algebra for AI Agent Workflows

## Study boundary

This study implements a small, independent static verifier for a declared workflow IR inspired by the paper's normal-form contracts. It is not the author's SkillBase compiler, does not execute tools, does not translate prose into FAOP syntax, and does not prove that declarations match runtime behavior.

The primary source and the 28-page PDF were reviewed. The paper is theory-first and explicitly defers a full empirical study; therefore the ReproForge reproduction status remains PARTIAL.

## Implemented mechanism

The verifier checks FNF-1 atomic leaves, FNF-2 dataflow availability, FNF-3 unique and acyclic procedure calls, FNF-4 least-privilege tool scope, and optional loop and time/cost bounds. The implementation deliberately omits an FAOP parser, optimizer, proof engine, full type system, dead-branch solver, and runtime enforcement.

## Run

From the repository root:

    python studies/arxiv-2610.22061/experiments/run_static_verifier.py
    python -m pytest -q tests/test_faop_static_verifier.py
    reproforge validate studies/arxiv-2610.22061/manifest.yaml
    reproforge study-status studies/arxiv-2610.22061

The frozen fixture is in fixtures/faop_static_v2.json. Do not tune against this frozen evaluation; create a new version for changed fixtures or acceptance criteria.

## Evidence summary

The synthetic mechanism runner reports 14/14 expected case outcomes. The suite contains two valid workflows and twelve negative/boundary cases. The deliberately weak shape-only baseline accepts all 14 cases and falsely accepts all 12 invalid fixtures. This baseline is only a contrast for structural checking, not a paper benchmark or a competitive static-analysis baseline.
