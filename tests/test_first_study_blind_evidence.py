import json
from pathlib import Path

from reproforge.validation import load_document, validate_document

ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT / "studies" / "arxiv-2610.03213"


def test_blind_v1_evidence_schema_validates():
    record = load_document(STUDY / "evidence" / "C3.blind-v1.evidence.json")
    schema = load_document(ROOT / "schemas" / "evidence.schema.json")
    assert validate_document(record, schema) == []


def test_blind_v1_records_significant_gain_without_claiming_target():
    result = json.loads(
        (STUDY / "evidence" / "task_tool_specialized_minilm_blind_v1.result.json").read_text()
    )
    assert result["blind_count"] == 144
    assert result["after_specialization"]["accuracy"] > result["before_specialization"]["accuracy"]
    assert result["after_specialization"]["f1"] > result["before_specialization"]["f1"]
    assert result["paired_mcnemar"]["p_value_two_sided"] < 0.001
    assert result["blind_meets_paper_operational_target"] is False
