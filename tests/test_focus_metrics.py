import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
METRICS = ROOT / "capabilities" / "agent.decision-preserving-context-compressor" / "metrics.py"


def _load():
    spec = importlib.util.spec_from_file_location("focus_metrics_test", METRICS)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_paper_metrics_exact_formula():
    mod = _load()
    inputs = [1000, 1500, 900]
    outputs = [100, 80, 120]
    expected_dependency = (
        ((1000 + 2 * 100) * 100) / 2
        + ((1500 + 2 * 80) * 80) / 2
        + ((900 + 2 * 120) * 120) / 2
    )
    assert mod.peak_tokens(inputs) == 1500
    assert mod.cumulative_tokens(inputs, outputs) == 3700
    assert mod.dependency_cost(inputs, outputs) == expected_dependency


def test_compressed_trace_reduces_context_metrics_when_outputs_fixed():
    mod = _load()
    outputs = [100, 100, 100]
    full = [2000, 3000, 4000]
    compressed = [2000, 2200, 2400]
    assert mod.peak_tokens(compressed) < mod.peak_tokens(full)
    assert mod.cumulative_tokens(compressed, outputs) < mod.cumulative_tokens(full, outputs)
    assert mod.dependency_cost(compressed, outputs) < mod.dependency_cost(full, outputs)
