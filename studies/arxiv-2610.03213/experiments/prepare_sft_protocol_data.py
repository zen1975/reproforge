"""Prepare paper-sized, class-balanced SFT protocol data.

This recreates the *shape* of the paper's SFT stage using independent synthetic
examples. It does not reproduce ASTRA data or the unpublished seed/GEPA prompt.
"""

from __future__ import annotations

import importlib.util
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
STUDY = ROOT / "studies" / "arxiv-2610.03213"
OUT_DIR = STUDY / "experiments" / "generated"
TRAIN_OUT = OUT_DIR / "sft_train_4404.jsonl"
VAL_OUT = OUT_DIR / "sft_validation_1136.jsonl"
SUMMARY_OUT = OUT_DIR / "sft_protocol_summary.json"
SEED = 261003213

SEED_PROMPT = (
    "You are a task-tool relevance classifier. Determine whether the candidate "
    "tool is appropriate for the task. Return exactly one JSON object with keys "
    '"reasoning" and "appropriate", where appropriate is a boolean.'
)


def _load_generator():
    path = STUDY / "experiments" / "generate_protocol_equivalent_mcp.py"
    spec = importlib.util.spec_from_file_location("protocol_gen_for_sft", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load protocol generator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _balanced_sample(rows, size, rng):
    if size % 2:
        raise ValueError("balanced sample size must be even")
    half = size // 2
    positives = [row for row in rows if row["label"] == 1]
    negatives = [row for row in rows if row["label"] == 0]
    if len(positives) < half or len(negatives) < half:
        raise ValueError(
            f"insufficient rows for balanced sample: +{len(positives)} -{len(negatives)}"
        )
    sampled = rng.sample(positives, half) + rng.sample(negatives, half)
    rng.shuffle(sampled)
    return sampled


def _format(row):
    user = (
        f'{SEED_PROMPT}\n\nTask: {row["task"]}\n'
        f'Tool name: {row["tool_name"]}\n'
        f'Tool description: {row["tool_description"]}\n'
    )
    completion = json.dumps(row["target_response"], separators=(",", ":"), sort_keys=True)
    return {
        "prompt": user,
        "completion": completion,
        "label": row["label"],
        "pool": row["pool"],
        "group_id": row["group_id"],
        "set_type": row["set_type"],
    }


def prepare():
    generator = _load_generator()
    data = generator.generate(
        train_groups_per_n=500,
        validation_groups_per_n=140,
        test_groups_per_n=80,
    )
    rng = random.Random(SEED)
    train_rows = [row for row in data["rows"] if row["pool"] == "train"]
    val_rows = [row for row in data["rows"] if row["pool"] == "validation"]

    train = [_format(row) for row in _balanced_sample(train_rows, 4404, rng)]
    validation = [_format(row) for row in _balanced_sample(val_rows, 1136, rng)]

    return train, validation, {
        "dataset_id": "independent-sft-protocol-v1",
        "seed": SEED,
        "train_count": len(train),
        "validation_count": len(validation),
        "train_positive": sum(row["label"] for row in train),
        "train_negative": sum(1 - row["label"] for row in train),
        "validation_positive": sum(row["label"] for row in validation),
        "validation_negative": sum(1 - row["label"] for row in validation),
        "paper_shape": {
            "train_count": 4404,
            "validation_count": 1136,
            "class_balanced": True,
            "response_schema": {"reasoning": "string", "appropriate": "boolean"},
        },
        "divergences": [
            "Independent synthetic cross-MCP data replaces ASTRA single-tool examples.",
            "Paper seed/GEPA prompt text is not published in the paper; ReproForge uses an independent seed prompt.",
            "This data preparation is protocol-equivalent evidence, not paper-dataset reproduction.",
        ],
    }


def main():
    train, validation, summary = prepare()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    TRAIN_OUT.write_text("\n".join(json.dumps(row, sort_keys=True) for row in train) + "\n")
    VAL_OUT.write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in validation) + "\n"
    )
    SUMMARY_OUT.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
