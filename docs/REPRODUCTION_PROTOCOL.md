# Reproduction Protocol v0.1

ReproForge treats a reproduction as a claim-level, evidence-backed study rather than a binary statement that a paper "works".

## 1. Intake

Record the canonical paper reference, authors, source URL, version/date when relevant, and declared paper license. Do not copy full paper text into the repository.

## 2. Asset gate

Declare every external asset before use: code, dataset, model, weights, benchmark, API, and other material dependency. Record provenance, license status, whether redistribution is permitted, and whether the asset will be redistributed.

An `UNKNOWN` or `RESTRICTED` license must never be silently treated as permission to redistribute.

## 3. Claim extraction

Convert the study into discrete claims. Every claim must have a stable identifier, a concise statement, and measurable acceptance criteria defined before the reproduction result is known.

## 4. Implementation classification

Use exactly one classification:

- `INDEPENDENT`: implemented from the research description without copying author code.
- `DERIVED`: implementation incorporates third-party or author code; provenance must be explicit.
- `OFFICIAL_AUDIT`: reproduction primarily executes/audits official implementation.

## 5. Environment freeze

Capture interpreter/runtime versions, operating environment, dependency lock information, hardware-relevant information, seeds, configuration files, and immutable identifiers for external assets where available.

## 6. Execution

Prefer multiple deterministic seeds where stochasticity exists. Preserve raw outputs needed to recompute reported metrics. Do not edit raw evidence after verdict calculation; create a new run instead.

## 7. Evidence

Evidence should include hashes of inputs and outputs, metrics, logs or summaries sufficient to audit the conclusion, and the environment record. Large licensed assets should normally be referenced rather than redistributed.

## 8. Verdicts

- `PASS`: the predefined acceptance criteria are met.
- `PARTIAL`: a meaningful subset is met, or results are materially close but outside the predefined PASS condition.
- `FAIL`: the reproduction provides sufficient evidence that the predefined acceptance criteria are not met under the declared protocol.
- `INCONCLUSIVE`: evidence, compute, data, specification, licensing, or access is insufficient for a defensible conclusion.

A FAIL is not automatically evidence that the original paper is wrong. It is evidence that the declared reproduction did not satisfy the declared criteria.

## 9. Publication

Publish the protocol, code you have rights to publish, structured manifests, environment metadata, and evidence summaries. Clearly distinguish original work from third-party assets and cite the source paper.
