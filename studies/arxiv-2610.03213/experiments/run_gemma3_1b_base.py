"""Small protocol-equivalent Gemma 3 1B Base evaluation.

Requires authorized access to google/gemma-3-1b-it.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

ROOT = Path(__file__).resolve().parents[3]
STUDY = ROOT / "studies" / "arxiv-2610.03213"
MODEL_ID = "google/gemma-3-1b-it"
MAX_NEW_TOKENS = 96


def _load_metrics():
    import importlib.util
    path = STUDY / "experiments" / "paper_style_metrics.py"
    spec = importlib.util.spec_from_file_location("paper_metrics", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load metrics")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def prompt(row):
    return (
        "You are a task-tool relevance classifier. Evaluate only whether the candidate "
        "tool is appropriate for the task. Return exactly one JSON object with keys "
        '"reasoning" and "appropriate", where appropriate is true or false.\n\n'
        f'Task: {row["task"]}\n'
        f'Tool name: {row["tool_name"]}\n'
        f'Tool description: {row["tool_description"]}\n'
    )


def run():
    token = os.environ.get("HF_TOKEN")
    if not token:
        raise RuntimeError("HF_TOKEN is required for official Gemma access")

    data = json.loads(
        (STUDY / "experiments" / "protocol_equivalent_mcp_v1.json").read_text()
    )
    test_rows = [r for r in data["rows"] if r["pool"] == "test"][:48]

    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, token=token)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        token=token,
        torch_dtype=torch.float32,
        low_cpu_mem_usage=True,
    )
    model.eval()

    outputs = []
    for row in test_rows:
        messages = [{"role": "user", "content": prompt(row)}]
        text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        batch = tokenizer(text, return_tensors="pt")
        with torch.no_grad():
            generated = model.generate(
                **batch,
                max_new_tokens=MAX_NEW_TOKENS,
                do_sample=False,
            )
        completion = tokenizer.decode(
            generated[0][batch["input_ids"].shape[1]:],
            skip_special_tokens=True,
        ).strip()
        outputs.append(completion)

    metrics = _load_metrics().evaluate([r["label"] for r in test_rows], outputs)
    return {
        "model_id": MODEL_ID,
        "condition": "Base",
        "protocol_dataset": data["dataset_id"],
        "sample_count": len(test_rows),
        "decoding": {"do_sample": False, "max_new_tokens": MAX_NEW_TOKENS},
        "metrics": metrics,
        "paper_reference_gemma3_1b_base": {
            "accuracy": 0.6159,
            "f1": 0.6674,
            "failed_parses": 103,
        },
        "boundary": (
            "Independent protocol-equivalent synthetic sample, not the paper test set. "
            "Do not compare as an exact reproduction."
        ),
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
