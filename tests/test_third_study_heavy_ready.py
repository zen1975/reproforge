import json
from pathlib import Path

from reproforge.validation import load_document, validate_document

ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT / "studies" / "arxiv-2610.06191"


def test_summary_audit_evidence_schema_validates():
    schema = load_document(ROOT / "schemas" / "evidence.schema.json")
    record = load_document(STUDY / "evidence" / "C1.official-summary-audit.evidence.json")
    assert validate_document(record, schema) == []


def test_summary_audit_matches_all_released_cells():
    result = json.loads(
        (STUDY / "evidence" / "official_episode_summary_audit_v1.result.json").read_text()
    )
    assert result["cells_audited"] == 43
    assert result["mean6_exact_matches"] == 43
    assert result["answer_summary_exact_matches"] == 43
    assert result["all_exact_match"] is True


def test_study_is_heavy_compute_ready_with_handoff():
    status = load_document(STUDY / "status.yaml")
    assert status["lifecycle"] == "HEAVY_COMPUTE_READY"
    assert status["reproduction_status"] == "PARTIAL"
    assert status["free_light_phase_complete"] is True
    assert status["handoff"]["ready"] is True
    assert (STUDY / "HANDOFF.md").exists()
