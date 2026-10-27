# Continuation handoff — arXiv:2610.22466

## Current state

- Lifecycle: MECHANISM_VERIFIED
- Reproduction status: PARTIAL
- Free/light phase complete: false
- Handoff ready: false

Lightweight protocol work remains; this is not a heavy-compute handoff.

## Completed

- arXiv identity, full PDF and CC BY 4.0 paper license verified (2026-10-20);
- independent HDA score arithmetic and local paired-bootstrap analogue implemented;
- frozen synthetic evaluation `hda-synthetic-v1` run; result and Evidence JSON saved;
- experimental capability `research.harness-delta-attribution-auditor` registered.

## Frozen evaluation

- Fixture: `studies/arxiv-2610.22466/fixtures/hda_synthetic_v1.json`
- Result: `studies/arxiv-2610.22466/evidence/hda_synthetic_v1.result.json`
- Evidence: `studies/arxiv-2610.22466/evidence/C1.synthetic-attribution.evidence.json`, `C2.no-gain-guard.evidence.json`

## Next lightweight work

1. Identify an independently licensed small benchmark or trace set; record its license before use.
2. Build baseline / compute-matched baseline / evolved / neutralized score vectors from actual runs on it, under a new evaluation id.
3. Preserve raw per-item scores so the paired bootstrap can be re-run.

## Commands

    python studies/arxiv-2610.22466/experiments/run_hda_synthetic.py
    python -m pytest -q tests/test_hda_attribution.py
    reproforge study-status studies/arxiv-2610.22466
    make verify

## External prerequisites and secrets

None for the current mechanism test.

## Known unknowns

- Raw per-item logs and full trajectories are not in the inspected author repository.
- Compute-matching and shortcut-neutralization construction is task-specific and partly human-reviewed in the paper.
