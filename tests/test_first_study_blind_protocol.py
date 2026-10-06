import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT / "studies" / "arxiv-2610.03213"


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_blind_families_are_disjoint_from_train_dev_test_families():
    train_mod = _load(
        STUDY / "experiments" / "generate_task_tool_sft_dataset.py",
        "task_tool_train_gen",
    )
    blind_mod = _load(
        STUDY / "experiments" / "generate_task_tool_blind_v1.py",
        "task_tool_blind_gen",
    )
    prior = {
        family
        for families in train_mod.SPLITS.values()
        for family in families
    }
    blind = set(blind_mod.FAMILIES)
    assert prior.isdisjoint(blind)


def test_blind_benchmark_is_balanced_and_frozen_shape():
    blind_mod = _load(
        STUDY / "experiments" / "generate_task_tool_blind_v1.py",
        "task_tool_blind_shape",
    )
    data = blind_mod.generate()
    assert len(data["rows"]) == 144
    assert data["families"] == ["commerce", "documents", "identity", "notifications"]
    positives = sum(row["label"] for row in data["rows"])
    assert positives == 48
    assert len(data["rows"]) - positives == 96
