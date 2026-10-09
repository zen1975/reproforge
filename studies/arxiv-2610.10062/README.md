# Study arXiv:2610.10062 — Loud Failures, Quiet Failures

Source: https://arxiv.org/abs/2610.10062 (v1, submitted 2026-10-07).
Intake verified from arXiv abstract, full HTML and eight-page PDF. PDF bears IEEE copyright/reuse restrictions.

## Why selected
Tool faults are common in operational agents. This work separates noticing, replanning, recovery and repetition, and uses clean-run-relative end states rather than conflating baseline competence with recovery.

## Current empirical boundary
An independent scripted synthetic injector was executed locally: 15 trials; 12 injected faults; 9/9 loud detections; 1/3 quiet detections; 12/15 recoveries. Four pytest regression tests passed. These are scripted policy diagnostics and are not paper-model results.

## Missing
Real multi-turn model trajectories, BFCL benchmark, paired clean-run variation, blinded detection coding, task-clustered inference, published model comparisons.
Lifecycle MECHANISM_VERIFIED; reproduction PARTIAL; capability experimental.
