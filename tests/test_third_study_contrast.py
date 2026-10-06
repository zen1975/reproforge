import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT / "studies" / "arxiv-2610.06191"
CONTRAST = ROOT / "capabilities" / "agent.evidence-aware-stopping-gate" / "contrast.py"


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_time_matched_contrast_distinguishes_evidence_from_clock():
    runner = _load(
        STUDY / "experiments" / "run_contrast_synthetic.py",
        "contrast_synthetic_test",
    )
    result = runner.run()
    assert result["all_pass"] is True
    assert result["evidence_integrating_delta"] > 0.9
    assert abs(result["clock_driven_delta"]) < 1e-12


def test_contrast_is_deterministic_for_fixed_bootstrap_seed():
    metric = _load(CONTRAST, "contrast_determinism")
    trajectories = [
        {
            "question_id": "q1",
            "actions": ["search", "search", "search", "search", "finish"],
            "judgments": ["USELESS", "USELESS", "USELESS", "USELESS"],
        },
        {
            "question_id": "q1",
            "actions": ["search", "search", "search", "search", "search"],
            "judgments": ["USELESS", "USEFUL", "USELESS", "USELESS"],
        },
    ]
    a = metric.time_matched_contrast(
        trajectories, t_min=4, t_max=4, bootstrap_samples=50, seed=7
    )
    b = metric.time_matched_contrast(
        trajectories, t_min=4, t_max=4, bootstrap_samples=50, seed=7
    )
    assert a == b
