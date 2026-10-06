import json
from pathlib import Path

from reproforge.validation import load_document, validate_document

ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT / "studies" / "arxiv-2610.03213"


def test_specialized_sft_evidence_schema_validates():
    record = load_document(STUDY / "evidence" / "C3.specialized-sft.evidence.json")
    schema = load_document(ROOT / "schemas" / "evidence.schema.json")
    assert validate_document(record, schema) == []


def test_specialized_sft_result_records_material_gain_without_overclaiming():
    result = json.loads(
        (STUDY / "evidence" / "task_tool_specialized_minilm_sft_v1.result.json").read_text()
    )
    before = result["initial_untrained_test_at_threshold_0"]
    after = result["test_metrics"]
    assert after["accuracy"] > before["accuracy"]
    assert after["f1"] > before["f1"]
    assert after["false_positive_rate"] == 0.0
    assert result["test_meets_paper_operational_target"] is False
    assert result["families"]["test"] == ["translate", "database"]
