"""FOCUS paper evaluation metrics that do not require model inference."""

from __future__ import annotations

from collections.abc import Sequence


def peak_tokens(input_tokens: Sequence[int]) -> int:
    if not input_tokens:
        return 0
    if any(value < 0 for value in input_tokens):
        raise ValueError("token counts must be non-negative")
    return max(input_tokens)


def dependency_cost(
    input_tokens: Sequence[int],
    output_tokens: Sequence[int],
) -> float:
    """Paper dependency metric: sum_t ((n_i + 2*n_o) * n_o) / 2."""
    if len(input_tokens) != len(output_tokens):
        raise ValueError("input/output token sequences must have equal length")
    if any(value < 0 for value in input_tokens) or any(value < 0 for value in output_tokens):
        raise ValueError("token counts must be non-negative")
    return sum(
        ((n_i + 2 * n_o) * n_o) / 2
        for n_i, n_o in zip(input_tokens, output_tokens, strict=True)
    )


def cumulative_tokens(
    input_tokens: Sequence[int],
    output_tokens: Sequence[int],
) -> int:
    if len(input_tokens) != len(output_tokens):
        raise ValueError("input/output token sequences must have equal length")
    return sum(input_tokens) + sum(output_tokens)
