"""Decision-preserving span selector derived independently from FOCUS Algorithm 1.

The selector consumes already-generated plan dependency sets and defensive rescue
decisions. Draft-model generation is intentionally outside this deterministic core.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence


@dataclass(frozen=True)
class Span:
    id: str
    reasoning: str
    action: str
    observation: str


@dataclass(frozen=True)
class CompressionResult:
    retained_ids: tuple[str, ...]
    dropped_ids: tuple[str, ...]
    utility: dict[str, float]
    utility_retained_ids: tuple[str, ...]
    rescued_ids: tuple[str, ...]


def estimate_utility(
    span_ids: Sequence[str],
    rollout_dependencies: Sequence[Iterable[str]],
) -> dict[str, float]:
    if not rollout_dependencies:
        raise ValueError("at least one rollout is required")
    known = set(span_ids)
    counts = {span_id: 0 for span_id in span_ids}
    for dependencies in rollout_dependencies:
        cited = set(dependencies)
        unknown = cited - known
        if unknown:
            raise ValueError(f"unknown span ids in rollout: {sorted(unknown)}")
        for span_id in cited:
            counts[span_id] += 1
    n = len(rollout_dependencies)
    return {span_id: counts[span_id] / n for span_id in span_ids}


def compress(
    spans: Sequence[Span],
    rollout_dependencies: Sequence[Iterable[str]],
    *,
    tau: float = 0.3,
    rescued_ids: Iterable[str] = (),
) -> CompressionResult:
    if not 0.0 <= tau <= 1.0:
        raise ValueError("tau must be in [0, 1]")
    ids = [span.id for span in spans]
    if len(ids) != len(set(ids)):
        raise ValueError("span ids must be unique")

    utility = estimate_utility(ids, rollout_dependencies)
    utility_keep = {span_id for span_id, score in utility.items() if score >= tau}

    rescue = set(rescued_ids)
    unknown_rescue = rescue - set(ids)
    if unknown_rescue:
        raise ValueError(f"unknown rescued span ids: {sorted(unknown_rescue)}")

    keep = utility_keep | rescue
    retained = tuple(span_id for span_id in ids if span_id in keep)
    dropped = tuple(span_id for span_id in ids if span_id not in keep)
    return CompressionResult(
        retained_ids=retained,
        dropped_ids=dropped,
        utility=utility,
        utility_retained_ids=tuple(span_id for span_id in ids if span_id in utility_keep),
        rescued_ids=tuple(span_id for span_id in ids if span_id in rescue),
    )
