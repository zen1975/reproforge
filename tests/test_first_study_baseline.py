import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLASSIFIER_PATH = (
    ROOT / "capabilities" / "agent.task-tool-relevance-classifier" / "classifier.py"
)
FIXTURES_PATH = ROOT / "studies" / "arxiv-2610.03213" / "fixtures" / "synthetic_cases.json"


def _load_classifier():
    spec = importlib.util.spec_from_file_location("reproforge_first_study_classifier", CLASSIFIER_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.classify


def test_reference_baseline_matches_all_synthetic_cases():
    classify = _load_classifier()
    payload = json.loads(FIXTURES_PATH.read_text(encoding="utf-8"))

    results = []
    for case in payload["cases"]:
        result = classify(case["task"], case["tool_name"], case["tool_description"])
        results.append(result["relevant"] == case["expected_relevant"])

    assert all(results)
    assert len(results) == 6


def test_reference_baseline_is_deterministic():
    classify = _load_classifier()
    args = ("send email to the project team", "email_send", "send email message to recipients")
    assert classify(*args) == classify(*args)
