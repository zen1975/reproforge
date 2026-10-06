from pathlib import Path

from reproforge.cli import cmd_validate_all_statuses, cmd_validate_status
from reproforge.validation import load_document, validate_document

ROOT = Path(__file__).resolve().parents[1]


def test_example_study_status_validates_schema():
    status = load_document(ROOT / "templates" / "study-status.example.yaml")
    schema = load_document(ROOT / "schemas" / "study-status.schema.json")
    assert validate_document(status, schema) == []


def test_all_current_study_statuses_are_valid():
    assert cmd_validate_all_statuses() == 0


def test_heavy_compute_ready_study_has_ready_handoff():
    path = ROOT / "studies" / "arxiv-2610.03213" / "status.yaml"
    assert cmd_validate_status(str(path)) == 0
    status = load_document(path)
    assert status["lifecycle"] == "HEAVY_COMPUTE_READY"
    assert status["free_light_phase_complete"] is True
    assert status["handoff"]["ready"] is True
    assert (ROOT / status["handoff"]["path"]).exists()


def test_incomplete_study_does_not_claim_free_light_completion():
    status = load_document(ROOT / "studies" / "arxiv-2610.03315" / "status.yaml")
    assert status["lifecycle"] == "MECHANISM_VERIFIED"
    assert status["free_light_phase_complete"] is False
