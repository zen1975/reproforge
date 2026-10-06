import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT / "studies" / "arxiv-2610.03213"


def _load_gen():
    path = STUDY / "experiments" / "generate_protocol_equivalent_mcp.py"
    spec = importlib.util.spec_from_file_location("protocol_gen", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_protocol_dataset_uses_server_disjoint_8_4_split():
    mod = _load_gen()
    assert len(mod.TRAIN_SERVERS) == 8
    assert len(mod.TEST_SERVERS) == 4
    assert set(mod.TRAIN_SERVERS).isdisjoint(mod.TEST_SERVERS)


def test_protocol_dataset_has_correct_wrong_and_null_candidate_rows():
    data = _load_gen().generate()
    kinds = {row["set_type"] for row in data["rows"]}
    assert kinds == {"correct", "wrong", "null"}
    assert all(row["label"] == (1 if row["set_type"] == "correct" else 0) for row in data["rows"])


def test_each_group_is_cross_server_and_candidate_level_labeled():
    data = _load_gen().generate()
    groups = {}
    for row in data["rows"]:
        groups.setdefault(row["group_id"], []).append(row)
    assert groups
    for rows in groups.values():
        correct = [row for row in rows if row["set_type"] == "correct"]
        n = len(correct)
        assert n in {2, 3}
        assert len({row["server"] for row in correct}) == n
        assert len(rows) == n * 3
