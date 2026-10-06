"""Deterministic evidence-aware stopping gate.

This is a small ReproForge implementation of the harness-level mechanism described
in arXiv:2610.06191. It intentionally contains no model calls and no author code.
"""

from __future__ import annotations


class EvidenceStoppingGate:
    def __init__(self, threshold: int = 5):
        if threshold < 1:
            raise ValueError("threshold must be >= 1")
        self.threshold = threshold
        self.consecutive_useless = 0
        self.fired = False

    def reset(self) -> None:
        self.consecutive_useless = 0
        self.fired = False

    def update(self, judgment: str) -> bool:
        if self.fired:
            return True
        normalized = judgment.strip().upper()
        if normalized == "USELESS":
            self.consecutive_useless += 1
        elif normalized == "USEFUL":
            self.consecutive_useless = 0
        else:
            raise ValueError("judgment must be USEFUL or USELESS")
        if self.consecutive_useless >= self.threshold:
            self.fired = True
        return self.fired


def should_force_answer(judgments: list[str], threshold: int = 5) -> bool:
    gate = EvidenceStoppingGate(threshold=threshold)
    return any(gate.update(judgment) for judgment in judgments)
