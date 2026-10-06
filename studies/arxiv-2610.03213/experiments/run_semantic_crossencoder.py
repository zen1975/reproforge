"""Evaluate a lightweight semantic CrossEncoder on the first study benchmark.

This is an independent baseline using an off-the-shelf relevance model. It is
not the Gemma 3 / GEPA / SFT / GRPO setup reported in arXiv:2610.03213.
"""

from __future__ import annotations

import json
from pathlib import Path

from sentence_transformers import CrossEncoder

ROOT = Path(__file__).resolve().parents[3]
STUDY = ROOT / "studies" / "arxiv-2610.03213"
MODEL_ID = "cross-encoder/ms-marco-MiniLM-L6-v2"
THRESHOLD = 0.0


def _metrics(rows):
    tp = tn = fp = fn = 0
    for row in rows:
        pred = row["score"] >= THRESHOLD
        expected = row["expected_relevant"]
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
    return {
        "accuracy": (tp + tn) / n,
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


def run():
    data = json.loads(
        (STUDY / "experiments" / "task_tool_synthetic_hard_v1.json").read_text()
    )
    model = CrossEncoder(MODEL_ID)
    pairs = [
        [case["task"], f'{case["tool_name"]}: {case["tool_description"]}']
        for case in data["cases"]
    ]
    scores = [float(x) for x in model.predict(pairs, show_progress_bar=False)]
    rows = []
    for case, score in zip(data["cases"], scores, strict=True):
        rows.append(
            {
                "id": case["id"],
                "expected_relevant": case["expected_relevant"],
                "score": score,
                "predicted_relevant": score >= THRESHOLD,
            }
        )
    metrics = _metrics(rows)
    return {
        "benchmark_id": data["benchmark_id"],
        "model_id": MODEL_ID,
        "threshold": THRESHOLD,
        "case_count": len(rows),
        "metrics": metrics,
        "paper_operational_target": {"accuracy": 0.95, "f1": 0.95},
        "meets_paper_operational_target": (
            metrics["accuracy"] >= 0.95 and metrics["f1"] >= 0.95
        ),
        "rows": rows,
        "notes": (
            "Independent off-the-shelf semantic relevance baseline. No threshold tuning "
            "was performed on this benchmark; the fixed decision threshold is 0.0. "
            "This is not a reproduction of the paper's Gemma 3 / GEPA / SFT / GRPO results."
        ),
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
