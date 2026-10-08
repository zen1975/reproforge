"""Execute a frozen synthetic LiteTrajEval protocol fixture."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
STUDY = ROOT / "studies" / "arxiv-2610.03315"


def _load():
    path = STUDY / "experiments" / "litetraj_protocol.py"
    spec = importlib.util.spec_from_file_location("litetraj_protocol", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load protocol")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def run():
    m = _load()

    units = [
        "timeout from payment api request",
        "timeout from payment api request repeated",
        "user requested cancel one item",
        "cancel whole order tool executed",
        "later observation confirms whole order cancelled",
    ]
    anchor = "cancel one item whole order cancelled"
    selected = m.mmr_select(units, anchor, 3, lam=0.6)

    predictions = [[33, 35], [8], []]
    references = [
        [m.FailureGroup((33,)), m.FailureGroup((35,))],
        [m.FailureGroup((9, 10)),],
        [m.FailureGroup((4,)),],
    ]

    payload = m.build_single_call_payload(
        "cancel only the garden hose",
        "order cancelled",
        [
            {"step_id": 31, "status": "ok", "output": "reason requested"},
            {"step_id": 33, "status": "error", "output": "cancel whole order"},
            {"step_id": 35, "status": "warning", "output": "whole order cancelled"},
        ],
        [{"start_step_id": 33, "end_step_id": 35, "taxonomy_candidates": ["policy_failure"]}],
    )

    result = {
        "benchmark_id": "litetraj-protocol-synthetic-v1",
        "mmr": {
            "selected_count": len(selected),
            "selected": selected,
            "unique_count": len(set(selected)),
        },
        "metrics": {
            "detection_rate": m.detection_rate(predictions),
            "align_detected_at_1": m.alignment_detected(predictions, references, 1),
            "align_detected_at_3": m.alignment_detected(predictions, references, 3),
        },
        "judge_payload": {
            "single_call": payload["judge_contract"]["single_call"],
            "required_field_count": len(payload["judge_contract"]["required_fields"]),
            "candidate_region_count": len(payload["trajectory_hint"]["candidate_regions"]),
        },
        "claim_scope": "Protocol-equivalent synthetic verification only; no judge-quality or paper-benchmark claim.",
    }
    result["verdict"] = "PASS" if (
        result["mmr"]["selected_count"] == 3
        and result["mmr"]["unique_count"] == 3
        and result["metrics"]["detection_rate"] == 2 / 3
        and result["metrics"]["align_detected_at_1"] == 1.0
        and result["metrics"]["align_detected_at_3"] == 1.0
        and result["judge_payload"]["single_call"] is True
        and result["judge_payload"]["required_field_count"] == 5
    ) else "FAIL"
    return result


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
