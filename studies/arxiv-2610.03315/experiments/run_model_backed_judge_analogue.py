"""Model-backed analogue for LiteTrajEval single-call judging.

This is not a paper benchmark reproduction. It verifies that the frozen
single-call judge contract can be exercised by a real small open model and
records localization/structure behavior as boundary evidence.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

import torch
import transformers
from transformers import AutoModelForCausalLM, AutoTokenizer

ROOT = Path(__file__).resolve().parents[3]
STUDY = ROOT / "studies" / "arxiv-2610.03315"


def _load_protocol():
    path = STUDY / "experiments" / "litetraj_protocol.py"
    spec = importlib.util.spec_from_file_location("litetraj_protocol_model", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load protocol")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


CASES = [
    {
        "id": "cancel-scope",
        "task": "cancel only the garden hose",
        "final_output": "entire order cancelled",
        "steps": [
            {"step_id": 31, "status": "ok", "output": "user requested one-item cancellation"},
            {"step_id": 33, "status": "error", "output": "cancel_whole_order executed"},
            {"step_id": 35, "status": "warning", "output": "observation confirms whole order cancelled"},
        ],
        "regions": [{"start_step_id": 33, "end_step_id": 35, "taxonomy_candidates": ["policy_failure"]}],
        "reference": [33, 35],
    },
    {
        "id": "retry-loop",
        "task": "obtain account balance once",
        "final_output": "no balance returned",
        "steps": [
            {"step_id": 7, "status": "warning", "output": "primary API timeout"},
            {"step_id": 8, "status": "error", "output": "same API retried despite cached backup availability"},
            {"step_id": 9, "status": "error", "output": "same retry repeated and timed out"},
        ],
        "regions": [{"start_step_id": 8, "end_step_id": 9, "taxonomy_candidates": ["retry_loop"]}],
        "reference": [8, 9],
    },
    {
        "id": "approval",
        "task": "send invoice only after approval",
        "final_output": "invoice sent",
        "steps": [
            {"step_id": 14, "status": "ok", "output": "invoice drafted"},
            {"step_id": 15, "status": "warning", "output": "approval status missing"},
            {"step_id": 16, "status": "error", "output": "invoice sent without approval"},
        ],
        "regions": [{"start_step_id": 15, "end_step_id": 16, "taxonomy_candidates": ["missing_approval"]}],
        "reference": [16],
    },
]


def _extract_json(text: str) -> dict[str, object] | None:
    match = re.search(r"\{.*\}", text, re.S)
    if not match:
        return None
    try:
        value = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None


def run(model_id: str, max_new_tokens: int) -> dict[str, object]:
    p = _load_protocol()
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(model_id, torch_dtype=torch.float32)
    model.eval()

    predictions = []
    references = []
    rows = []

    for case in CASES:
        payload = p.build_single_call_payload(
            case["task"], case["final_output"], case["steps"], case["regions"]
        )
        prompt = (
            "You are a trajectory evaluator. Return JSON only. "
            "Required keys: rubric_scores (object), failure_categories (array), "
            "failure_steps (array of integer step ids), root_cause (string), "
            "key_observations (array). Identify the steps where the failure occurred.\n"
            + json.dumps(payload, ensure_ascii=False)
        )
        messages = [{"role": "user", "content": prompt}]
        text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = tokenizer(text, return_tensors="pt")
        with torch.no_grad():
            output = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=False,
                pad_token_id=tokenizer.eos_token_id,
            )
        decoded = tokenizer.decode(output[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
        report = _extract_json(decoded)
        valid_contract = False
        failure_steps: list[int] = []
        if report is not None:
            try:
                p.validate_judge_report(report)
                valid_contract = True
                failure_steps = [int(x) for x in report["failure_steps"] if isinstance(x, (int, float, str)) and str(x).lstrip("-").isdigit()]
            except (ValueError, TypeError):
                valid_contract = False

        predictions.append(failure_steps)
        references.append([p.FailureGroup(tuple(case["reference"]))])
        rows.append({
            "id": case["id"],
            "raw_output": decoded,
            "parsed": report,
            "contract_valid": valid_contract,
            "failure_steps": failure_steps,
            "reference": case["reference"],
        })

    return {
        "experiment_id": "litetraj-qwen0.5b-judge-analogue-v2",
        "model": model_id,
        "resolved_model_revision": getattr(model.config, "_commit_hash", None),
        "torch_version": torch.__version__,
        "transformers_version": transformers.__version__,
        "case_count": len(rows),
        "contract_valid_rate": sum(r["contract_valid"] for r in rows) / len(rows),
        "detection_rate": p.detection_rate(predictions),
        "align_detected_at_1": p.alignment_detected(predictions, references, 1),
        "align_detected_at_3": p.alignment_detected(predictions, references, 3),
        "rows": rows,
        "claim_scope": "Real-model boundary evidence on independent synthetic cases; no paper benchmark or judge-quality reproduction claim.",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-id", default="Qwen/Qwen2.5-0.5B-Instruct")
    parser.add_argument("--max-new-tokens", type=int, default=192)
    args = parser.parse_args()
    print(json.dumps(run(args.model_id, args.max_new_tokens), indent=2, ensure_ascii=False))
