import importlib.util
import json
from pathlib import Path

from reproforge.validation import load_document, validate_document

ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT / "studies" / "arxiv-2610.03213"


def _load_runner():
    path = STUDY / "experiments" / "run_task_tool_synthetic_hard.py"
    spec = importlib.util.spec_from_file_location("task_tool_benchmark", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_task_tool_hard_result_is_reproducible():
    module = _load_runner()
    expected = json.loads(
        (STUDY / "evidence" / "task_tool_synthetic_hard_v1.result.json").read_text()
    )
    assert module.run() == expected


def test_task_tool_evidence_schema_validates():
    record = load_document(STUDY / "evidence" / "C1.synthetic-hard.evidence.json")
    schema = load_document(ROOT / "schemas" / "evidence.schema.json")
    assert validate_document(record, schema) == []


def test_lexical_reference_does_not_meet_paper_target():
    result = _load_runner().run()
    metrics = result["lexical_overlap_reference_v1"]
    assert metrics["accuracy"] == 0.5
    assert metrics["f1"] < 0.95
    assert result["meets_paper_operational_target"] is False
