import json
from pathlib import Path

from reproforge.validation import load_document, validate_document

ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT / "studies" / "arxiv-2610.02858"


def test_harness_signal_evidence_validates():
    schema = load_document(ROOT / "schemas" / "evidence.schema.json")
    record = load_document(STUDY / "evidence" / "C1.harness-signal-qwen-v2.evidence.json")
    assert validate_document(record, schema) == []


def test_multiseed_evidence_validates():
    schema = load_document(ROOT / "schemas" / "evidence.schema.json")
    record = load_document(STUDY / "evidence" / "C3.real-pair-multiseed.evidence.json")
    assert validate_document(record, schema) == []


def test_real_teacher_generates_active_harness_signal():
    result = json.loads((STUDY / "evidence" / "had_harness_signal_qwen_contrast_v2.result.json").read_text())
    assert result["active_contrasts"] == 2
    assert result["valid_active_contrasts"] == 2
    assert result["harness_corrected_student_actions"] == 2
    assert result["uses_task_reward"] is False
    assert result["uses_future_information_for_validity"] is False


def test_multiseed_result_stays_bounded_and_directional():
    result = json.loads((STUDY / "evidence" / "had_real_teacher_pair_multiseed_v1.result.json").read_text())
    assert result["performance_claim"] == "NONE"
    assert result["aggregate"]["accuracy_improvement_runs"] == 0
    assert result["aggregate"]["seeds_where_had_margin_change_exceeded_distill"] == 3
    assert result["aggregate"]["had_minus_distill_mean_margin_change"] > 0
