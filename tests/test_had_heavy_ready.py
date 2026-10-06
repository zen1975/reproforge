import json
from pathlib import Path

from reproforge.validation import load_document, validate_document

ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT / "studies" / "arxiv-2610.02858"


def test_qwen_smoke_evidence_validates():
    schema = load_document(ROOT / "schemas" / "evidence.schema.json")
    record = load_document(STUDY / "evidence" / "C4.qwen0.5b-smoke.evidence.json")
    assert validate_document(record, schema) == []


def test_had_invalid_preference_fails_safe_in_real_model_smoke():
    result = json.loads((STUDY / "evidence" / "had_qwen0.5b_had_smoke_v2.result.json").read_text())
    invalid = result["invalid_step"]
    assert invalid["valid_preference"] is False
    assert invalid["preference_loss"] == 0.0
    assert invalid["preference_grad_norm"] == 0.0
    assert invalid["lambda"] == 0.0


def test_had_smoke_makes_no_performance_claim():
    result = json.loads((STUDY / "evidence" / "had_qwen0.5b_smoke_v2_comparison.result.json").read_text())
    assert result["performance_claim"] == "NONE"
    assert result["had"]["accuracy_after"] == 0.75
    assert result["distill_only"]["accuracy_after"] == 0.75


def test_had_is_heavy_compute_ready_with_handoff():
    status = load_document(STUDY / "status.yaml")
    assert status["lifecycle"] == "HEAVY_COMPUTE_READY"
    assert status["reproduction_status"] == "PARTIAL"
    assert status["free_light_phase_complete"] is True
    assert status["handoff"]["ready"] is True
    assert (STUDY / "HANDOFF.md").exists()
