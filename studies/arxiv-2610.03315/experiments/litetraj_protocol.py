"""Lightweight protocol reconstruction for arXiv:2610.03315.

This module implements the paper-described evaluation shape without claiming
paper-benchmark reproduction. Similarity is injected; the synthetic fixture
uses Jaccard as an explicitly independent analogue because the paper does not
fully specify the embedding/similarity implementation used for MMR.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Sequence


def token_set(text: str) -> frozenset[str]:
    return frozenset(part for part in text.lower().split() if part)


def jaccard(a: str, b: str) -> float:
    left, right = token_set(a), token_set(b)
    if not left and not right:
        return 1.0
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def mmr_select(
    units: Sequence[str],
    anchor: str,
    limit: int,
    *,
    lam: float = 0.5,
    similarity: Callable[[str, str], float] = jaccard,
) -> list[str]:
    """Select evidence with relevance/redundancy tradeoff."""
    if not 0.0 <= lam <= 1.0:
        raise ValueError("lam must be in [0, 1]")
    if limit < 0:
        raise ValueError("limit must be non-negative")

    remaining = list(units)
    selected: list[str] = []
    while remaining and len(selected) < limit:
        scored = []
        for index, unit in enumerate(remaining):
            relevance = similarity(unit, anchor)
            redundancy = max((similarity(unit, other) for other in selected), default=0.0)
            score = lam * relevance - (1.0 - lam) * redundancy
            scored.append((score, -index, unit))
        _, _, chosen = max(scored)
        selected.append(chosen)
        remaining.remove(chosen)
    return selected


@dataclass(frozen=True)
class FailureGroup:
    steps: tuple[int, ...]


def detection_rate(predictions: Sequence[Sequence[int]]) -> float:
    if not predictions:
        return 0.0
    return sum(bool(row) for row in predictions) / len(predictions)


def alignment_detected(
    predictions: Sequence[Sequence[int]],
    references: Sequence[Sequence[FailureGroup]],
    tolerance: int,
) -> float:
    """Paper-style group-level alignment conditional on detected samples."""
    if len(predictions) != len(references):
        raise ValueError("predictions/references length mismatch")
    if tolerance < 0:
        raise ValueError("tolerance must be non-negative")

    matched = 0
    total = 0
    for predicted, groups in zip(predictions, references, strict=True):
        if not predicted:
            continue
        total += len(groups)
        for group in groups:
            if any(
                abs(pred - truth) <= tolerance
                for pred in predicted
                for truth in group.steps
            ):
                matched += 1
    return matched / total if total else 0.0


def build_single_call_payload(
    task: str,
    final_output: str,
    serialized_steps: Sequence[dict[str, object]],
    candidate_regions: Sequence[dict[str, object]],
) -> dict[str, object]:
    """Construct one judge input containing trajectory plus weak guidance."""
    return {
        "task": {"input": task, "final_output": final_output},
        "steps": list(serialized_steps),
        "trajectory_hint": {"candidate_regions": list(candidate_regions)},
        "judge_contract": {
            "single_call": True,
            "required_fields": [
                "rubric_scores",
                "failure_categories",
                "failure_steps",
                "root_cause",
                "key_observations",
            ],
        },
    }


_REQUIRED_REPORT_FIELDS = {
    "rubric_scores",
    "failure_categories",
    "failure_steps",
    "root_cause",
    "key_observations",
}


def validate_judge_report(report: dict[str, object]) -> None:
    """Validate the one-call structured diagnostic report contract."""
    missing = _REQUIRED_REPORT_FIELDS - set(report)
    if missing:
        raise ValueError("missing judge report fields: " + ", ".join(sorted(missing)))
    if not isinstance(report["failure_steps"], list):
        raise ValueError("failure_steps must be a list")
    if not isinstance(report["failure_categories"], list):
        raise ValueError("failure_categories must be a list")
    if not isinstance(report["rubric_scores"], dict):
        raise ValueError("rubric_scores must be an object")
    if not isinstance(report["root_cause"], str):
        raise ValueError("root_cause must be text")
    if not isinstance(report["key_observations"], list):
        raise ValueError("key_observations must be a list")
