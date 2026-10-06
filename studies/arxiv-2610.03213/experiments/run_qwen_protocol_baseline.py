"""Run an ungated 0.5B SLM base/instruction baseline on protocol-equivalent data."""

from __future__ import annotations

import json
import re
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

ROOT=Path(__file__).resolve().parents[3]
STUDY=ROOT/"studies"/"arxiv-2610.03213"
MODEL_ID="Qwen/Qwen2.5-0.5B-Instruct"
MODEL_REVISION="c89bee90d9f811437d9735454613c35b4a3c4dc8"
MAX_CASES=160


def _parse(text):
    m=re.search(r'\b(RELEVANT|IRRELEVANT)\b',text.upper())
    if not m:
        return None
    return m.group(1)=="RELEVANT"


def _metrics(rows):
    valid=[r for r in rows if r["prediction"] is not None]
    tp=sum(r["prediction"] and r["label"]==1 for r in valid)
    tn=sum((not r["prediction"]) and r["label"]==0 for r in valid)
    fp=sum(r["prediction"] and r["label"]==0 for r in valid)
    fn=sum((not r["prediction"]) and r["label"]==1 for r in valid)
    n=len(valid)
    precision=tp/(tp+fp) if tp+fp else 0.0
    recall=tp/(tp+fn) if tp+fn else 0.0
    f1=2*precision*recall/(precision+recall) if precision+recall else 0.0
    return {
      "attempted":len(rows),"valid":n,"parse_failures":len(rows)-n,
      "accuracy":(tp+tn)/n if n else 0.0,"precision":precision,"recall":recall,"f1":f1,
      "tp":tp,"tn":tn,"fp":fp,"fn":fn
    }


def run():
    data=json.loads((STUDY/"experiments"/"protocol_equivalent_mcp_v1.json").read_text())
    test=[r for r in data["rows"] if r["pool"]=="test"][:MAX_CASES]
    tok=AutoTokenizer.from_pretrained(MODEL_ID,revision=MODEL_REVISION)
    model=AutoModelForCausalLM.from_pretrained(
        MODEL_ID,revision=MODEL_REVISION,torch_dtype=torch.float32,low_cpu_mem_usage=True
    )
    model.eval()
    out=[]
    for row in test:
        prompt=(
          "You are a strict task-tool relevance classifier. "
          "Decide whether the candidate tool is required or logically relevant to completing the task. "
          "Wrong actions on the same object are IRRELEVANT. Output exactly RELEVANT or IRRELEVANT.\n"
          f"TASK: {row['task']}\n"
          f"TOOL NAME: {row['tool_name']}\n"
          f"TOOL DESCRIPTION: {row['tool_description']}\n"
          "ANSWER:"
        )
        inputs=tok(prompt,return_tensors="pt")
        with torch.no_grad():
            ids=model.generate(**inputs,max_new_tokens=6,do_sample=False)
        generated=tok.decode(ids[0][inputs["input_ids"].shape[1]:],skip_special_tokens=True).strip()
        out.append({
          "id":row["group_id"]+":"+row["tool_name"]+":"+row["set_type"],
          "label":row["label"],"prediction":_parse(generated),"raw":generated
        })
    metrics=_metrics(out)
    return {
      "experiment_id":"qwen2.5-0.5b-protocol-base-v1",
      "model_id":MODEL_ID,"model_revision":MODEL_REVISION,
      "max_cases":MAX_CASES,"metrics":metrics,
      "paper_operational_target":{"accuracy":0.95,"f1":0.95},
      "meets_target":metrics["accuracy"]>=0.95 and metrics["f1"]>=0.95,
      "rows":out,
      "notes":"Ungated Apache-2.0 0.5B instruction SLM used as a model-class proxy because Gemma 3 is gated. This is not a Gemma reproduction."
    }


if __name__=="__main__":
    print(json.dumps(run(),indent=2,sort_keys=True))
