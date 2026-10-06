import importlib.util
import json
from pathlib import Path

from reproforge.validation import load_document, validate_document

ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT / "studies" / "arxiv-2610.03315"


def _load_benchmark():
    path = STUDY / "experiments" / "run_serializer_stress.py"
    spec = importlib.util.spec_from_file_location("serializer_stress_benchmark", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_committed_serializer_stress_result_is_reproducible():
    module = _load_benchmark()
    expected = json.loads((STUDY / "evidence" / "serializer_stress_result.json").read_text())
    assert module.run() == expected


def test_serializer_stress_evidence_schema_validates():
    record = load_document(STUDY / "evidence" / "C1.serializer-stress.evidence.json")
    schema = load_document(ROOT / "schemas" / "evidence.schema.json")
    assert validate_document(record, schema) == []


def test_stress_benchmark_demonstrates_late_failure_budget_retention():
    result = _load_benchmark().run()
    tiered = result["tiered_waterfall"]
    head = result["naive_head_truncation"]
    assert tiered["budget_compliance_rate"] == 1.0
    assert tiered["error_full_retention_rate"] == 1.0
    assert tiered["mean_error_step_allocation"] > head["mean_error_step_allocation"]
    assert result["derived"]["error_allocation_multiplier_vs_head"] > 3.0
