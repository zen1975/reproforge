import importlib.util
import json
from pathlib import Path

from reproforge.validation import load_document, validate_document

ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT / "studies" / "arxiv-2609.37590"
CORE = ROOT / "capabilities" / "agent.decision-preserving-context-compressor" / "compressor.py"


def _load():
    spec = importlib.util.spec_from_file_location("focus_test", CORE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_focus_utility_is_citation_frequency():
    mod = _load()
    spans = [mod.Span(f"s_{i}", "", "", "") for i in range(1, 4)]
    result = mod.compress(
        spans,
        [{"s_1"}, {"s_1", "s_2"}, {"s_3"}],
        tau=0.3,
    )
    assert result.utility == {"s_1": 2 / 3, "s_2": 1 / 3, "s_3": 1 / 3}
    assert result.retained_ids == ("s_1", "s_2", "s_3")


def test_defensive_rescue_is_union_only():
    mod = _load()
    spans = [mod.Span(f"s_{i}", "", "", "") for i in range(1, 4)]
    optimistic = mod.compress(spans, [{"s_1"}] * 3, tau=0.3)
    defensive = mod.compress(spans, [{"s_1"}] * 3, tau=0.3, rescued_ids={"s_3"})
    assert optimistic.retained_ids == ("s_1",)
    assert defensive.retained_ids == ("s_1", "s_3")


def test_frozen_synthetic_result_passes():
    result = json.loads(
        (STUDY / "evidence" / "focus_synthetic_protocol_v1.result.json").read_text()
    )
    assert result["all_pass"] is True
    assert result["case_count"] == 4
    assert result["paper_defaults"] == {"N": 3, "tau": 0.3}


def test_focus_evidence_validates():
    schema = load_document(ROOT / "schemas" / "evidence.schema.json")
    for name in [
        "C1.synthetic-selection.evidence.json",
        "C2.synthetic-defensive.evidence.json",
    ]:
        assert validate_document(load_document(STUDY / "evidence" / name), schema) == []
