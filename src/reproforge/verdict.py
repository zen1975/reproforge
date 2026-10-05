"""Claim-level reproduction verdicts."""

from __future__ import annotations

from enum import StrEnum


class Verdict(StrEnum):
    PASS = "PASS"
    PARTIAL = "PARTIAL"
    FAIL = "FAIL"
    INCONCLUSIVE = "INCONCLUSIVE"


def aggregate_verdict(verdicts: list[Verdict]) -> Verdict:
    """Aggregate claim verdicts conservatively.

    FAIL dominates. INCONCLUSIVE blocks PASS. PARTIAL dominates a mixture of
    PASS and PARTIAL. An empty result is INCONCLUSIVE.
    """
    if not verdicts:
        return Verdict.INCONCLUSIVE
    if Verdict.FAIL in verdicts:
        return Verdict.FAIL
    if Verdict.INCONCLUSIVE in verdicts:
        return Verdict.INCONCLUSIVE
    if Verdict.PARTIAL in verdicts:
        return Verdict.PARTIAL
    return Verdict.PASS
