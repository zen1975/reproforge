import importlib.util
import json
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


def test_protocol_dataset_validation_uses_train_server_pool_and_test_is_disjoint():
    mod = _load(
        STUDY / "experiments" / "generate_protocol_equivalent_mcp.py",
        "protocol_gen_v2",
    )
    data = mod.generate()
    train_servers = set(mod.TRAIN_SERVERS)
    test_servers = set(mod.TEST_SERVERS)
    assert train_servers.isdisjoint(test_servers)
    for row in data["rows"]:
        if row["pool"] in {"train", "validation"}:
            assert row["server"] in train_servers
        else:
            assert row["pool"] == "test"
            assert row["server"] in test_servers


def test_protocol_dataset_has_structured_training_target():
    mod = _load(
        STUDY / "experiments" / "generate_protocol_equivalent_mcp.py",
        "protocol_targets",
    )
    data = mod.generate()
    assert data["rows"]
    for row in data["rows"][:50]:
        target = row["target_response"]
        assert isinstance(target["reasoning"], str)
        assert isinstance(target["appropriate"], bool)
        assert target["appropriate"] is bool(row["label"])


def test_paper_style_metrics_separate_parse_failure_from_classification_accuracy():
    mod = _load(
        STUDY / "experiments" / "paper_style_metrics.py",
        "paper_style_metrics_test",
    )
    result = mod.evaluate(
        [1, 0, 1],
        [
            '{"reasoning":"ok","appropriate":true}',
            '{"reasoning":"ok","appropriate":false}',
            "not-json",
        ],
    )
    assert result["failed_parses"] == 1
    assert result["accuracy"] == 1.0
    assert result["e2e_accuracy"] == 2 / 3


def test_paper_protocol_configuration_is_exactly_bounded():
    config = json.loads(
        (STUDY / "experiments" / "paper_protocol_config_v1.json").read_text()
    )
    assert config["sft"]["lora_r"] == 32
    assert config["sft"]["lora_alpha"] == 64
    assert config["sft"]["epochs"] == 3
    assert config["grpo"]["responses_per_prompt"] == 16
    assert config["grpo"]["kl_beta"] == 0.001
    assert config["paper_hardware"] == "single H100 GPU"
