"""Lightweight trajectory summary metrics for arXiv:2610.06191."""

from __future__ import annotations

import statistics
from collections.abc import Iterable, Mapping, Sequence

MEAN6_REGIMES = (
    "persistent",
    "recover_after_1",
    "recover_after_2",
    "recover_after_3",
    "late_onset_from_3",
    "clean",
)


def _useless_runs(judgments: Sequence[str | None], n: int) -> list[int]:
    run = 0
    out = []
    for index in range(n):
        judgment = judgments[index] if index < len(judgments) else None
        run = run + 1 if judgment == "USELESS" else 0
        out.append(run)
    return out


def answer_rate_after_run(trajectories: Iterable[Mapping], k: int = 5) -> dict:
    """Rate of final-answer actions after a trajectory reaches k useless judgments."""
    if k < 1:
        raise ValueError("k must be >= 1")
    reached = 0
    answered = 0
    for trajectory in trajectories:
        actions = trajectory["actions"]
        judgments = trajectory["judgments"]
        last = min(len(actions) - 1, len(judgments))
        runs = _useless_runs(judgments, last)
        if max(runs, default=0) >= k:
            reached += 1
            answered += bool(actions) and actions[-1] == "finish"
    return {
        "reached": reached,
        "answered": answered,
        "rate": answered / reached if reached else float("nan"),
    }


def mean6_success(episodes: Iterable[Mapping]) -> float:
    """Equal-weight per-question success over the six paper regimes."""
    by_question: dict[str, dict[str, bool]] = {}
    for episode in episodes:
        by_question.setdefault(str(episode["question_id"]), {})[
            str(episode["regime"])
        ] = bool(episode["success"])
    complete = [
        values
        for values in by_question.values()
        if all(regime in values for regime in MEAN6_REGIMES)
    ]
    if not complete:
        return float("nan")
    return statistics.mean(
        sum(bool(values[regime]) for regime in MEAN6_REGIMES) / 6
        for values in complete
    )
