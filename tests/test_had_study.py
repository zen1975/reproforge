import importlib.util
import json
from pathlib import Path

from reproforge.validation import load_document, validate_document

ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT / "studies" / "arxiv-2610.02858"
CORE = ROOT / "capabilities" / "training.harness-aware-action-distillation" / "had.py"


def _load():
    spec = importlib.util.spec_from_file_location("had_test", CORE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_synthetic_had_protocol_is_frozen_and_passes():
    result = json.loads(
        (STUDY / "evidence" / "had_synthetic_protocol_v1.result.json").read_text()
    )
    assert result["all_pass"] is True
    assert result["passed"] == result["check_count"] == 10
    assert result["beta"] == 0.5
    assert result["rho"] == 0.5


def test_had_evidence_schema_validates():
    schema = load_document(ROOT / "schemas" / "evidence.schema.json")
    record = load_document(STUDY / "evidence" / "C3.synthetic-protocol.evidence.json")
    assert validate_document(record, schema) == []


def test_validity_mask_rejects_positive_only():
    had = _load()
    harness = had.HarnessRecord(
        admissible_actions=frozenset({"go sink", "wait"}),
        held_objects=frozenset(),
        no_effect_actions=frozenset({"wait"}),
    )
    invalid = had.build_preference(
        teacher_with_harness_action="wait",
        teacher_without_harness_action="go sink",
        harness=harness,
    )
    assert invalid.valid_positive is False
    assert invalid.active_contrast is True
    assert had.masked_preference_loss(
        invalid,
        positive_action_token_logprobs=[-0.1],
        negative_action_token_logprobs=[-1.0],
    ) == 0.0


def test_gradient_balance_zero_preference_gradient_fails_safe():
    had = _load()
    assert had.gradient_balance_lambda(4.0, 0.0, rho=0.5) == 0.0
    assert had.gradient_balance_lambda(4.0, 2.0, rho=0.5) == 1.0
