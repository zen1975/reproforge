"""Time-matched stopping contrast for trajectory records.

Derived from the protocol described in arXiv:2610.06191. This implementation is
kept in ReproForge and does not import the authors' package.
"""

from __future__ import annotations

import collections
import random
from collections.abc import Iterable, Mapping, Sequence


def _runs(judgments: Sequence[str | None], n: int) -> dict[int, int]:
    out = {}
    run = 0
    for t in range(1, n + 1):
        judgment = judgments[t - 1] if t <= len(judgments) else None
        run = run + 1 if judgment == "USELESS" else 0
        out[t] = run
    return out


def _decision_points(trajectory: Mapping):
    actions = trajectory["actions"]
    judgments = trajectory["judgments"]
    last = min(len(actions) - 1, len(judgments))
    runs = _runs(judgments, last)
    for t in range(1, last + 1):
        yield t, runs[t], actions[t] == "finish"


def _pooled_risk_difference(rows: list[dict[int, list[int]]]):
    totals = collections.defaultdict(lambda: [0, 0, 0, 0])
    for row in rows:
        for t, values in row.items():
            for i, value in enumerate(values):
                totals[t][i] += value

    numerator = 0.0
    denominator = 0.0
    for t, (answered_all, n_all, answered_mixed, n_mixed) in totals.items():
        if not n_all or not n_mixed:
            continue
        weight = n_all * n_mixed / (n_all + n_mixed)
        risk_difference = answered_all / n_all - answered_mixed / n_mixed
        numerator += weight * risk_difference
        denominator += weight
    value = numerator / denominator if denominator else float("nan")
    return value, {int(k): list(v) for k, v in sorted(totals.items())}


def time_matched_contrast(
    trajectories: Iterable[Mapping],
    *,
    t_min: int = 3,
    t_max: int = 6,
    bootstrap_samples: int = 2000,
    seed: int = 0,
    cluster_key: str = "question_id",
):
    """Compute the paper's time-matched contrast Δ.

    At a fixed decision time t:
      exposure 1 = every observed result so far was judged USELESS;
      exposure 0 = the latest result was USELESS but at least one earlier result was USEFUL.

    The per-time risk differences are pooled using the sample-size weighting
    specified by the paper/toolkit protocol. Percentile intervals bootstrap
    whole question clusters.
    """
    grouped = {}
    for trajectory in trajectories:
        grouped.setdefault(trajectory[cluster_key], []).append(trajectory)

    per_cluster = []
    for group in grouped.values():
        cells = collections.defaultdict(lambda: [0, 0, 0, 0])
        for trajectory in group:
            for t, run, answered in _decision_points(trajectory):
                if not t_min <= t <= t_max:
                    continue
                if run == t:
                    cells[t][0] += int(answered)
                    cells[t][1] += 1
                elif 1 <= run <= t - 2:
                    cells[t][2] += int(answered)
                    cells[t][3] += 1
        per_cluster.append(dict(cells))

    delta, cells = _pooled_risk_difference(per_cluster)

    rng = random.Random(seed)
    bootstrap = []
    if per_cluster:
        for _ in range(bootstrap_samples):
            sampled = [per_cluster[rng.randrange(len(per_cluster))] for _ in per_cluster]
            value, _ = _pooled_risk_difference(sampled)
            if value == value:
                bootstrap.append(value)
    bootstrap.sort()
    if bootstrap:
        low = bootstrap[int(0.025 * len(bootstrap))]
        high = bootstrap[int(0.975 * len(bootstrap)) - 1]
    else:
        low = high = float("nan")

    return {
        "delta": delta,
        "ci_low": low,
        "ci_high": high,
        "cells": cells,
        "n_clusters": len(per_cluster),
        "bootstrap_samples": bootstrap_samples,
        "seed": seed,
    }
