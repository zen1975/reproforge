import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT / "studies" / "arxiv-2610.32770"
EXP = STUDY / "experiments"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


data = _load("opst_wr_data", EXP / "opst_wr_data.py")
agg = _load("aggregate_opst_wr", EXP / "aggregate_opst_wr.py")
FIXTURE = json.loads((STUDY / "fixtures" / "opst_wr_v1.json").read_text())
CONFIG = json.loads((EXP / "opst_wr_config_v1.json").read_text())


def test_fixture_is_reproducible_from_generator():
    text = json.dumps(data.build(), indent=1, sort_keys=True) + "\n"
    assert text == (STUDY / "fixtures" / "opst_wr_v1.json").read_text()


def test_splits_are_disjoint_and_sized():
    questions = [q["question"] for split in FIXTURE["splits"].values() for q in split]
    questions += [r["question"] for rows in FIXTURE["train"].values() for r in rows]
    assert len(questions) == len(set(questions))
    assert {k: len(v) for k, v in FIXTURE["splits"].items()} == {"heldout": 200, "calibration": 200, "smoke": 8}
    assert all(len(rows) == 64 for rows in FIXTURE["train"].values())


def test_corruption_is_exactly_75_percent_and_consistent():
    for rows in FIXTURE["train"].values():
        assert sum(r["corrupt_at_p075"] for r in rows) == 48
        for r in rows:
            assert r["wrong_letter"] != r["gold"]
            assert r["z_correct"].endswith(f"Answer: {r['gold']}")
            assert r["z_wrong"].endswith(f"Answer: {r['wrong_letter']}")
            assert r["options"][data.LETTERS.index(r["wrong_letter"])] in r["z_wrong"]
            assert r["options"][data.LETTERS.index(r["gold"])] in r["z_correct"]


def test_every_config_value_declares_its_source():
    values = CONFIG["values"]
    assert all(v["source"] in {"paper", "reproforge"} for v in values.values())
    paper = {k for k, v in values.items() if v["source"] == "paper"}
    assert paper == {"alpha", "ema_beta", "loss_aggregation", "filters", "wrong_fractions"}


def test_runner_literals_match_config():
    src = (EXP / "run_opst_wr_analogue.py").read_text()
    assert "r=8, lora_alpha=16, lora_dropout=0.0" in src
    assert "lr=2e-4, weight_decay=0.0" in src
    assert '["q_proj", "k_proj", "v_proj", "o_proj"]' in src
    assert "temperature=1.0" in src and "top_p=1.0" in src and "top_k=0" in src


def _cell(method, p, seed, after_logp, train_shift=0.1, base_acc=0.6):
    return {
        "evaluation_id": agg.EVALUATION_ID,
        "mode": "frozen",
        "method": method,
        "p": p,
        "seed": seed,
        "hashes": {"runner_sha256": "x"},
        "before": {
            "heldout": {"mean_gold_logprob": -1.0, "accuracy": base_acc},
            "train_gold": {"mean_gold_logprob": -1.0},
        },
        "after": {
            "heldout": {"mean_gold_logprob": after_logp, "accuracy": 0.5},
            "train_gold": {"mean_gold_logprob": -1.0 + train_shift},
        },
    }


def _cells(sft_drop, opst_drop, **kw):
    cells = []
    for s in agg.SEEDS:
        cells += [
            _cell("sft", 0.0, s, -0.9, **kw),
            _cell("sft", 0.75, s, -0.9 - sft_drop, **kw),
            _cell("opst", 0.0, s, -0.9, **kw),
            _cell("opst", 0.75, s, -0.9 - opst_drop, **kw),
        ]
    return cells


def test_aggregate_verdicts():
    assert agg.aggregate(_cells(0.3, 0.05))["verdict"] == "PASS"
    assert agg.aggregate(_cells(0.3, 0.4))["verdict"] == "FAIL"
    assert agg.aggregate(_cells(0.001, 0.0))["verdict"] == "INCONCLUSIVE"
    assert agg.aggregate(_cells(0.3, 0.0, train_shift=0.0))["verdict"] == "INCONCLUSIVE"
    assert agg.aggregate(_cells(0.3, 0.05, base_acc=0.97))["verdict"] == "INCONCLUSIVE"


def test_aggregate_rejects_incomplete_or_mixed_runs():
    cells = _cells(0.3, 0.05)
    with pytest.raises(ValueError):
        agg.aggregate(cells[:-1])
    mixed = copy.deepcopy(cells)
    mixed[0]["hashes"] = {"runner_sha256": "y"}
    with pytest.raises(ValueError):
        agg.aggregate(mixed)
    smoke = copy.deepcopy(cells)
    smoke[0]["mode"] = "smoke"
    with pytest.raises(ValueError):
        agg.aggregate(smoke)


def test_frozen_files_match_preregistration():
    prereg = json.loads((EXP / "opst_wr_preregistration_v1.json").read_text())
    for rel, digest in prereg["frozen_files_sha256"].items():
        assert hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() == digest, rel


def test_committed_c6_result_reaggregates_from_cells():
    cells_dir = STUDY / "evidence" / "opst_wr_qwen0.5b_v1_cells"
    committed = json.loads((STUDY / "evidence" / "opst_wr_qwen0.5b_v1.result.json").read_text())
    cells = [json.loads(p.read_text()) for p in sorted(cells_dir.glob("*.json"))]
    result = agg.aggregate(cells)
    assert all(committed[k] == v for k, v in result.items())
    assert committed["verdict"] == "INCONCLUSIVE"
    for name, digest in committed["cell_files"].items():
        assert "sha256:" + hashlib.sha256((cells_dir / name).read_bytes()).hexdigest() == digest
