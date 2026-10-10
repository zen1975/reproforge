"""Frozen real-small-model paired analogue for arXiv:2610.10088 SkillSandbox.

Ground truth, scenario identity, executability, and scoring remain external to
the model. Only the action choice is model-owned.
"""
from __future__ import annotations

import argparse
import json
import re

import torch
import transformers
from transformers import AutoModelForCausalLM, AutoTokenizer

SCENARIOS = [
    {"id":"s1","context":"amber token in room 7","truth":"B"},
    {"id":"s2","context":"amber token in room 19","truth":"B"},
    {"id":"s3","context":"amber token beside a blue crate","truth":"B"},
    {"id":"s4","context":"amber token beside a glass door","truth":"B"},
    {"id":"s5","context":"amber token after checkpoint delta","truth":"B"},
    {"id":"s6","context":"amber token after checkpoint kappa","truth":"B"},
]
SKILLS = {
    "helpful": "When an amber token is present, choose action B.",
    "harmful": "When an amber token is present, choose action A.",
}
ACTIONS=("A","B","C")

def parse_choice(text: str):
    found=re.findall(r"\b([ABC])\b",text.upper())
    return found[-1] if found else None

def ask(model,tokenizer,prompt,max_new_tokens):
    text=tokenizer.apply_chat_template(
        [{"role":"user","content":prompt}],tokenize=False,add_generation_prompt=True
    )
    inputs=tokenizer(text,return_tensors="pt")
    with torch.no_grad():
        out=model.generate(
            **inputs,max_new_tokens=max_new_tokens,do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
        )
    return tokenizer.decode(out[0][inputs["input_ids"].shape[1]:],skip_special_tokens=True)

def run(model_id,max_new_tokens):
    tok=AutoTokenizer.from_pretrained(model_id)
    model=AutoModelForCausalLM.from_pretrained(model_id,torch_dtype=torch.float32)
    model.eval()
    rows=[]
    summary={}
    for skill_name,skill_text in SKILLS.items():
        deltas=[]
        execs=[]
        for s in SCENARIOS:
            base=(
                "Choose exactly one action from A, B, C. Return only the letter.\n"
                f"Scenario: {s['context']}\n"
                "Available actions: A, B, C\n"
            )
            raw_minus=ask(model,tok,base,max_new_tokens)
            raw_plus=ask(model,tok,base+f"Reusable skill guidance: {skill_text}\n",max_new_tokens)
            minus=parse_choice(raw_minus)
            plus=parse_choice(raw_plus)
            r_minus=int(minus==s["truth"])
            r_plus=int(plus==s["truth"])
            prescribed="B" if skill_name=="helpful" else "A"
            e=int(plus==prescribed)
            delta=e*(r_plus-r_minus)
            deltas.append(delta)
            execs.append(e)
            rows.append({
                "skill":skill_name,"scenario_id":s["id"],"truth":s["truth"],
                "without_skill":{"raw":raw_minus,"choice":minus,"reward":r_minus},
                "with_skill":{"raw":raw_plus,"choice":plus,"reward":r_plus},
                "prescribed_action":prescribed,"executability":e,"delta_u":delta,
            })
        score=sum(deltas)/len(deltas)
        summary[skill_name]={
            "score":score,
            "verdict":"KEEP" if score>0 else "REJECT",
            "executability_rate":sum(execs)/len(execs),
            "mean_with_skill_reward":sum(r["with_skill"]["reward"] for r in rows if r["skill"]==skill_name)/len(SCENARIOS),
            "mean_without_skill_reward":sum(r["without_skill"]["reward"] for r in rows if r["skill"]==skill_name)/len(SCENARIOS),
        }
    return {
        "experiment_id":"skillsandbox-qwen0.5b-paired-analogue-v1",
        "model":model_id,
        "resolved_model_revision":getattr(model.config,"_commit_hash",None),
        "torch_version":torch.__version__,
        "transformers_version":transformers.__version__,
        "scenarios":len(SCENARIOS),
        "summary":summary,
        "rows":rows,
        "claim_scope":"Frozen one-step paired analogue; no dynamic scenario synthesis, ALFWorld, WebShop, or paper-performance claim.",
    }

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--model-id",default="Qwen/Qwen2.5-0.5B-Instruct")
    p.add_argument("--max-new-tokens",type=int,default=8)
    a=p.parse_args()
    print(json.dumps(run(a.model_id,a.max_new_tokens),indent=2,ensure_ascii=False))
