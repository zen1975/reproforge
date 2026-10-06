import importlib.util
import json
from pathlib import Path

from reproforge.validation import load_document, validate_document

ROOT=Path(__file__).resolve().parents[1]
STUDY=ROOT/"studies"/"arxiv-2610.06191"
CAP=ROOT/"capabilities"/"agent.evidence-aware-stopping-gate"/"gate.py"


def _load():
    spec=importlib.util.spec_from_file_location("gate_test",CAP)
    assert spec is not None and spec.loader is not None
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_gate_fires_at_exactly_five_consecutive_useless():
    mod=_load()
    gate=mod.EvidenceStoppingGate(5)
    assert [gate.update("USELESS") for _ in range(4)] == [False]*4
    assert gate.update("USELESS") is True


def test_useful_resets_before_fire_and_fire_is_sticky():
    mod=_load()
    gate=mod.EvidenceStoppingGate(5)
    for _ in range(4):
        assert gate.update("USELESS") is False
    assert gate.update("USEFUL") is False
    assert gate.consecutive_useless == 0
    for _ in range(5):
        fired=gate.update("USELESS")
    assert fired is True
    assert gate.update("USEFUL") is True


def test_synthetic_mechanism_result_is_frozen_and_passes():
    result=json.loads((STUDY/"evidence"/"stopping_gate_synthetic_v1.result.json").read_text())
    assert result["all_pass"] is True
    assert result["scenario_pass_rate"] == 1.0
    assert result["total_tool_calls_saved_vs_deadline_baseline"] == 4


def test_evidence_schema_validates():
    record=load_document(STUDY/"evidence"/"C2.synthetic-gate.evidence.json")
    schema=load_document(ROOT/"schemas"/"evidence.schema.json")
    assert validate_document(record,schema)==[]
