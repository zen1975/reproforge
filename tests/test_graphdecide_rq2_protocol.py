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


def test_graphdecide_rq2_protocol_passes():
    runner = _load(
        STUDY / "experiments" / "run_graphdecide_rq2_protocol.py",
        "graphdecide_rq2_runner",
    )
    result = runner.run()
    assert result["verdict"] == "PASS"
    assert result["matched_items"] == 8
    assert result["contrasts"]["TG-BAG"]["difference_pp"] == 37.5
    assert result["bootstrap"]["resamples"] == 1000
    assert result["bootstrap"]["seed"] == 20261001


def test_conditions_preserve_identity_and_hide_truth():
    p = _load(
        STUDY / "experiments" / "graphdecide_rq2_protocol.py",
        "graphdecide_rq2_protocol_test",
    )
    item = p.MatchedItem(
        "x", "query", ("a", "b"), "a", "target", ("context",),
        ("n0", "n1"), (("n0", "n1"),), (("anchor", "a"),)
    )
    payloads = {c: p.build_condition(item, c) for c in ("T", "G", "TG", "BAG", "A")}
    p.validate_matched_payloads(payloads)
    assert "truth" not in payloads["TG"]
    assert "edges" in payloads["TG"]
    assert "edges" not in payloads["BAG"]
    assert "target_text" not in payloads["A"]


def test_invalid_and_unsupported_are_separate_from_incorrect_candidate():
    p = _load(
        STUDY / "experiments" / "graphdecide_rq2_protocol.py",
        "graphdecide_rq2_choice_test",
    )
    item = p.MatchedItem(
        "x", "q", ("a", "b"), "a", "t", (), (), (), ()
    )
    invalid = p.score_choice(item, "c")
    unsupported = p.score_choice(item, None)
    wrong = p.score_choice(item, "b")
    assert invalid == {"supported": True, "valid": False, "correct": False}
    assert unsupported == {"supported": False, "valid": False, "correct": False}
    assert wrong == {"supported": True, "valid": True, "correct": False}
