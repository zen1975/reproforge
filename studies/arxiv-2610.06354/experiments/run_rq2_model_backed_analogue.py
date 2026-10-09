"""Real-model analogue for GraphDecide RQ2 matched conditions.

This is not a paper benchmark reproduction. It exercises a real small open
model behind the frozen candidate/readout contract on independently authored
matched graph/text items and records condition-wise paired outcomes.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

ROOT = Path(__file__).resolve().parents[3]
STUDY = ROOT / "studies" / "arxiv-2610.06354"


def _load():
    path = STUDY / "experiments" / "graphdecide_rq2_protocol.py"
    spec = importlib.util.spec_from_file_location("graphdecide_rq2_model", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load rq2 protocol")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


ITEMS = [
    {
        "id": "i1",
        "query": "Which candidate is directly connected to target?",
        "candidates": ("c0", "c1"),
        "truth": "c0",
        "target_text": "target is a logistics hub",
        "context_text": ("c0 is a depot", "c1 is a cafe"),
        "nodes": ("target", "c0", "c1"),
        "edges": (("target", "c0"),),
        "anchors": (("depot", "c0"), ("cafe", "c1")),
    },
    {
        "id": "i2",
        "query": "Which candidate is directly connected to target?",
        "candidates": ("c0", "c1"),
        "truth": "c1",
        "target_text": "target is a research lab",
        "context_text": ("c0 is a library", "c1 is an institute"),
        "nodes": ("target", "c0", "c1"),
        "edges": (("target", "c1"),),
        "anchors": (("library", "c0"), ("institute", "c1")),
    },
    {
        "id": "i3",
        "query": "Which candidate shares a graph edge with target?",
        "candidates": ("c0", "c1"),
        "truth": "c0",
        "target_text": "target has neutral descriptive text",
        "context_text": ("c0 neutral text", "c1 neutral text"),
        "nodes": ("target", "c0", "c1"),
        "edges": (("target", "c0"), ("c0", "aux")),
        "anchors": (("anchor0", "c0"), ("anchor1", "c1")),
    },
    {
        "id": "i4",
        "query": "Which candidate shares a graph edge with target?",
        "candidates": ("c0", "c1"),
        "truth": "c1",
        "target_text": "target has neutral descriptive text",
        "context_text": ("c0 neutral text", "c1 neutral text"),
        "nodes": ("target", "c0", "c1"),
        "edges": (("target", "c1"), ("c1", "aux")),
        "anchors": (("anchor0", "c0"), ("anchor1", "c1")),
    },
]


def _choice(text: str) -> str | None:
    matches = re.findall(r"\b(c0|c1)\b", text.lower())
    return matches[-1] if matches else None


def run(model_id: str, max_new_tokens: int) -> dict[str, object]:
    m = _load()
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(model_id, torch_dtype=torch.float32)
    model.eval()

    conditions = ("T", "G", "TG", "BAG", "A")
    by_condition: dict[str, list[bool]] = {c: [] for c in conditions}
    rows = []

    for raw in ITEMS:
        item = m.MatchedItem(
            raw["id"], raw["query"], raw["candidates"], raw["truth"],
            raw["target_text"], raw["context_text"], raw["nodes"], raw["edges"], raw["anchors"]
        )
        payloads = {c: m.build_condition(item, c) for c in conditions}
        m.validate_matched_payloads(payloads)

        for condition in conditions:
            payload = payloads[condition]
            prompt = (
                "Choose exactly one candidate from the candidate list. "
                "Return only c0 or c1. Do not explain.\n"
                + json.dumps(payload, ensure_ascii=False)
            )
            text = tokenizer.apply_chat_template(
                [{"role": "user", "content": prompt}],
                tokenize=False,
                add_generation_prompt=True,
            )
            inputs = tokenizer(text, return_tensors="pt")
            with torch.no_grad():
                output = model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens,
                    do_sample=False,
                    pad_token_id=tokenizer.eos_token_id,
                )
            decoded = tokenizer.decode(
                output[0][inputs["input_ids"].shape[1]:],
                skip_special_tokens=True,
            )
            choice = _choice(decoded)
            score = m.score_choice(item, choice)
            by_condition[condition].append(bool(score["correct"]))
            rows.append({
                "item_id": item.item_id,
                "condition": condition,
                "raw_output": decoded,
                "choice": choice,
                "supported": score["supported"],
                "valid": score["valid"],
                "correct": score["correct"],
            })

    accuracy = {
        c: sum(by_condition[c]) / len(by_condition[c])
        for c in conditions
    }
    contrasts = {
        "TG-BAG_pp": m.paired_difference(by_condition["TG"], by_condition["BAG"]),
        "G-A_pp": m.paired_difference(by_condition["G"], by_condition["A"]),
    }
    return {
        "experiment_id": "graphdecide-rq2-qwen0.5b-analogue-v1",
        "model": model_id,
        "items": len(ITEMS),
        "conditions": list(conditions),
        "accuracy": accuracy,
        "contrasts": contrasts,
        "valid_rate": sum(r["valid"] for r in rows) / len(rows),
        "rows": rows,
        "claim_scope": "Real-model boundary evidence on independent matched synthetic items; no GraphDecide benchmark performance claim.",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-id", default="Qwen/Qwen2.5-0.5B-Instruct")
    parser.add_argument("--max-new-tokens", type=int, default=8)
    args = parser.parse_args()
    print(json.dumps(run(args.model_id, args.max_new_tokens), indent=2, ensure_ascii=False))
