"""Paper intake identity/provenance gate."""

from __future__ import annotations

from typing import Any


def validate_intake_identity(manifest: dict[str, Any], source: dict[str, Any]) -> dict[str, Any]:
    """Compare a study manifest against captured source metadata.

    Identity may match while authority remains unverified. A study can only be
    marked VERIFIED when its captured source is explicitly authoritative.
    """
    errors: list[str] = []
    paper = manifest.get("paper", {})

    checks = {
        "arxiv_id": paper.get("arxiv_id") == source.get("arxiv_id"),
        "title": paper.get("title") == source.get("title"),
        "authors": paper.get("authors") == source.get("authors"),
        "canonical_url": paper.get("canonical_url") == source.get("canonical_url"),
    }
    for field, ok in checks.items():
        if not ok:
            errors.append(f"{field} mismatch")

    if not source.get("abstract"):
        errors.append("source abstract missing")

    authoritative = bool(source.get("authoritative"))
    if errors:
        status = "REJECTED"
    elif authoritative:
        status = "VERIFIED"
    else:
        status = "IDENTITY_MATCHED_SOURCE_UNVERIFIED"

    return {
        "status": status,
        "authoritative": authoritative,
        "checks": checks,
        "errors": errors,
    }
