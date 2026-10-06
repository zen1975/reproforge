# Candidate Queue

`candidates/` is the screening layer before a paper becomes a full ReproForge study.

A candidate is **not** a reproduced study and must not appear in the capability registry merely because it looks promising.

## Flow

```text
Recent arXiv scan
    ↓
SOURCE_VERIFIED
    ↓
PDF_PROTOCOL_REVIEW
    ↓
LICENSE_ASSET_REVIEW
    ↓
MECHANISM_DESIGN
    ↓
Promote to studies/<study-id>/
```

A candidate should be promoted only after the canonical source identity is confirmed and the paper has enough implementation/evaluation detail to justify a study.

## Priority

- `A+`: unusually reusable + high free/lightweight verification potential.
- `A`: strong reusable capability candidate.
- `A-`: useful but more infrastructure-heavy, expensive, or indirect.
- `B`: worth retaining but not near-term.

Priority is not scientific quality. It is **ReproForge reuse/verification priority**.

## Rules

- Verify arXiv ID/title/date against the canonical arXiv page.
- Do not copy paper-reported metrics into Evidence as reproduced results.
- Do not create a Capability registry entry until a study has actual evidence.
- Unknown license/access status remains unknown until reviewed.
- Prefer candidates whose useful mechanism can be independently tested in the free/lightweight phase.
- Keep rejected/deferred candidates with a reason rather than silently deleting history.

Validate:

```bash
reproforge validate-candidates candidates/queue.yaml
```
