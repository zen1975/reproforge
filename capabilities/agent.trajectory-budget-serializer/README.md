# Trajectory Budget Serializer

Status: `experimental`  
Paper reproduction status: `NOT_RUN`

This is an independently written deterministic kernel inspired by the tier-based waterfall allocation described in arXiv:2610.03315.

It is deliberately narrower than LiteTrajEval. It does **not** implement the paper's offline rule synthesis, trajectory normalization, failure-region hinting, MMR evidence selection, or rubric-guided LLM judge.

The kernel takes per-step compacted output lengths, step statuses (`ok`, `warning`, `error`), a global output budget, and tier floors. It first preserves configured minimums, then reduces lower-priority tiers before higher-priority tiers, always reducing the longest reducible allocations first.

Promotion to `verified` requires benchmark-level reproduction evidence, not merely passing unit tests.
