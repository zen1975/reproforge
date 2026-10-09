"""Independent synthetic mechanism regression; no author assets used."""

import importlib.util
import sys
from pathlib import Path

MODULE = (
    Path(__file__).resolve().parents[1]
    / "capabilities"
    / "agent.tool-fault-auditor"
    / "fault_audit.py"
)
spec = importlib.util.spec_from_file_location("fault_audit", MODULE)
assert spec is not None and spec.loader is not None
fault_audit = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = fault_audit
spec.loader.exec_module(fault_audit)


def test_once_and_clean():
    state = {"n": 0}

    def work():
        state["n"] += 1
        return {"n": state["n"]}

    injector = fault_audit.FaultInjector("timeout", 2)
    assert injector.call(1, "t", work).fault_fired is False
    assert injector.call(2, "t", work).error == "timeout"
    assert state["n"] == 1
    assert injector.call(3, "t", work).value == {"n": 2}
    assert state["n"] == 2
    clean = fault_audit.FaultInjector("clean", 1)
    assert clean.call(1, "t", work).fault_fired is False


def test_corruption_preserves_real_state_and_shape():
    state = {"n": 0}

    def work():
        state["n"] += 1
        return {"n": state["n"], "meta": "ok"}

    injector = fault_audit.FaultInjector("silent_corruption", 1)
    result = injector.call(1, "t", work)
    assert result.value == {"n": 2, "meta": "ok"}
    assert state == {"n": 1}
    assert result.error is None and result.fault_fired
    assert injector.call(2, "t", work).value == {"n": 2, "meta": "ok"}


def test_target_and_repetition_and_metrics():
    injector = fault_audit.FaultInjector("missing_tool", 2, "special")
    assert injector.call(2, "other", lambda: 4).fault_fired is False
    assert injector.call(3, "special", lambda: 5).error == "missing_tool"
    assert fault_audit.state_agreement({"a": 1, "b": 3}, {"a": 1, "b": 2}) == 0.5
    assert fault_audit.repeated_calls([("a", 1), ("a", 2), ("a", 3)]) == {
        "same_tool_three": True,
        "identical_three": False,
    }
    assert fault_audit.repeated_calls([("a", 1)] * 3)["identical_three"]


def test_synthetic_benchmark_results():
    result = fault_audit.run_synthetic()
    assert result["total"] == 15
    assert result["fired"] == 12
    assert result["loud_detected"] == 9
    assert result["loud_total"] == 9
    assert result["quiet_detected"] == 1
    assert result["quiet_total"] == 3
    assert result["recovered"] == 12
