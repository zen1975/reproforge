import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT / "studies" / "arxiv-2610.03315"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_litetraj_protocol_fixture_passes():
    runner = _load(STUDY / "experiments" / "run_litetraj_protocol.py", "litetraj_runner")
    result = runner.run()
    assert result["verdict"] == "PASS"
    assert result["metrics"]["detection_rate"] == 2 / 3
    assert result["metrics"]["align_detected_at_1"] == 1.0
    assert result["metrics"]["align_detected_at_3"] == 1.0


def test_mmr_rejects_invalid_lambda_and_selects_requested_count():
    protocol = _load(STUDY / "experiments" / "litetraj_protocol.py", "litetraj_protocol_test")
    try:
        protocol.mmr_select(["a"], "a", 1, lam=1.1)
    except ValueError:
        pass
    else:
        raise AssertionError("invalid lambda must fail")

    selected = protocol.mmr_select(["alpha beta", "alpha beta", "beta gamma"], "alpha", 2)
    assert len(selected) == 2


def test_alignment_is_conditional_on_detected_samples():
    protocol = _load(STUDY / "experiments" / "litetraj_protocol.py", "litetraj_alignment_test")
    refs = [[protocol.FailureGroup((10,))], [protocol.FailureGroup((20,))]]
    assert protocol.detection_rate([[10], []]) == 0.5
    assert protocol.alignment_detected([[10], []], refs, 1) == 1.0


def test_structured_judge_report_contract():
    protocol = _load(STUDY / "experiments" / "litetraj_protocol.py", "litetraj_report_test")
    valid = {
        "rubric_scores": {"goal": 2},
        "failure_categories": ["policy_failure"],
        "failure_steps": [33],
        "root_cause": "wrong cancellation scope",
        "key_observations": ["whole order cancelled"],
    }
    protocol.validate_judge_report(valid)

    invalid = dict(valid)
    del invalid["failure_steps"]
    try:
        protocol.validate_judge_report(invalid)
    except ValueError:
        pass
    else:
        raise AssertionError("missing required report field must fail")
