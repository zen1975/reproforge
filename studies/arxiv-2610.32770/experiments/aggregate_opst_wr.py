"""Apply the pre-registered C6 criteria to the 12 cell results.

Usage (from repository root):
    python studies/arxiv-2610.32770/experiments/aggregate_opst_wr.py <dir-with-cell-json> [--run-id N] [--write]

Standard library only. Criteria are frozen in manifest.yaml (C6); the
thresholds below must not change under this evaluation id.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STUDY = HERE.parent

EVALUATION_ID = "opst-wrong-answer-robustness-qwen0.5b-v1"
METHODS = ("sft", "opst")
PS = (0.0, 0.75)
SEEDS = (101, 202, 303)
MANIPULATION_MIN_DROP = 0.02
ACTIVITY_MIN_SHIFT = 0.02
BASE_ACC_RANGE = (0.30, 0.90)


def mean(xs: list[float]) -> float:
    return sum(xs) / len(xs)


def aggregate(cells: list[dict]) -> dict:
    by_key = {(c["method"], c["p"], c["seed"]): c for c in cells}
    expected = {(mth, p, s) for mth in METHODS for p in PS for s in SEEDS}
    missing = sorted(expected - set(by_key))
    if missing or len(cells) != len(expected):
        raise ValueError(f"expected exactly 12 cells, missing {missing}")
    if any(c["mode"] != "frozen" or c["evaluation_id"] != EVALUATION_ID for c in cells):
        raise ValueError("all cells must be frozen runs of this evaluation id")
    if len({json.dumps(c["hashes"], sort_keys=True) for c in cells}) != 1:
        raise ValueError("cells were produced by different runner/config/fixture versions")

    base_logp = {round(c["before"]["heldout"]["mean_gold_logprob"], 6) for c in cells}
    base_acc = cells[0]["before"]["heldout"]["accuracy"]
    base_consistent = len(base_logp) == 1

    def after(mth, p, s, split="heldout", key="mean_gold_logprob"):
        return by_key[(mth, p, s)]["after"][split][key]

    per_seed = []
    for s in SEEDS:
        drop_sft = after("sft", 0.0, s) - after("sft", 0.75, s)
        drop_opst = after("opst", 0.0, s) - after("opst", 0.75, s)
        c = by_key[("opst", 0.0, s)]
        shift = abs(c["after"]["train_gold"]["mean_gold_logprob"] - c["before"]["train_gold"]["mean_gold_logprob"])
        per_seed.append({
            "seed": s,
            "drop_sft": drop_sft,
            "drop_opst": drop_opst,
            "opst_drop_smaller": drop_opst < drop_sft,
            "opst_p0_train_gold_shift": shift,
        })

    mean_drop_sft = mean([r["drop_sft"] for r in per_seed])
    mean_drop_opst = mean([r["drop_opst"] for r in per_seed])
    guards = {
        "base_eval_identical_across_cells": base_consistent,
        "base_accuracy_in_range": BASE_ACC_RANGE[0] <= base_acc <= BASE_ACC_RANGE[1],
        "sft_manipulation_bites": mean_drop_sft >= MANIPULATION_MIN_DROP and sum(r["drop_sft"] > 0 for r in per_seed) >= 2,
        "opst_active": mean([r["opst_p0_train_gold_shift"] for r in per_seed]) >= ACTIVITY_MIN_SHIFT,
    }
    seeds_opst_smaller = sum(r["opst_drop_smaller"] for r in per_seed)
    robust = seeds_opst_smaller >= 2 and mean_drop_sft - mean_drop_opst > 0
    if not all(guards.values()):
        verdict = "INCONCLUSIVE"
    else:
        verdict = "PASS" if robust else "FAIL"

    table = {
        f"{mth}_p{p}": {
            "mean_gold_logprob": mean([after(mth, p, s) for s in SEEDS]),
            "accuracy": mean([after(mth, p, s, key="accuracy") for s in SEEDS]),
        }
        for mth in METHODS
        for p in PS
    }
    return {
        "claim_id": "C6-wrong-answer-robustness-analogue",
        "evaluation_id": EVALUATION_ID,
        "base_heldout": {"mean_gold_logprob": cells[0]["before"]["heldout"]["mean_gold_logprob"], "accuracy": base_acc},
        "per_seed": per_seed,
        "mean_drop_sft": mean_drop_sft,
        "mean_drop_opst": mean_drop_opst,
        "mean_drop_difference_sft_minus_opst": mean_drop_sft - mean_drop_opst,
        "seeds_opst_drop_smaller": seeds_opst_smaller,
        "guards": guards,
        "heldout_table": table,
        "thresholds": {
            "manipulation_min_mean_drop_nats": MANIPULATION_MIN_DROP,
            "opst_activity_min_train_gold_shift_nats": ACTIVITY_MIN_SHIFT,
            "base_accuracy_range": list(BASE_ACC_RANGE),
        },
        "verdict": verdict,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("cells_dir", type=Path)
    parser.add_argument("--run-id", type=int)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    paths = sorted(args.cells_dir.rglob("*.json"))
    cells = [json.loads(p.read_text()) for p in paths]
    result = aggregate(cells)
    result["workflow_run"] = args.run_id
    result["cell_files"] = {p.name: "sha256:" + hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    result["hashes"] = cells[0]["hashes"]
    result["environment"] = cells[0]["environment"]
    result["not_paper_evidence"] = (
        "Qwen2.5-0.5B LoRA on synthetic arithmetic, one round, 32 steps. Tests the direction of the "
        "Table 5c mechanism only; no MMLU, Gemma 4 or paper-scale number is reproduced."
    )
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.write:
        out = STUDY / "evidence"
        (out / "opst_wr_qwen0.5b_v1.result.json").write_text(text)
        cell_out = out / "opst_wr_qwen0.5b_v1_cells"
        cell_out.mkdir(exist_ok=True)
        for p in paths:
            (cell_out / p.name).write_bytes(p.read_bytes())
    sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
