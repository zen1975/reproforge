import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "capabilities" / "agent.evidence-aware-stopping-gate" / "summary.py"


def _load():
    spec = importlib.util.spec_from_file_location("summary_test", SUMMARY)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_answer_after_five_useless_requires_reaching_decision_point():
    mod = _load()
    episodes = [
        {
            "actions": ["search", "search", "search", "search", "search", "finish"],
            "judgments": ["USELESS"] * 5,
        },
        {
            "actions": ["search", "search", "search", "search", "search", "search"],
            "judgments": ["USELESS"] * 5,
        },
        {
            "actions": ["search", "search", "search", "search", "finish"],
            "judgments": ["USELESS"] * 4,
        },
    ]
    result = mod.answer_rate_after_run(episodes, k=5)
    assert result == {"reached": 2, "answered": 1, "rate": 0.5}


def test_mean6_is_equal_weight_per_question():
    mod = _load()
    episodes = []
    regimes = list(mod.MEAN6_REGIMES)
    for regime in regimes:
        episodes.append(
            {"question_id": "q1", "regime": regime, "success": regime == "clean"}
        )
        episodes.append(
            {"question_id": "q2", "regime": regime, "success": True}
        )
    assert mod.mean6_success(episodes) == ((1 / 6) + 1.0) / 2
