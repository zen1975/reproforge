# Continuation handoff — arXiv:2610.32770

## Current state

- Lifecycle: MECHANISM_VERIFIED
- Reproduction status: PARTIAL
- Free/light phase complete: false
- Handoff ready: false (lightweight work remains)

## Completed

- arXiv metadata, v1 TeX e-print and HTML reviewed; paper CC BY 4.0; no author code or data linked.
- Mechanism claims C1-C4 pre-registered (`b6035ac`), run once as `opst-mechanism-v1`, all PASS.
- Finding: the printed skewed-JSD mixture weighting contradicts the paper's own stated limits and bound; the GKD-consistent form satisfies them (`report.md`).

## Frozen evaluations

- `opst-objective-semantics-v1`, `opst-sample-selection-v1` (`fixtures/opst_selection_v1.json`), `opst-ema-loss-semantics-v1`
- Result: `evidence/opst_mechanism_v1.result.json`; Evidence: `evidence/C1..C4.*.evidence.json`
- `tests/test_opst_mechanism.py` fails if the implementation or fixture drifts from the committed evidence hashes.

## Next lightweight work (GitHub Actions CPU, new evaluation id, pre-register first)

Pick one; both use a small instruction model such as `Qwen/Qwen2.5-0.5B-Instruct` with a pinned revision, the GKD-consistent objective, an EMA teacher, and LoRA on CPU.

1. **Wrong-answer robustness contrast (paper Table 4c analogue).** Same generated sample set; replace p in {0, 0.75} of candidate answers with wrong ones; compare SFT-on-z vs OPST-conditioning on a held-out set the generator never saw. Directly tests the "condition, don't imitate" mechanism.
2. **Placebo privileged-information contrast (Table 4b analogue).** Teacher conditioned on full z vs z from another problem on the same topic vs none. Tests whether gains are sample-specific.

Every value the paper does not publish (lr, optimizer, steps, batch, G, T_gen, T_low, max length, LoRA rank, topics) must be recorded as a ReproForge choice in a config file, never as a paper value. Do not use the commented-out lines in the TeX source.

## Local/heavy (outside this repository's GitHub-only scope)

Gemma 4 E2B/E4B (gated) or Qwen3-4B-Base; 7 rounds x 285 samples; lm-evaluation-harness scoring (MMLU 5-shot, others zero-shot, log-likelihood MC without thinking); OOD ARC-Challenge/MATH-500/Winogrande.

## Commands

    python studies/arxiv-2610.32770/experiments/run_opst_mechanism.py
    python -m pytest -q tests/test_opst_mechanism.py
    reproforge study-status studies/arxiv-2610.32770
    make verify

## External prerequisites and secrets

None for the current phase. A 0.5B analogue needs no secret; Gemma 4 needs an authorized HF token kept out of the repository.
