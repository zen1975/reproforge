import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARSER = ROOT / "capabilities" / "agent.decision-preserving-context-compressor" / "parser.py"


def _load():
    spec = importlib.util.spec_from_file_location("focus_parser_test", PARSER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_parser_collects_dependencies_and_last_rescue_set():
    mod = _load()
    text = (
        "Step: use invoice | Depends on: [s_4, s_5]\n"
        "Step: send email | Depends on: [s_1]\n"
        "Rescued Spans: [s_2, s_3] | Reason: avoid repeating failed auth"
    )
    deps, rescued = mod.parse_plan(text)
    assert deps == {"s_1", "s_4", "s_5"}
    assert rescued == {"s_2", "s_3"}


def test_parser_rejects_malformed_span_ids():
    mod = _load()
    try:
        mod.parse_plan("Step: x | Depends on: [span1]")
    except ValueError:
        pass
    else:
        raise AssertionError("malformed span id must fail closed")


def test_parser_fails_when_model_omits_dependency_format():
    mod = _load()
    try:
        mod.parse_plan("[s_7] Thought: continue history | Action: noop")
    except ValueError as exc:
        assert "no dependency citation" in str(exc)
    else:
        raise AssertionError("missing dependency citations must fail closed")
