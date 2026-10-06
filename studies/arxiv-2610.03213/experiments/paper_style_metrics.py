"""Paper-style metric evaluator for task-tool relevance predictions."""

from __future__ import annotations

import json
from typing import Iterable


def parse_prediction(text: str):
    try:
        obj = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return None
    if not isinstance(obj, dict) or not isinstance(obj.get("appropriate"), bool):
        return None
    return obj["appropriate"]


def evaluate(labels: Iterable[int], outputs: Iterable[str]):
    labels = list(labels)
    outputs = list(outputs)
    if len(labels) != len(outputs):
        raise ValueError("labels and outputs must have same length")

    tp = tn = fp = fn = failed = 0
    for label, text in zip(labels, outputs, strict=True):
        pred = parse_prediction(text)
        if pred is None:
            failed += 1
            continue
        if pred and label == 1:
            tp += 1
        elif pred and label == 0:
            fp += 1
        elif not pred and label == 1:
            fn += 1
        else:
            tn += 1

    parsed = tp + tn + fp + fn
    total = len(labels)
    accuracy = (tp + tn) / parsed if parsed else 0.0
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "failed_parses": failed,
        "parse_success_rate": parsed / total if total else 0.0,
        "e2e_accuracy": (tp + tn) / total if total else 0.0,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "false_positive_rate": fp / (fp + tn) if fp + tn else 0.0,
        "false_negative_rate": fn / (fn + tp) if fn + tp else 0.0,
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
    }
