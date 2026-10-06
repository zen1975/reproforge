import json
from pathlib import Path

from reproforge.validation import load_document, validate_document

ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT / "studies" / "arxiv-2610.06191"


def test_contrast_evidence_schema_validates():
    schema = load_document(ROOT / "schemas" / "evidence.schema.json")
    for name in [
        "C3.synthetic-contrast.evidence.json",
        "C3.official-delta-audit.evidence.json",
    ]:
        record = load_document(STUDY / "evidence" / name)
        assert validate_document(record, schema) == []


def test_official_delta_audit_matches_all_released_cells():
    result = json.loads(
        (STUDY / "evidence" / "official_episode_delta_audit_v2.result.json").read_text()
    )
    assert result["cells_audited"] == 43
    assert result["exact_delta_matches"] == 43
    assert result["exact_ci_matches"] == 43
    assert result["all_cells_exact_match"] is True
    assert result["official_commit"] == "2e6404e542b4afdafa3d54d9b18eb1c28c2bafc8"


def test_study_is_protocol_verified_but_not_full_reproduction():
    status = load_document(STUDY / "status.yaml")
    assert status["lifecycle"] == "PROTOCOL_VERIFIED"
    assert status["reproduction_status"] == "PARTIAL"
    assert status["free_light_phase_complete"] is False
