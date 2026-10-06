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


def _metrics(rows, threshold):
    tp = tn = fp = fn = 0
    for row in rows:
        pred = row["score"] >= threshold
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


def _calibrate_threshold(dev_rows):
    scores = sorted({row["score"] for row in dev_rows})
    if not scores:
        return 0.0
    candidates = [scores[0] - 1.0, scores[-1] + 1.0]
    candidates += scores
    candidates += [
        (left + right) / 2 for left, right in zip(scores, scores[1:], strict=False)
    ]
    best = None
    for threshold in candidates:
        metrics = _metrics(dev_rows, threshold)
        key = (metrics["f1"], metrics["accuracy"], -abs(threshold))
        if best is None or key > best[0]:
            best = (key, threshold, metrics)
    assert best is not None
    return best[1]


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
    rows = [
        {
            "id": case["id"],
            "expected_relevant": case["expected_relevant"],
            "score": score,
        }
        for case, score in zip(data["cases"], scores, strict=True)
    ]

    fixed_threshold = 0.0
    fixed_metrics = _metrics(rows, fixed_threshold)

    dev_rows = rows[:16]
    test_rows = rows[16:]
    calibrated_threshold = _calibrate_threshold(dev_rows)
    dev_metrics = _metrics(dev_rows, calibrated_threshold)
    test_metrics = _metrics(test_rows, calibrated_threshold)

    for row in rows:
        row["predicted_relevant_fixed_0"] = row["score"] >= fixed_threshold
        row["split"] = "dev" if row in dev_rows else "test"
        row["predicted_relevant_calibrated"] = row["score"] >= calibrated_threshold

    return {
        "benchmark_id": data["benchmark_id"],
        "model_id": MODEL_ID,
        "case_count": len(rows),
        "fixed_threshold_baseline": {
            "threshold": fixed_threshold,
            "metrics": fixed_metrics,
        },
        "calibrated_split": {
            "dev_count": len(dev_rows),
            "test_count": len(test_rows),
            "threshold": calibrated_threshold,
            "dev_metrics": dev_metrics,
            "test_metrics": test_metrics,
        },
        "paper_operational_target": {"accuracy": 0.95, "f1": 0.95},
        "test_meets_paper_operational_target": (
            test_metrics["accuracy"] >= 0.95 and test_metrics["f1"] >= 0.95
        ),
        "rows": rows,
        "notes": (
            "Independent off-the-shelf semantic relevance baseline. The first 16 cases "
            "are used only to choose a scalar decision threshold; the final 16 cases are "
            "held out for test scoring. No model weights are tuned. This is not a "
            "reproduction of the paper's Gemma 3 / GEPA / SFT / GRPO results."
        ),
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
