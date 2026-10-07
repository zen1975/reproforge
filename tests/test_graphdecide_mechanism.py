import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT / "studies" / "arxiv-2610.06354"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_graphdecide_synthetic_mechanism_passes():
    runner = _load(
        STUDY / "experiments" / "run_graphdecide_mechanism.py",
        "graphdecide_runner",
    )
    result = runner.run()
    assert result["verdict"] == "PASS"
    assert result["graph_cognition"]["task_count"] == 6
    assert result["graph_cognition"]["correct_count"] == 6
    assert result["graph_cognition"]["all_reference_matches"] is True


def test_invalid_and_unsupported_choices_are_not_smuggled_into_accuracy():
    runner = _load(
        STUDY / "experiments" / "run_graphdecide_mechanism.py",
        "graphdecide_runner_invalid",
    )
    result = runner.run()
    probes = result["interface_probes"]
    assert probes["invalid_output_valid"] is False
    assert probes["invalid_output_correct"] is False
    assert probes["unsupported_supported"] is False
    assert probes["unsupported_correct"] is False


def test_sequential_failure_has_no_artificial_objective_or_gap():
    runner = _load(
        STUDY / "experiments" / "run_graphdecide_mechanism.py",
        "graphdecide_runner_seq",
    )
    result = runner.run()["sequential"]
    assert result["complete_status"] == "complete"
    assert result["complete_objective"] == 4.0
    assert result["complete_gap"] == 0.0
    assert result["failed_status"] == "invalid_action"
    assert result["failed_objective"] is None
    assert result["failed_gap"] is None
    assert result["summary"]["coverage"] == 0.5
    assert result["summary"]["completed"] == 1
    assert result["summary"]["failed"] == 1
