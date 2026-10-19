"""Independent HDA-style score attribution for bounded, already-scored task arrays.

This implements the published arithmetic and a clearly-labelled local bootstrap analogue.
It does not implement the paper's agentic shortcut-detection or harness neutralization steps.
"""
from __future__ import annotations

import math
import random
from typing import Iterable


def _scores(values: Iterable[float], name: str) -> list[float]:
    out = [float(value) for value in values]
    if not out:
        raise ValueError(f"{name} must not be empty")
    if any(not math.isfinite(value) for value in out):
        raise ValueError(f"{name} must contain only finite scores")
    return out


def mean(values: Iterable[float]) -> float:
    xs = list(values)
    if not xs:
        raise ValueError("cannot average an empty sequence")
    return sum(xs) / len(xs)


def paired_bootstrap_ci(
    baseline: Iterable[float],
    evolved: Iterable[float],
    *,
    resamples: int = 2_000,
    seed: int = 20_261_020,
    alpha: float = 0.05,
) -> dict:
    """Percentile CI for paired mean gain; resample count/seed are local analogue settings."""
    base = _scores(baseline, "baseline")
    evo = _scores(evolved, "evolved")
    if len(base) != len(evo):
        raise ValueError("paired score arrays must have equal lengths")
    if resamples < 100:
        raise ValueError("resamples must be >= 100 for this local analogue")
    if not 0 < alpha < 1:
        raise ValueError("alpha must be between 0 and 1")

    differences = [e - b for b, e in zip(base, evo, strict=True)]
    observed = mean(differences)
    rng = random.Random(seed)
    n = len(differences)
    estimates = [mean(rng.choices(differences, k=n)) for _ in range(resamples)]
    estimates.sort()
    lower_index = max(0, math.floor((alpha / 2) * (resamples - 1)))
    upper_index = min(resamples - 1, math.ceil((1 - alpha / 2) * (resamples - 1)))
    lower = estimates[lower_index]
    upper = estimates[upper_index]
    return {
        "observed_gain": observed,
        "ci_lower": lower,
        "ci_upper": upper,
        "alpha": alpha,
        "resamples": resamples,
        "seed": seed,
        "significant_positive_gain": lower > 0,
        "method": "paired_percentile_bootstrap_local_analogue",
    }


def attribute_gains(
    baseline: Iterable[float],
    compute_matched_baseline: Iterable[float],
    evolved: Iterable[float],
    neutralized_evolved: Iterable[float],
    *,
    significant_positive_gain: bool,
) -> dict:
    """Compute HDA's T/O/G score components and bounded reporting shares."""
    arrays = {
        "baseline": _scores(baseline, "baseline"),
        "compute_matched_baseline": _scores(compute_matched_baseline, "compute_matched_baseline"),
        "evolved": _scores(evolved, "evolved"),
        "neutralized_evolved": _scores(neutralized_evolved, "neutralized_evolved"),
    }
    lengths = {len(values) for values in arrays.values()}
    if len(lengths) != 1:
        raise ValueError("all four score arrays must have equal lengths")

    scores = {name: mean(values) for name, values in arrays.items()}
    delta = scores["evolved"] - scores["baseline"]
    if not significant_positive_gain or delta <= 0:
        return {
            "status": "WITHIN_NOISE_OR_NO_POSITIVE_GAIN",
            "scores": scores,
            "delta": delta,
            "attribution_assigned": False,
            "reason": (
                "Published protocol withholds attribution unless the search-set gain is "
                "significant; this run also requires a positive observed gain."
            ),
        }

    t = scores["compute_matched_baseline"] - scores["baseline"]
    o = scores["evolved"] - scores["neutralized_evolved"]
    g = scores["neutralized_evolved"] - scores["compute_matched_baseline"]
    if not math.isclose(delta, o + t + g, rel_tol=0.0, abs_tol=1e-12):
        raise ArithmeticError("HDA attribution conservation identity failed")

    raw_o_share = 100 * o / delta
    raw_t_share = 100 * t / delta
    reported_o = min(100.0, max(0.0, raw_o_share))
    reported_t = min(100.0 - reported_o, max(0.0, raw_t_share))
    reported_g = 100.0 - reported_o - reported_t
    return {
        "status": "ATTRIBUTED",
        "scores": scores,
        "delta": delta,
        "raw_components": {
            "O_overfitting": o,
            "T_test_time_scaling": t,
            "G_residual_upper_bound": g,
        },
        "raw_identity_error": delta - (o + t + g),
        "raw_shares_percent": {"O": raw_o_share, "T": raw_t_share, "G": 100 * g / delta},
        "reported_shares_percent": {"O": reported_o, "T": reported_t, "G": reported_g},
        "interpretation": {
            "O": "lower-bound estimate of detected overfitting",
            "T": "gain explained by matched test-time compute",
            "G": "upper bound on generalizable improvement; not proof of transfer",
        },
        "attribution_assigned": True,
    }
