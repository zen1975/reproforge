"""Deterministic synthetic data for the OPST wrong-answer robustness analogue.

Paper Table 5c disables both filters and replaces a fraction p of candidate
answers with wrong ones. This generator builds four-option arithmetic
questions with known ground truth so that "wrong" is well defined. Everything
here is a ReproForge choice; the paper's generated data are not published.

Usage (from repository root):
    python studies/arxiv-2610.32770/experiments/opst_wr_data.py [--write]
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STUDY = HERE.parent
FIXTURE = STUDY / "fixtures" / "opst_wr_v1.json"

EVALUATION_ID = "opst-wrong-answer-robustness-qwen0.5b-v1"
LETTERS = "ABCD"
SPLIT_SEEDS = {"heldout": 32770001, "calibration": 32770002, "smoke": 32770003}
TRAIN_SEEDS = [101, 202, 303]
SIZES = {"heldout": 200, "calibration": 200, "smoke": 8, "train": 64}
WRONG_FRACTION = 0.75
OFFSETS = [-11, -10, -9, -2, -1, 1, 2, 9, 10, 11]


def make_question(rng: random.Random) -> dict:
    if rng.random() < 0.5:
        a, b = rng.randint(100, 899), rng.randint(100, 899)
        expr, gold = f"{a} + {b}", a + b
    else:
        a, b = rng.randint(12, 98), rng.randint(3, 9)
        expr, gold = f"{a} * {b}", a * b
    values = [gold] + [gold + d for d in rng.sample(OFFSETS, 3)]
    rng.shuffle(values)
    options = [str(v) for v in values]
    return {
        "expression": expr,
        "question": f"What is {expr}?",
        "options": options,
        "gold": LETTERS[values.index(gold)],
    }


def candidate(q: dict, letter: str) -> str:
    """z = (r, a): a one-line rationale and answer consistent with `letter`."""
    value = q["options"][LETTERS.index(letter)]
    return f"{q['expression']} = {value}. Answer: {letter}"


def _draw(rng: random.Random, n: int, seen: set[str]) -> list[dict]:
    out = []
    while len(out) < n:
        q = make_question(rng)
        if q["question"] in seen:
            continue
        seen.add(q["question"])
        out.append(q)
    return out


def build() -> dict:
    seen: set[str] = set()
    splits = {}
    for name in ("heldout", "calibration", "smoke"):
        rng = random.Random(SPLIT_SEEDS[name])
        splits[name] = [{"id": f"{name}-{i:03d}", **q} for i, q in enumerate(_draw(rng, SIZES[name], seen))]
    train = {}
    n_wrong = round(WRONG_FRACTION * SIZES["train"])
    for seed in TRAIN_SEEDS:
        rng = random.Random(seed)
        items = _draw(rng, SIZES["train"], seen)
        wrong_idx = set(rng.sample(range(len(items)), n_wrong))
        rows = []
        for i, q in enumerate(items):
            wrong_letter = rng.choice([x for x in LETTERS if x != q["gold"]])
            rows.append({
                "id": f"train{seed}-{i:03d}",
                **q,
                "z_correct": candidate(q, q["gold"]),
                "corrupt_at_p075": i in wrong_idx,
                "z_wrong": candidate(q, wrong_letter),
                "wrong_letter": wrong_letter,
            })
        train[str(seed)] = rows
    return {
        "evaluation_id": EVALUATION_ID,
        "description": (
            "Synthetic four-option arithmetic questions (3-digit addition, 2-digit x 1-digit "
            "multiplication). Distractors are gold +/- {1,2,9,10,11}. z = one-line rationale + "
            "answer letter; a wrong z replaces both the rationale value and the letter so they stay "
            "consistent. ReproForge construction, not paper data."
        ),
        "wrong_fraction": WRONG_FRACTION,
        "train_seeds": TRAIN_SEEDS,
        "splits": splits,
        "train": train,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    text = json.dumps(build(), indent=1, sort_keys=True) + "\n"
    if args.write:
        FIXTURE.write_text(text)
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
