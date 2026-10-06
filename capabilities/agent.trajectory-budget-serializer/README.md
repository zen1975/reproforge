# Trajectory Budget Serializer

Status: `experimental`  
Paper reproduction status: `PARTIAL`

This is an independently written deterministic kernel inspired by the tier-based waterfall allocation described in arXiv:2610.03315.

It is deliberately narrower than LiteTrajEval. It does **not** implement the paper's offline rule synthesis, full trajectory normalization, MMR evidence selection, or rubric-guided LLM judge.

The kernel takes per-step compacted output lengths, step statuses (`ok`, `warning`, `error`), a global output budget, and tier floors. It first preserves configured minimums, then reduces lower-priority tiers before higher-priority tiers, always reducing the longest reducible allocations first.

## Independent stress evidence

ReproForge includes a deterministic 10-case synthetic stress benchmark where warning/error steps move progressively later in a 12-step trajectory. With a 3,500-character output budget and uniform 700-character steps:

- tiered waterfall: 100% budget compliance;
- tiered waterfall: 100% full retention of error-step allocation;
- naive head truncation: 30% full retention of error-step allocation;
- mean error-step allocation: 700 characters vs 210 for head truncation (3.33x).

This is deliberately a mechanism test, not the paper benchmark. It demonstrates that the reusable allocation kernel behaves as intended under late-failure pressure. It does not validate the paper's failure-localization, LLM-judge, cost, or runtime claims.

Promotion to `verified` still requires protocol-equivalent benchmark evidence.
