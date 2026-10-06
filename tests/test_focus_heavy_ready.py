import json
from pathlib import Path

from reproforge.validation import load_document, validate_document

ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT / "studies" / "arxiv-2609.37590"


def test_qwen_negative_evidence_validates():
    schema = load_document(ROOT / "schemas" / "evidence.schema.json")
    record = load_document(STUDY / "evidence" / "C3.qwen0.5b-negative.evidence.json")
    assert validate_document(record, schema) == []


def test_qwen_boundary_is_preserved_as_negative_evidence():
    result = json.loads(
        (STUDY / "evidence" / "focus_qwen0.5b_draft_analogue_v1_negative.result.json").read_text()
    )
    assert result["rollouts"] == 3
    assert result["parse_successes"] == 0
    assert result["rejection_reason_category"] == "hallucinated_unknown_span_ids"
    assert result["required_preserved"] is False


def test_focus_is_heavy_compute_ready_with_handoff():
    status = load_document(STUDY / "status.yaml")
    assert status["lifecycle"] == "HEAVY_COMPUTE_READY"
    assert status["reproduction_status"] == "PARTIAL"
    assert status["free_light_phase_complete"] is True
    assert status["handoff"]["ready"] is True
    assert (STUDY / "HANDOFF.md").exists()
