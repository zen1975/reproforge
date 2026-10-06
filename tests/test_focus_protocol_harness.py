import importlib.util
import json
from pathlib import Path

from reproforge.validation import load_document, validate_document

ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT / "studies" / "arxiv-2609.37590"
CAP = ROOT / "capabilities" / "agent.decision-preserving-context-compressor"


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_provider_neutral_protocol_result_passes():
    result = json.loads(
        (STUDY / "evidence" / "focus_provider_neutral_protocol_v1.result.json").read_text()
    )
    assert result["all_pass"] is True
    assert result["passed"] == result["check_count"] == 7


def test_provider_neutral_protocol_evidence_validates():
    schema = load_document(ROOT / "schemas" / "evidence.schema.json")
    record = load_document(STUDY / "evidence" / "C3.provider-neutral-protocol.evidence.json")
    assert validate_document(record, schema) == []


def test_harness_does_not_call_draft_under_budget():
    core = _load(CAP / "compressor.py", "focus_test_core")
    harness = _load(CAP / "harness.py", "focus_test_harness")
    spans = [core.Span("s_1", "r", "a", "o")]
    calls = []

    def draft(**kwargs):
        calls.append(kwargs)
        raise AssertionError("draft should not be called")

    result = harness.run_focus(
        spans,
        goal="g",
        context_tokens=100,
        memory_budget_tokens=2048,
        draft=draft,
    )
    assert result.compression_triggered is False
    assert result.retained_ids == ("s_1",)
    assert calls == []
