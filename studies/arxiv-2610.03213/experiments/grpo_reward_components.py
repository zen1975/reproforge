"""Deterministic GRPO reward *components* from the paper description.

The paper states the reward combines schema compliance, label correctness, and
an excessive-reasoning penalty, with an extra penalty for invalid outputs.
It does not publish scalar weights. ReproForge therefore exposes components
without inventing a weighted total.
"""

from __future__ import annotations

import json


def reward_components(output: str, expected_label: bool, reasoning_limit_chars: int = 400):
    valid_json = False
    valid_schema = False
    label_correct = False
    reasoning_chars = 0

    try:
        obj = json.loads(output)
        valid_json = isinstance(obj, dict)
    except (json.JSONDecodeError, TypeError):
        obj = None

    if isinstance(obj, dict):
        reasoning = obj.get("reasoning")
        appropriate = obj.get("appropriate")
        valid_schema = isinstance(reasoning, str) and isinstance(appropriate, bool)
        if valid_schema:
            label_correct = appropriate is expected_label
            reasoning_chars = len(reasoning)

    return {
        "schema_compliance": 1 if valid_schema else 0,
        "label_correctness": 1 if label_correct else 0,
        "excessive_reasoning_chars": max(0, reasoning_chars - reasoning_limit_chars),
        "invalid_output": 0 if valid_schema else 1,
        "published_weighted_total_available": False,
    }


def combine_components(*_args, **_kwargs):
    raise RuntimeError(
        "Paper does not publish reward weights; ReproForge will not invent a scalar combination."
    )
