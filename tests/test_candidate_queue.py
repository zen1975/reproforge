from pathlib import Path

from reproforge.cli import cmd_validate_candidates
from reproforge.validation import load_document, validate_document

ROOT = Path(__file__).resolve().parents[1]


def test_candidate_queue_schema_validates():
    queue = load_document(ROOT / "candidates" / "queue.yaml")
    schema = load_document(ROOT / "schemas" / "candidate-queue.schema.json")
    assert validate_document(queue, schema) == []


def test_candidate_queue_has_unique_verified_sources():
    queue = load_document(ROOT / "candidates" / "queue.yaml")
    candidates = queue["candidates"]
    ids = [item["arxiv_id"] for item in candidates]
    assert len(ids) == len(set(ids))
    assert all(item["source_verified"] is True for item in candidates)
    allowed = {"SOURCE_VERIFIED", "PDF_REVIEWED", "PROMOTED_TO_STUDY", "DEFERRED", "REJECTED"}
    assert all(item["status"] in allowed for item in candidates)


def test_candidate_queue_cli_validates():
    assert cmd_validate_candidates(str(ROOT / "candidates" / "queue.yaml")) == 0


def test_high_priority_candidates_have_concrete_capability_hypotheses():
    queue = load_document(ROOT / "candidates" / "queue.yaml")
    top = [item for item in queue["candidates"] if item["priority"] in {"A+", "A"}]
    assert top
    assert all(item["candidate_capability"].startswith(("agent.", "research.")) for item in top)
