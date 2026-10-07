"""Execute the frozen GraphDecide synthetic mechanism fixture."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
STUDY = ROOT / "studies" / "arxiv-2610.06354"


def _load_module():
    path = STUDY / "experiments" / "graphdecide_mechanism.py"
    spec = importlib.util.spec_from_file_location("graphdecide_mechanism", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load mechanism")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run() -> dict[str, Any]:
    m = _load_module()
    spec = json.loads((STUDY / "experiments" / "graphdecide_synthetic_spec.json").read_text())
    graph = m.SimpleGraph.build(spec["graph"]["vertices"], spec["graph"]["edges"])

    cognition_rows = []
    for row in spec["queries"]:
        query = m.Query(row["task"], row["args"], tuple(row["candidates"]))
        result = m.evaluate_query(graph, query, row["expected"])
        cognition_rows.append({
            "id": row["id"],
            "task": row["task"],
            "reference": result.reference,
            "expected": row["expected"],
            "valid": result.valid,
            "correct": result.correct,
        })

    invalid_probe = m.evaluate_query(
        graph,
        m.Query("adjacency", {"u": "A", "v": "B"}, ("yes", "no")),
        "maybe",
    )
    unsupported_probe = m.evaluate_query(
        graph,
        m.Query("adjacency", {"u": "A", "v": "B"}, ("yes", "no")),
        None,
    )

    tsp = spec["tsp"]
    distances = {tuple(key.split("|")): value for key, value in tsp["distances"].items()}
    instance = m.TSPInstance(tuple(tsp["cities"]), distances, float(tsp["reference"]))

    order = {"A": "B", "B": "C", "C": "D"}
    def optimal_policy(state, candidates):
        preferred = order.get(str(state["current"]))
        return preferred if preferred in candidates else candidates[0]

    def invalid_policy(state, candidates):
        del state, candidates
        return "NOT_A_CITY"

    complete = m.run_tsp(instance, optimal_policy, tsp["start"])
    failed = m.run_tsp(instance, invalid_policy, tsp["start"])
    summary = m.summarize_trajectories([complete, failed])

    return {
        "benchmark_id": spec["benchmark_id"],
        "graph_cognition": {
            "task_count": len(cognition_rows),
            "correct_count": sum(row["correct"] for row in cognition_rows),
            "all_reference_matches": all(row["reference"] == row["expected"] for row in cognition_rows),
            "rows": cognition_rows,
        },
        "interface_probes": {
            "invalid_output_valid": invalid_probe.valid,
            "invalid_output_correct": invalid_probe.correct,
            "unsupported_supported": unsupported_probe.supported,
            "unsupported_correct": unsupported_probe.correct,
        },
        "sequential": {
            "complete_status": complete.status,
            "complete_objective": complete.objective,
            "complete_gap": complete.gap,
            "complete_candidate_history": complete.candidate_history,
            "failed_status": failed.status,
            "failed_objective": failed.objective,
            "failed_gap": failed.gap,
            "summary": summary,
        },
        "verdict": "PASS" if (
            all(row["correct"] for row in cognition_rows)
            and not invalid_probe.valid
            and not unsupported_probe.supported
            and complete.complete
            and complete.objective == 4.0
            and complete.gap == 0.0
            and failed.objective is None
            and failed.gap is None
            and summary["coverage"] == 0.5
        ) else "FAIL",
        "claim_scope": "Mechanism contract only; no paper benchmark performance claim.",
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
