"""Deterministic tier-aware trajectory budget allocation.

Independent implementation of the reusable allocation idea described in
arXiv:2610.03315. This module is not a reproduction of the full LiteTrajEval
system and does not include an LLM judge.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

_STATUS_ORDER = ("ok", "warning", "error")
_DEFAULT_FLOORS = {"ok": 120, "warning": 240, "error": 480}


def allocate_budgets(
    lengths: Sequence[int],
    statuses: Sequence[str],
    budget: int,
    floors: Mapping[str, int] | None = None,
) -> list[int]:
    """Allocate a fixed output budget while protecting higher-status evidence.

    Reduction proceeds from ok -> warning -> error. Within each tier, the
    currently longest reducible allocations are shortened evenly toward the
    next length level or the configured floor.
    """
    if len(lengths) != len(statuses):
        raise ValueError("lengths and statuses must have equal size")
    if budget < 0:
        raise ValueError("budget must be non-negative")
    if any(length < 0 for length in lengths):
        raise ValueError("lengths must be non-negative")
    if any(status not in _STATUS_ORDER for status in statuses):
        raise ValueError("unsupported status")

    limits = dict(_DEFAULT_FLOORS)
    if floors is not None:
        limits.update(floors)
    if any(limits[status] < 0 for status in _STATUS_ORDER):
        raise ValueError("floors must be non-negative")

    allocations = list(lengths)
    minimums = [
        min(length, limits[status])
        for length, status in zip(lengths, statuses, strict=True)
    ]

    if sum(allocations) <= budget:
        return allocations

    for tier in _STATUS_ORDER:
        while sum(allocations) > budget:
            candidates = [
                i
                for i, status in enumerate(statuses)
                if status == tier and allocations[i] > minimums[i]
            ]
            if not candidates:
                break

            longest = max(allocations[i] for i in candidates)
            group = [i for i in candidates if allocations[i] == longest]
            lower_levels = [allocations[i] for i in candidates if allocations[i] < longest]
            next_level = max(lower_levels, default=0)

            target = max(max(minimums[i] for i in group), next_level)
            reducible = sum(allocations[i] - max(minimums[i], target) for i in group)
            excess = sum(allocations) - budget

            if reducible <= 0:
                for i in group:
                    allocations[i] = max(minimums[i], allocations[i] - 1)
                continue

            reduction = min(excess, reducible)
            per_item, remainder = divmod(reduction, len(group))
            for position, i in enumerate(group):
                delta = per_item + (1 if position < remainder else 0)
                allocations[i] = max(minimums[i], allocations[i] - delta)

    if sum(allocations) > budget:
        excess = sum(allocations) - budget
        for tier in _STATUS_ORDER:
            for i, status in enumerate(statuses):
                if status != tier or excess <= 0:
                    continue
                reducible = allocations[i]
                delta = min(reducible, excess)
                allocations[i] -= delta
                excess -= delta

    return allocations
