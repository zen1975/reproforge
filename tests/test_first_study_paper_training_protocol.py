import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT / "studies" / "arxiv-2610.03213"


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_sft_protocol_prepare_matches_paper_counts_and_balance():
    mod = _load(
        STUDY / "experiments" / "prepare_sft_protocol_data.py",
        "sft_protocol_prepare",
    )
    train, validation, summary = mod.prepare()
    assert len(train) == 4404
    assert len(validation) == 1136
    assert summary["train_positive"] == 2202
    assert summary["train_negative"] == 2202
    assert summary["validation_positive"] == 568
    assert summary["validation_negative"] == 568


def test_grpo_reward_exposes_components_without_invented_weights():
    mod = _load(
        STUDY / "experiments" / "grpo_reward_components.py",
        "grpo_reward_components_test",
    )
    good = mod.reward_components(
        '{"reasoning":"needed","appropriate":true}',
        True,
    )
    assert good["schema_compliance"] == 1
    assert good["label_correctness"] == 1
    assert good["invalid_output"] == 0
    assert good["published_weighted_total_available"] is False

    with pytest.raises(RuntimeError, match="does not publish reward weights"):
        mod.combine_components(good)
