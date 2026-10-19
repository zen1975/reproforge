"""Run a frozen synthetic mechanism test for the independent FAOP-like verifier."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

STUDY_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = STUDY_DIR.parents[1]
FIXTURE_PATH = STUDY_DIR / "fixtures" / "faop_static_v2.json"
VERIFIER_PATH = (
    REPO_ROOT / "capabilities" / "agent.faop-workflow-static-verifier" / "verifier.py"
)
RESULT_PATH = STUDY_DIR / "evidence" / "faop_static_verifier_v2.result.json"
EVIDENCE_PATH = STUDY_DIR / "evidence" / "faop_static_verifier_v2.evidence.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_verifier() -> Any:
    spec = importlib.util.spec_from_file_location("faop_static_verifier", VERIFIER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load independent verifier")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.verify_registry


def shape_only_accepts(workflows: list[dict[str, Any]]) -> bool:
    required = {"id", "inputs", "outputs", "scope", "steps"}
    return all(
        isinstance(workflow, dict)
        and required.issubset(workflow)
        and isinstance(workflow["steps"], list)
        for workflow in workflows
    )


def main() -> int:
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    verify_registry = load_verifier()
    case_results: list[dict[str, Any]] = []
    for case in fixture["cases"]:
        result = verify_registry(
            case["workflows"],
            require_termination=case.get("require_termination", False),
            require_bounds=case.get("require_bounds", False),
        )
        actual_codes = sorted({item["code"] for item in result["violations"]})
        expected_codes = sorted(case["expected_codes"])
        case_pass = result["valid"] is case["expected_valid"] and set(expected_codes).issubset(actual_codes)
        case_results.append(
            {
                "name": case["name"],
                "expected_valid": case["expected_valid"],
                "actual_valid": result["valid"],
                "expected_codes": expected_codes,
                "actual_codes": actual_codes,
                "mechanism_test_pass": case_pass,
                "shape_only_baseline_accepts": shape_only_accepts(case["workflows"]),
            }
        )

    total = len(case_results)
    correct = sum(item["mechanism_test_pass"] for item in case_results)
    baseline_accepted = sum(item["shape_only_baseline_accepts"] for item in case_results)
    baseline_false_accepts = sum(
        item["shape_only_baseline_accepts"] and not item["expected_valid"]
        for item in case_results
    )
    result_doc = {
        "evaluation_id": fixture["evaluation_id"],
        "paper_benchmark": fixture["paper_benchmark"],
        "verifier_sha256": sha256(VERIFIER_PATH),
        "fixture_sha256": sha256(FIXTURE_PATH),
        "case_count": total,
        "case_names": [item["name"] for item in case_results],
        "mechanism_cases_correct": correct,
        "mechanism_case_accuracy": correct / total if total else 0.0,
        "shape_only_baseline_accept_count": baseline_accepted,
        "shape_only_baseline_false_accepts": baseline_false_accepts,
    }
    RESULT_PATH.write_text(json.dumps(result_doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    evidence = {
        "claim_id": "C1-C5-independent-static-mechanism",
        "run_id": fixture["evaluation_id"],
        "artifact_hashes": {
            "verifier.py": sha256(VERIFIER_PATH),
            "fixture.json": sha256(FIXTURE_PATH),
            "run_static_verifier.py": sha256(Path(__file__)),
            "result.json": sha256(RESULT_PATH),
        },
        "metrics": {
            "synthetic_cases": total,
            "mechanism_cases_correct": correct,
            "mechanism_case_accuracy": correct / total if total else 0.0,
            "shape_only_baseline_accept_count": baseline_accepted,
            "shape_only_baseline_false_accepts": baseline_false_accepts,
            "paper_benchmark": False,
        },
        "verdict": "PASS" if correct == total else "FAIL",
        "notes": (
            "PASS applies only to this frozen, hand-authored synthetic mechanism suite. "
            "The shape-only baseline is intentionally limited to required top-level fields. "
            "This does not reproduce the paper's SkillBase compiler, prove declared effects match "
            "runtime behavior, or reproduce any empirical paper result."
        ),
    }
    EVIDENCE_PATH.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: result_doc[key] for key in (
        "evaluation_id", "paper_benchmark", "case_count", "mechanism_cases_correct",
        "mechanism_case_accuracy", "shape_only_baseline_accept_count", "shape_only_baseline_false_accepts"
    )}, indent=2, sort_keys=True))
    return 0 if correct == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
