"""Frozen response-propagation analogue for arXiv:2610.10265.

The memory condition is externally authored and labeled. The model only produces
the answer. We score whether it emits the current, stale, or wrong-person value.
"""
from __future__ import annotations

import argparse
import json

import torch
import transformers
from transformers import AutoModelForCausalLM, AutoTokenizer

CASES = [
    {
        "id":"m1","participant":"Alex Chen / Orion","question":"What time is Alex's standup?",
        "current":"10:45","stale":"09:30","wrong":"08:15",
        "clean":["Alex Chen on Orion: standup is at 10:45."],
        "stale_block":["Alex Chen on Orion: standup is at 10:45.","Alex Chen on Orion: standup was at 09:30."],
        "wrong_block":["Alex Chen on Orion: standup is at 10:45.","Alex Chen on Atlas: standup is at 08:15."],
    },
    {
        "id":"m2","participant":"Maya Lee / Cedar","question":"Which room is Maya's weekly sync in?",
        "current":"Room 7","stale":"Room 3","wrong":"Room 12",
        "clean":["Maya Lee on Cedar: weekly sync is in Room 7."],
        "stale_block":["Maya Lee on Cedar: weekly sync is in Room 7.","Maya Lee on Cedar: weekly sync was in Room 3."],
        "wrong_block":["Maya Lee on Cedar: weekly sync is in Room 7.","Maya Lee on Birch: weekly sync is in Room 12."],
    },
    {
        "id":"m3","participant":"Sam Patel / Nova","question":"What is Sam's current lunch preference?",
        "current":"soba","stale":"ramen","wrong":"tacos",
        "clean":["Sam Patel on Nova: lunch preference is soba."],
        "stale_block":["Sam Patel on Nova: lunch preference is soba.","Sam Patel on Nova: lunch preference used to be ramen."],
        "wrong_block":["Sam Patel on Nova: lunch preference is soba.","Sam Patel on Vega: lunch preference is tacos."],
    },
    {
        "id":"m4","participant":"Jordan Kim / Apollo","question":"What is Jordan's current delivery day?",
        "current":"Thursday","stale":"Tuesday","wrong":"Saturday",
        "clean":["Jordan Kim on Apollo: delivery day is Thursday."],
        "stale_block":["Jordan Kim on Apollo: delivery day is Thursday.","Jordan Kim on Apollo: delivery day used to be Tuesday."],
        "wrong_block":["Jordan Kim on Apollo: delivery day is Thursday.","Jordan Kim on Mercury: delivery day is Saturday."],
    },
]
CONDITIONS=("clean","stale_block","wrong_block")

def ask(model,tok,prompt,max_new_tokens):
    text=tok.apply_chat_template(
        [{"role":"user","content":prompt}],tokenize=False,add_generation_prompt=True
    )
    inputs=tok(text,return_tensors="pt")
    with torch.no_grad():
        out=model.generate(
            **inputs,max_new_tokens=max_new_tokens,do_sample=False,
            pad_token_id=tok.eos_token_id,
        )
    return tok.decode(out[0][inputs["input_ids"].shape[1]:],skip_special_tokens=True).strip()

def contains(text,value):
    return value.lower() in text.lower()

def run(model_id,max_new_tokens):
    tok=AutoTokenizer.from_pretrained(model_id)
    model=AutoModelForCausalLM.from_pretrained(model_id,torch_dtype=torch.float32)
    model.eval()
    rows=[]
    for case in CASES:
        for cond in CONDITIONS:
            block="\n".join(f"- {x}" for x in case[cond])
            prompt=(
                "Answer using only the memory block. Return only the value, no explanation.\n"
                f"Current conversation participant/context: {case['participant']}\n"
                f"Memory block:\n{block}\n"
                f"Question: {case['question']}\n"
            )
            raw=ask(model,tok,prompt,max_new_tokens)
            flags={
                "current":contains(raw,case["current"]),
                "stale":contains(raw,case["stale"]),
                "wrong_person":contains(raw,case["wrong"]),
            }
            rows.append({"case_id":case["id"],"condition":cond,"raw_output":raw,**flags})
    summary={}
    for cond in CONDITIONS:
        s=[r for r in rows if r["condition"]==cond]
        summary[cond]={
            "n":len(s),
            "current_rate":sum(r["current"] for r in s)/len(s),
            "stale_rate":sum(r["stale"] for r in s)/len(s),
            "wrong_person_rate":sum(r["wrong_person"] for r in s)/len(s),
        }
    return {
        "experiment_id":"memory-qwen0.5b-response-propagation-v1",
        "model":model_id,
        "resolved_model_revision":getattr(model.config,"_commit_hash",None),
        "torch_version":torch.__version__,
        "transformers_version":transformers.__version__,
        "cases":len(CASES),
        "conditions":list(CONDITIONS),
        "summary":summary,
        "rows":rows,
        "claim_scope":"Frozen response-propagation analogue only; no paper benchmark, key-assigner, LongMemEval, or LoCoMo reproduction claim.",
    }

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--model-id",default="Qwen/Qwen2.5-0.5B-Instruct")
    p.add_argument("--max-new-tokens",type=int,default=16)
    a=p.parse_args()
    print(json.dumps(run(a.model_id,a.max_new_tokens),indent=2,ensure_ascii=False))
