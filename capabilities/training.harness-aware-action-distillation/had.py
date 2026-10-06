"""Harness-Aware Distillation primitives from arXiv:2610.02858.

Independent implementation of the published mechanism. This module constructs
harness-aware action preferences and conservative validity masks without requiring
task rewards or future information.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import exp, log
from typing import Iterable


@dataclass(frozen=True)
class HarnessRecord:
    admissible_actions: frozenset[str]
    held_objects: frozenset[str]
    no_effect_actions: frozenset[str]


@dataclass(frozen=True)
class PreferenceRecord:
    positive_action: str
    negative_action: str
    valid_positive: bool
    active_contrast: bool


def _extract_object(action: str) -> str | None:
    # Minimal transport-neutral convention for deterministic mechanism tests:
    # actions may encode object use as "... object=<name>".
    marker = "object="
    if marker not in action:
        return None
    value = action.split(marker, 1)[1].split()[0].strip(" ,;")
    return value or None


def is_valid_positive(action: str, harness: HarnessRecord) -> bool:
    if action not in harness.admissible_actions:
        return False
    obj = _extract_object(action)
    if obj is not None and obj not in harness.held_objects:
        return False
    if action in harness.no_effect_actions:
        return False
    return True


def build_preference(
    *,
    teacher_with_harness_action: str,
    teacher_without_harness_action: str,
    harness: HarnessRecord,
) -> PreferenceRecord:
    return PreferenceRecord(
        positive_action=teacher_with_harness_action,
        negative_action=teacher_without_harness_action,
        valid_positive=is_valid_positive(teacher_with_harness_action, harness),
        active_contrast=teacher_with_harness_action != teacher_without_harness_action,
    )


def mean_logprob(token_logprobs: Iterable[float]) -> float:
    values = tuple(float(v) for v in token_logprobs)
    if not values:
        raise ValueError("action token logprobs must be non-empty")
    return sum(values) / len(values)


def action_margin(
    positive_action_token_logprobs: Iterable[float],
    negative_action_token_logprobs: Iterable[float],
) -> float:
    return (
        mean_logprob(positive_action_token_logprobs)
        - mean_logprob(negative_action_token_logprobs)
    )


def preference_loss(delta: float, beta: float = 0.5) -> float:
    if beta <= 0:
        raise ValueError("beta must be > 0")
    # -log(sigmoid(beta * delta)), stable for this lightweight range.
    x = beta * float(delta)
    if x >= 0:
        return log(1.0 + exp(-x))
    return -x + log(1.0 + exp(x))


def masked_preference_loss(
    record: PreferenceRecord,
    *,
    positive_action_token_logprobs: Iterable[float],
    negative_action_token_logprobs: Iterable[float],
    beta: float = 0.5,
) -> float:
    if not record.valid_positive or not record.active_contrast:
        return 0.0
    return preference_loss(
        action_margin(
            positive_action_token_logprobs,
            negative_action_token_logprobs,
        ),
        beta=beta,
    )


def gradient_balance_lambda(
    distillation_grad_norm: float,
    preference_grad_norm: float,
    rho: float = 0.5,
) -> float:
    if distillation_grad_norm < 0 or preference_grad_norm < 0:
        raise ValueError("gradient norms must be non-negative")
    if rho < 0:
        raise ValueError("rho must be non-negative")
    if preference_grad_norm == 0:
        return 0.0
    return rho * distillation_grad_norm / preference_grad_norm
