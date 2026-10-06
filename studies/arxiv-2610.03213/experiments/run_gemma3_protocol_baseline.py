"""Gemma 3 1B protocol baseline.

Requires prior acceptance of Google's Gemma license and HF_TOKEN access.
Fails closed if authentication or model access is unavailable.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

ROOT=Path(__file__).resolve().parents[3]
STUDY=ROOT/"studies"/"arxiv-2610.03213"
MODEL_ID="google/gemma-3-1b-it"
MAX_CASES=160


def _parse(text):
    m=re.search(r'\b(RELEVANT|IRRELEVANT)\b',text.upper())
    return None if not m else m.group(1)=="RELEVANT"


def _metrics(rows):
    valid=[r for r in rows if r["prediction"] is not None]
    tp=sum(r["prediction"] and r["label"]==1 for r in valid)
    tn=sum((not r["prediction"]) and r["label"]==0 for r in valid)
    fp=sum(r["prediction"] and r["label"]==0 for r in valid)
    fn=sum((not r["prediction"]) and r["label"]==1 for r in valid)
    n=len(valid)
    p=tp/(tp+fp) if tp+fp else 0.0
    rec=tp/(tp+fn) if tp+fn else 0.0
    f1=2*p*rec/(p+rec) if p+rec else 0.0
    return {"attempted":len(rows),"valid":n,"parse_failures":len(rows)-n,
            "accuracy":(tp+tn)/n if n else 0.0,"precision":p,"recall":rec,"f1":f1,
            "tp":tp,"tn":tn,"fp":fp,"fn":fn}


def run():
    token=os.environ.get("HF_TOKEN","").strip()
    if not token:
        raise RuntimeError("HF_TOKEN is required; Gemma reproduction fails closed")
    data=json.loads((STUDY/"experiments"/"protocol_equivalent_mcp_v1.json").read_text())
    test=[r for r in data["rows"] if r["pool"]=="test"][:MAX_CASES]
    tok=AutoTokenizer.from_pretrained(MODEL_ID,token=token)
    model=AutoModelForCausalLM.from_pretrained(
        MODEL_ID,token=token,torch_dtype=torch.float32,low_cpu_mem_usage=True
    )
    model.eval()
    rows=[]
    for row in test:
        messages=[
          {"role":"system","content":"You are a strict task-tool relevance classifier. Wrong actions on the same object are irrelevant. Answer exactly RELEVANT or IRRELEVANT."},
          {"role":"user","content":f"TASK: {row['task']}\nTOOL NAME: {row['tool_name']}\nTOOL DESCRIPTION: {row['tool_description']}"}
        ]
        prompt=tok.apply_chat_template(messages,tokenize=False,add_generation_prompt=True)
        inputs=tok(prompt,return_tensors="pt")
        with torch.no_grad():
            ids=model.generate(**inputs,max_new_tokens=6,do_sample=False)
        raw=tok.decode(ids[0][inputs["input_ids"].shape[1]:],skip_special_tokens=True).strip()
        rows.append({"group_id":row["group_id"],"label":row["label"],"prediction":_parse(raw),"raw":raw})
    metrics=_metrics(rows)
    return {"experiment_id":"gemma3-1b-protocol-base-v1","model_id":MODEL_ID,
            "metrics":metrics,"paper_operational_target":{"accuracy":0.95,"f1":0.95},
            "meets_target":metrics["accuracy"]>=0.95 and metrics["f1"]>=0.95,
            "rows":rows}


if __name__=="__main__":
    print(json.dumps(run(),indent=2,sort_keys=True))
