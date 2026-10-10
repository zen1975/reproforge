"""Frozen 0.5B proposer analogue for arXiv:2610.10088 SkillSandbox.

The model generates scenario text. Relevance, novelty, and format validity are
checked by deterministic external validators frozen before execution.
"""
from __future__ import annotations

import argparse
import json
import re

import torch
import transformers
from transformers import AutoModelForCausalLM, AutoTokenizer

CASES = [
    {"id":"p1","condition":"multipack total volume","source_detail":"brand alpha","required":["multipack","total volume"]},
    {"id":"p2","condition":"meeting reschedule confirmation","source_detail":"room cedar","required":["meeting","reschedule"]},
    {"id":"p3","condition":"inventory threshold alert","source_detail":"warehouse north","required":["inventory","threshold"]},
    {"id":"p4","condition":"route distance comparison","source_detail":"route amber","required":["route","distance"]},
    {"id":"p5","condition":"account balance before purchase","source_detail":"account delta","required":["account","balance"]},
    {"id":"p6","condition":"airport code lookup","source_detail":"city paris","required":["airport","code"]},
]

def normalize(s: str) -> str:
    return re.sub(r"\s+"," ",s.strip().lower())

def validate(text: str, case: dict) -> dict:
    t=normalize(text)
    relevant=all(tok in t for tok in case["required"])
    novel=normalize(case["source_detail"]) not in t
    format_valid=0 < len(t) <= 240 and "\n" not in text.strip()
    return {"relevant":relevant,"novel":novel,"format_valid":format_valid,
            "valid":relevant and novel and format_valid}

def run(model_id: str, max_new_tokens: int):
    tok=AutoTokenizer.from_pretrained(model_id)
    model=AutoModelForCausalLM.from_pretrained(model_id,torch_dtype=torch.float32)
    model.eval()
    rows=[]
    for case in CASES:
        prompt=(
            "Create ONE short novel verification scenario for a reusable agent skill.\n"
            "Preserve the applicability condition but change the source-specific detail.\n"
            "Return one sentence only. Do not explain.\n"
            f"Applicability condition: {case['condition']}\n"
            f"Source-specific detail that MUST NOT be reused: {case['source_detail']}\n"
        )
        text=tok.apply_chat_template(
            [{"role":"user","content":prompt}],tokenize=False,add_generation_prompt=True
        )
        inputs=tok(text,return_tensors="pt")
        with torch.no_grad():
            out=model.generate(
                **inputs,max_new_tokens=max_new_tokens,do_sample=False,
                pad_token_id=tok.eos_token_id,
            )
        decoded=tok.decode(out[0][inputs["input_ids"].shape[1]:],skip_special_tokens=True).strip()
        checks=validate(decoded,case)
        rows.append({"case_id":case["id"],"raw_output":decoded,**checks})
    n=len(rows)
    return {
        "experiment_id":"skillsandbox-qwen0.5b-proposer-analogue-v1",
        "model":model_id,
        "resolved_model_revision":getattr(model.config,"_commit_hash",None),
        "torch_version":torch.__version__,
        "transformers_version":transformers.__version__,
        "cases":n,
        "relevance_rate":sum(r["relevant"] for r in rows)/n,
        "novelty_rate":sum(r["novel"] for r in rows)/n,
        "format_valid_rate":sum(r["format_valid"] for r in rows)/n,
        "scenario_valid_rate":sum(r["valid"] for r in rows)/n,
        "rows":rows,
        "claim_scope":"Frozen proposer analogue only; no Builder environment execution, ALFWorld/WebShop, or paper-scale synthesis claim.",
    }

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--model-id",default="Qwen/Qwen2.5-0.5B-Instruct")
    p.add_argument("--max-new-tokens",type=int,default=48)
    a=p.parse_args()
    print(json.dumps(run(a.model_id,a.max_new_tokens),indent=2,ensure_ascii=False))
