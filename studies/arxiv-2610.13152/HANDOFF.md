# TQS structural trajectory audit — continuation

Lifecycle: MECHANISM_VERIFIED. Reproduction: PARTIAL. Handoff is **not** ready for heavy-compute promotion.

Completed: arXiv ID/title/submission and 17-page PDF reviewed; paper non-exclusive distribution license and author-code MIT license checked; author assets not copied. Independent CPU synthetic experiment and 10 unit tests executed, 6/6 mechanism assertions passed. Same-length step-count baseline ties, structural components separate traces.

Frozen evidence: `tqs-structural-components-synthetic-v1`. Do not tune on the two observed traces; create new unseen fixtures/version.

Run: `python studies/arxiv-2610.13152/experiments/run_structural_audit.py --output studies/arxiv-2610.13152/evidence/tqs_structural_synthetic_v1.result.json` and `python -m unittest discover -s tests -p 'test_trajectory_structure_audit.py' -v`.

Expected: 6 assertions, 10 tests; evidence JSON. No secret needed for current CPU run. External prerequisites for paper-level claims: lawful CoderForge-Preview access, author implementation inspection under MIT if needed, model/weights licenses, 30B-scale SFT compute, SWE-Bench Verified evaluation.

Unknown: exact lexicon/error-pattern matching, data preprocessing, full seven-component scoring equivalence, corpus licensing, training resources. No unpublished choices filled by guesswork.

Promotion: protocol-equivalent implementation with negative/boundary tests, held-out freeze, full Evidence, and CI green. HEAVY_COMPUTE_READY only when lightweight work is exhausted. Paper reproduced only after actual comparable training and evaluation.
