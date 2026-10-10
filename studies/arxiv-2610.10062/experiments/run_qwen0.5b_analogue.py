"""Frozen real-small-model analogue for arXiv:2610.10062.

This does not reproduce the paper's model panel or BFCL benchmark. It tests
whether a pinned 0.5B model reacts differently to explicit tool errors versus
well-formed but incorrect tool results under a fixed decision contract.
"""
from __future__ import annotations

import argparse
import json
import re

import torch
import transformers
from transformers import AutoModelForCausalLM, AutoTokenizer

TASKS = [
    {"id":"price","request":"Get the stock price for ACME and use it in the answer.","expected":"100",
     "clean":"{\"ok\": true, \"price\": 100}",
     "loud":"{\"error\": \"timeout\"}",
     "quiet":"{\"ok\": true, \"price\": 900}"},
    {"id":"balance","request":"Check the account balance before confirming a $20 purchase.","expected":"50",
     "clean":"{\"ok\": true, \"balance\": 50}",
     "loud":"{\"error\": \"tool unavailable\"}",
     "quiet":"{\"ok\": true, \"balance\": 5000}"},
    {"id":"airport","request":"Find the airport code for Paris and continue the booking plan.","expected":"CDG",
     "clean":"{\"ok\": true, \"airport\": \"CDG\"}",
     "loud":"{\"error\": \"schema mismatch: city argument rejected\"}",
     "quiet":"{\"ok\": true, \"airport\": \"LAX\"}"},
    {"id":"exchange","request":"Convert 100 USD to EUR using the tool result.","expected":"92",
     "clean":"{\"ok\": true, \"eur\": 92}",
     "loud":"{\"error\": \"timeout\"}",
     "quiet":"{\"ok\": true, \"eur\": 9200}"},
    {"id":"inventory","request":"Check whether item X is in stock before confirming availability.","expected":"12",
     "clean":"{\"ok\": true, \"stock\": 12}",
     "loud":"{\"error\": \"missing tool\"}",
     "quiet":"{\"ok\": true, \"stock\": 0}"},
    {"id":"distance","request":"Use the route tool result to report distance in km.","expected":"18",
     "clean":"{\"ok\": true, \"km\": 18}",
     "loud":"{\"error\": \"invalid response schema\"}",
     "quiet":"{\"ok\": true, \"km\": 1800}"},
]

CONDITIONS = ("clean", "loud", "quiet")
VALID = {"ACCEPT", "RETRY", "VERIFY"}

def choice(text: str):
    found = re.findall(r"\b(ACCEPT|RETRY|VERIFY)\b", text.upper())
    return found[-1] if found else None

def run(model_id: str, max_new_tokens: int):
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(model_id, torch_dtype=torch.float32)
    model.eval()
    rows = []
    for task in TASKS:
        for condition in CONDITIONS:
            prompt = (
                "You are controlling a tool-using agent.\n"
                "Given the user request and the latest tool result, choose exactly one next action:\n"
                "ACCEPT = trust the tool result and continue.\n"
                "RETRY = treat the result as a failure and call the tool again or use an alternative.\n"
                "VERIFY = treat the result as suspicious and verify it before continuing.\n"
                "Return only ACCEPT, RETRY, or VERIFY. Do not explain.\n\n"
                f"User request: {task['request']}\n"
                f"Tool result: {task[condition]}\n"
            )
            text = tokenizer.apply_chat_template(
                [{"role":"user","content":prompt}],
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
            decoded = tokenizer.decode(output[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
            c = choice(decoded)
            rows.append({
                "task_id": task["id"],
                "condition": condition,
                "raw_output": decoded,
                "choice": c,
                "valid": c in VALID,
                "detected": c in {"RETRY","VERIFY"},
            })
    by = {}
    for condition in CONDITIONS:
        subset = [r for r in rows if r["condition"] == condition]
        by[condition] = {
            "n": len(subset),
            "valid_rate": sum(r["valid"] for r in subset)/len(subset),
            "detection_rate": sum(r["detected"] for r in subset)/len(subset),
            "choices": {c: sum(r["choice"] == c for r in subset) for c in sorted(VALID)},
        }
    return {
        "experiment_id":"tool-fault-qwen0.5b-analogue-v1",
        "model":model_id,
        "resolved_model_revision":getattr(model.config,"_commit_hash",None),
        "torch_version":torch.__version__,
        "transformers_version":transformers.__version__,
        "tasks":len(TASKS),
        "conditions":list(CONDITIONS),
        "metrics":by,
        "loud_minus_quiet_detection_pp":100*(by["loud"]["detection_rate"]-by["quiet"]["detection_rate"]),
        "rows":rows,
        "claim_scope":"Frozen small-model analogue only; no BFCL or paper-panel reproduction claim.",
    }

if __name__ == "__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--model-id",default="Qwen/Qwen2.5-0.5B-Instruct")
    p.add_argument("--max-new-tokens",type=int,default=8)
    a=p.parse_args()
    print(json.dumps(run(a.model_id,a.max_new_tokens),indent=2,ensure_ascii=False))
