"""Deterministic lexical reference baseline for task-tool relevance.

This baseline is intentionally simple and is NOT a reproduction of the SLM,
SFT, or GRPO methods reported in arXiv:2610.03213. It exists to exercise the
ReproForge capability contract and provide a transparent reference floor.
"""

from __future__ import annotations

import re
from typing import Any

TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")
STOPWORDS = {
    "a",
    "an",
    "and",
    "for",
    "from",
    "in",
    "of",
    "on",
    "the",
    "to",
    "with",
}


def _tokens(text: str) -> set[str]:
    return {
        token.lower()
        for token in TOKEN_RE.findall(text)
        if token.lower() not in STOPWORDS and len(token) > 1
    }


def classify(
    task: str,
    tool_name: str,
    tool_description: str,
    *,
    threshold: float = 0.2,
) -> dict[str, Any]:
    """Score lexical overlap between a task and a candidate tool.

    The score is overlap / task-token-count. This is a deliberately weak,
    deterministic reference baseline rather than a semantic model.
    """
    task_tokens = _tokens(task)
    tool_tokens = _tokens(f"{tool_name} {tool_description}")
    if not task_tokens:
        score = 0.0
    else:
        score = len(task_tokens & tool_tokens) / len(task_tokens)
    return {
        "relevance_score": round(score, 6),
        "relevant": score >= threshold,
        "method": "lexical-overlap-reference-v1",
    }
