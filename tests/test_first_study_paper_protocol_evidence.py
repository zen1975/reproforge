import json
from pathlib import Path

from reproforge.validation import load_document, validate_document

ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT / "studies" / "arxiv-2610.03213"


def test_paper_protocol_evidence_records_validate():
    schema = load_document(ROOT / "schemas" / "evidence.schema.json")
    for name in [
        "C3.sft-protocol-prep.evidence.json",
        "C3.lora-sft-harness.evidence.json",
    ]:
        record = load_document(STUDY / "evidence" / name)
        assert validate_document(record, schema) == []


def test_sft_smoke_is_not_mislabeled_as_gemma_reproduction():
    result = json.loads(
        (STUDY / "evidence" / "lora_sft_harness_smoke_v1.result.json").read_text()
    )
    assert result["model_id"] == "HuggingFaceTB/SmolLM2-135M-Instruct"
    assert result["status"] == "HARNESS_EXECUTED"
    assert result["last_loss"] < result["first_loss"]
    assert "Not Gemma 3" in result["boundary"]


def test_gemma_access_block_is_explicit():
    result = json.loads(
        (STUDY / "evidence" / "gemma3_1b_access_preflight_v1.result.json").read_text()
    )
    assert result["status"] == "BLOCKED_MODEL_ACCESS"
    assert result["requested_model"] == "google/gemma-3-1b-it"
