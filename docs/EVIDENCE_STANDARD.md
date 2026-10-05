# Evidence Standard v0.1

A ReproForge result should be auditable without trusting a narrative summary alone.

Minimum evidence for a completed run:

- manifest hash,
- reproduction-spec hash when used,
- source revision or implementation identifier,
- environment record,
- declared random seed(s),
- configuration hash,
- input/provenance references,
- raw or recomputable metrics,
- output artifact hashes,
- claim-level verdicts,
- explanation for PARTIAL, FAIL, or INCONCLUSIVE outcomes.

Evidence files are append-oriented. Corrections should produce a new run/evidence record rather than rewriting historical raw evidence.
