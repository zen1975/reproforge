"""Run the independent hard synthetic task-tool relevance benchmark."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
STUDY = ROOT / "studies" / "arxiv-2610.03213"
CAPABILITY = ROOT / "capabilities" / "agent.task-tool-relevance-classifier"


def _load_classifier():
    path = CAPABILITY / "classifier.py"
    spec = importlib.util.spec_from_file_location("task_tool_classifier", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load classifier")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.classify


def run():
    classify = _load_classifier()
    data = json.loads(
        (STUDY / "experiments" / "task_tool_synthetic_hard_v1.json").read_text()
    )
    tp = tn = fp = fn = 0
    for case in data["cases"]:
        pred = classify(
            case["task"], case["tool_name"], case["tool_description"]
        )["relevant"]
        expected = case["expected_relevant"]
        if pred and expected:
            tp += 1
        elif pred and not expected:
            fp += 1
        elif not pred and expected:
            fn += 1
        else:
            tn += 1

    n = tp + tn + fp + fn
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    accuracy = (tp + tn) / n
    fpr = fp / (fp + tn) if fp + tn else 0.0
    fnr = fn / (fn + tp) if fn + tp else 0.0
    return {
        "benchmark_id": data["benchmark_id"],
        "case_count": n,
        "positive_count": tp + fn,
        "negative_count": tn + fp,
        "lexical_overlap_reference_v1": {
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "false_positive_rate": fpr,
            "false_negative_rate": fnr,
            "tp": tp,
            "tn": tn,
            "fp": fp,
            "fn": fn,
        },
        "paper_operational_target": {"accuracy": 0.95, "f1": 0.95},
        "meets_paper_operational_target": accuracy >= 0.95 and f1 >= 0.95,
        "interpretation": (
            "The deterministic lexical baseline is reproducible but fails the paper's "
            "95% accuracy/F1 operational target on this independent hard synthetic benchmark. "
            "This supports the need for semantic model-based specialization but does not "
            "reproduce the paper's Gemma/GEPA/SFT/GRPO results."
        ),
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
