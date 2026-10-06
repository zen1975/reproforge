"""Reproduce the deterministic serializer stress benchmark."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
STUDY = ROOT / "studies" / "arxiv-2610.03315"
CAPABILITY = ROOT / "capabilities" / "agent.trajectory-budget-serializer"


def _load_allocator():
    path = CAPABILITY / "serializer.py"
    spec = importlib.util.spec_from_file_location("trajectory_budget_serializer", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load serializer")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.allocate_budgets


def _head_truncate(lengths: list[int], budget: int) -> list[int]:
    remaining = budget
    allocations: list[int] = []
    for length in lengths:
        keep = min(length, max(remaining, 0))
        allocations.append(keep)
        remaining -= keep
    return allocations


def _metrics(rows: list[dict[str, Any]], key: str) -> dict[str, float]:
    n = len(rows)
    return {
        "budget_compliance_rate": sum(row[key]["total"] <= row["budget"] for row in rows) / n,
        "mean_error_step_allocation": sum(row[key]["error"] for row in rows) / n,
        "mean_warning_step_allocation": sum(row[key]["warning"] for row in rows) / n,
        "error_full_retention_rate": sum(
            row[key]["error"] == row["step_length"] for row in rows
        ) / n,
        "warning_full_retention_rate": sum(
            row[key]["warning"] == row["step_length"] for row in rows
        ) / n,
    }


def run() -> dict[str, Any]:
    allocate = _load_allocator()
    benchmark = json.loads((STUDY / "experiments" / "serializer_stress_spec.json").read_text())
    rows: list[dict[str, Any]] = []
    for case in benchmark["cases"]:
        lengths = [case["step_length"]] * case["step_count"]
        statuses = ["ok"] * case["step_count"]
        statuses[case["warning_step"]] = "warning"
        statuses[case["error_step"]] = "error"
        tiered = allocate(lengths, statuses, case["budget"])
        head = _head_truncate(lengths, case["budget"])
        rows.append({
            **case,
            "tiered_waterfall": {
                "error": tiered[case["error_step"]],
                "warning": tiered[case["warning_step"]],
                "total": sum(tiered),
            },
            "naive_head_truncation": {
                "error": head[case["error_step"]],
                "warning": head[case["warning_step"]],
                "total": sum(head),
            },
        })
    tiered_metrics = _metrics(rows, "tiered_waterfall")
    head_metrics = _metrics(rows, "naive_head_truncation")
    return {
        "benchmark_id": benchmark["benchmark_id"],
        "case_count": len(rows),
        "tiered_waterfall": tiered_metrics,
        "naive_head_truncation": head_metrics,
        "derived": {
            "error_allocation_multiplier_vs_head": (
                tiered_metrics["mean_error_step_allocation"]
                / head_metrics["mean_error_step_allocation"]
            ),
            "warning_allocation_multiplier_vs_head": (
                tiered_metrics["mean_warning_step_allocation"]
                / head_metrics["mean_warning_step_allocation"]
            ),
        },
        "interpretation": (
            "On this deliberately late-failure synthetic stress benchmark, tiered allocation "
            "preserves the full configured error/warning outputs while naive head truncation "
            "increasingly drops later critical steps. This validates the allocation kernel "
            "behavior only; it does not reproduce LiteTrajEval localization, judge quality, "
            "cost, or runtime claims."
        ),
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
