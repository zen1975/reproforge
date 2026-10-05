from pathlib import Path

from reproforge.intake import validate_intake_identity
from reproforge.validation import load_document, validate_document

ROOT = Path(__file__).resolve().parents[1]


def test_intake_source_record_schema_validates():
    source = load_document(ROOT / "studies" / "arxiv-2610.03213" / "source-metadata.json")
    schema = load_document(ROOT / "schemas" / "intake-source.schema.json")
    assert validate_document(source, schema) == []


def test_first_study_identity_matches_but_authority_remains_unverified():
    manifest = load_document(ROOT / "studies" / "arxiv-2610.03213" / "manifest.yaml")
    source = load_document(ROOT / "studies" / "arxiv-2610.03213" / "source-metadata.json")
    result = validate_intake_identity(manifest, source)
    assert result["status"] == "IDENTITY_MATCHED_SOURCE_UNVERIFIED"
    assert result["errors"] == []
    assert all(result["checks"].values())


def test_intake_gate_rejects_title_mismatch():
    manifest = load_document(ROOT / "studies" / "arxiv-2610.03213" / "manifest.yaml")
    source = load_document(ROOT / "studies" / "arxiv-2610.03213" / "source-metadata.json")
    source["title"] = "Wrong paper"
    result = validate_intake_identity(manifest, source)
    assert result["status"] == "REJECTED"
    assert "title mismatch" in result["errors"]


def test_authoritative_match_can_verify_identity():
    manifest = load_document(ROOT / "studies" / "arxiv-2610.03213" / "manifest.yaml")
    source = load_document(ROOT / "studies" / "arxiv-2610.03213" / "source-metadata.json")
    source["authoritative"] = True
    source["source_kind"] = "arxiv"
    result = validate_intake_identity(manifest, source)
    assert result["status"] == "VERIFIED"
