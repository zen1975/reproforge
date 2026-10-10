"""Frozen 0.5B key-assignment analogue for arXiv:2610.10265.

The model classifies whether two observations update the same mutable slot.
Labels are external and frozen before execution.
"""
from __future__ import annotations

import argparse
import json
import re

import torch
import transformers
from transformers import AutoModelForCausalLM, AutoTokenizer

PAIRS = [
    ("same1","Alex's standup is at 09:30.","The standup with Alex moved to 10:45.",1),
    ("same2","Maya's weekly sync is in Room 3.","Maya's weekly sync has moved to Room 7.",1),
    ("same3","Sam prefers ramen for lunch.","Sam now prefers soba for lunch.",1),
    ("same4","Project Nova deadline is Tuesday.","Nova's deadline changed to Thursday.",1),
    ("same5","Jordan's delivery day is Monday.","Jordan's delivery is now scheduled for Friday.",1),
    ("same6","Orion uses vendor Alpha.","The vendor for Orion has changed to Beta.",1),
    ("diff1","Alex's standup is at 10:45.","Alex's project sync is at 15:00.",0),
    ("diff2","Maya's weekly sync is in Room 7.","Maya's desk is in Room 12.",0),
    ("diff3","Sam prefers soba for lunch.","Sam's coffee order is espresso.",0),
    ("diff4","Project Nova deadline is Thursday.","Project Nova owner is Priya.",0),
    ("diff5","Jordan's delivery day is Friday.","Jordan's pickup location is Dock 2.",0),
    ("diff6","Orion uses vendor Beta.","Orion's budget is 5000.",0),
]

def parse(text:str):
    m=re.findall(r"\b(MERGE|SPLIT)\b",text.upper())
    return m[-1] if m else None

def run(model_id,max_new_tokens):
    tok=AutoTokenizer.from_pretrained(model_id)
    model=AutoModelForCausalLM.from_pretrained(model_id,torch_dtype=torch.float32)
    model.eval()
    rows=[]
    for pid,a,b,label in PAIRS:
        prompt=(
            "Decide whether the second observation updates the SAME mutable memory slot as the first.\n"
            "MERGE = same entity/property slot, so the second supersedes the first.\n"
            "SPLIT = different property/slot, so both should remain independently active.\n"
            "Return only MERGE or SPLIT.\n"
            f"Observation 1: {a}\n"
            f"Observation 2: {b}\n"
        )
        text=tok.apply_chat_template(
            [{"role":"user","content":prompt}],tokenize=False,add_generation_prompt=True
        )
        inputs=tok(text,return_tensors="pt")
        with torch.no_grad():
            out=model.generate(**inputs,max_new_tokens=max_new_tokens,do_sample=False,
                               pad_token_id=tok.eos_token_id)
        raw=tok.decode(out[0][inputs["input_ids"].shape[1]:],skip_special_tokens=True).strip()
        choice=parse(raw)
        pred=1 if choice=="MERGE" else 0 if choice=="SPLIT" else None
        rows.append({"pair_id":pid,"label_merge":label,"raw_output":raw,"choice":choice,
                     "valid":pred is not None,"correct":pred==label if pred is not None else False})
    same=[r for r in rows if r["label_merge"]==1]
    diff=[r for r in rows if r["label_merge"]==0]
    merge_recall=sum(r["choice"]=="MERGE" for r in same)/len(same)
    false_merge=sum(r["choice"]=="MERGE" for r in diff)/len(diff)
    valid=sum(r["valid"] for r in rows)/len(rows)
    acc=sum(r["correct"] for r in rows)/len(rows)
    return {
        "experiment_id":"memory-qwen0.5b-key-assignment-v1",
        "model":model_id,
        "resolved_model_revision":getattr(model.config,"_commit_hash",None),
        "torch_version":torch.__version__,
        "transformers_version":transformers.__version__,
        "pairs":len(rows),
        "valid_rate":valid,
        "merge_recall":merge_recall,
        "false_merge_rate":false_merge,
        "accuracy":acc,
        "rows":rows,
        "claim_scope":"Frozen synthetic key-assignment analogue only; no paper key-assigner, LongMemEval, or clean-retrieval-rate reproduction claim.",
    }

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--model-id",default="Qwen/Qwen2.5-0.5B-Instruct")
    p.add_argument("--max-new-tokens",type=int,default=8)
    a=p.parse_args()
    print(json.dumps(run(a.model_id,a.max_new_tokens),indent=2,ensure_ascii=False))
