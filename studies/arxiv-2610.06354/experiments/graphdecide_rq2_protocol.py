"""Adapter-neutral RQ2 protocol reconstruction for GraphDecide."""

from __future__ import annotations

from dataclasses import dataclass
import random
from typing import Mapping, Sequence


@dataclass(frozen=True)
class MatchedItem:
    item_id: str
    query: str
    candidates: tuple[str, ...]
    truth: str
    target_text: str
    context_text: tuple[str, ...]
    nodes: tuple[str, ...]
    edges: tuple[tuple[str, str], ...]
    anchors: tuple[tuple[str, str], ...]


def build_condition(item: MatchedItem, condition: str) -> dict[str, object]:
    """Build one matched condition without exposing held-out truth."""
    base = {
        "item_id": item.item_id,
        "query": item.query,
        "candidates": item.candidates,
        "condition": condition,
    }
    if condition == "T":
        base["target_text"] = item.target_text
        base["context_text"] = item.context_text
        base["anchors"] = item.anchors
    elif condition == "G":
        base["nodes"] = item.nodes
        base["edges"] = item.edges
        base["anchors"] = item.anchors
    elif condition == "TG":
        base["target_text"] = item.target_text
        base["context_text"] = item.context_text
        base["nodes"] = item.nodes
        base["edges"] = item.edges
        base["anchors"] = item.anchors
    elif condition == "BAG":
        base["target_text"] = item.target_text
        base["context_text"] = item.context_text
        base["nodes"] = item.nodes
        base["anchors"] = item.anchors
    elif condition in {"A", "A*"}:
        base["anchors"] = item.anchors
    else:
        raise ValueError("unsupported condition")
    return base


def validate_matched_payloads(payloads: Mapping[str, Mapping[str, object]]) -> None:
    ids = {p["item_id"] for p in payloads.values()}
    queries = {p["query"] for p in payloads.values()}
    candidates = {tuple(p["candidates"]) for p in payloads.values()}
    if len(ids) != 1 or len(queries) != 1 or len(candidates) != 1:
        raise ValueError("matched conditions must preserve item/query/candidates")
    if any("truth" in p for p in payloads.values()):
        raise ValueError("held-out truth leaked into model input")
    if "edges" in payloads["BAG"]:
        raise ValueError("BAG must remove explicit edges")
    if "edges" in payloads.get("A", {}) or "target_text" in payloads.get("A", {}):
        raise ValueError("A must not expose entity text or edges")
    if "edges" in payloads.get("A*", {}) or "target_text" in payloads.get("A*", {}):
        raise ValueError("A* must not expose additional entity text or edges")


def score_choice(item: MatchedItem, choice: str | None) -> dict[str, object]:
    supported = choice is not None
    valid = supported and choice in item.candidates
    correct = bool(valid and choice == item.truth)
    return {"supported": supported, "valid": valid, "correct": correct}


def paired_difference(
    left: Sequence[bool],
    right: Sequence[bool],
) -> float:
    if len(left) != len(right) or not left:
        raise ValueError("paired vectors must be non-empty and equal length")
    return 100.0 * sum(int(a) - int(b) for a, b in zip(left, right, strict=True)) / len(left)


def paired_bootstrap_interval(
    left: Sequence[bool],
    right: Sequence[bool],
    *,
    resamples: int = 1000,
    seed: int = 20261001,
    low_index: int = 24,
    high_index: int = 974,
) -> tuple[float, float]:
    """Paper-declared paired target bootstrap convention."""
    if len(left) != len(right) or not left:
        raise ValueError("paired vectors must be non-empty and equal length")
    rng = random.Random(seed)
    n = len(left)
    values = []
    for _ in range(resamples):
        indices = [rng.randrange(n) for _ in range(n)]
        l = [left[i] for i in indices]
        r = [right[i] for i in indices]
        values.append(paired_difference(l, r))
    values.sort()
    if high_index >= len(values):
        raise ValueError("bootstrap endpoint outside sample")
    return values[low_index], values[high_index]


def readout_choice(
    mode: str,
    raw: object,
    candidates: Sequence[str],
) -> str | None:
    """Map alternative model readouts back to the same candidate identity."""
    if mode in {"native_selection", "constrained_generation"}:
        if raw is None:
            return None
        return str(raw)
    if mode == "candidate_scoring":
        if not isinstance(raw, Mapping):
            raise ValueError("candidate_scoring requires a score mapping")
        if any(candidate not in raw for candidate in candidates):
            return None
        return max(candidates, key=lambda candidate: float(raw[candidate]))
    raise ValueError("unsupported readout mode")
