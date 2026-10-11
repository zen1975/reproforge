"""Frozen Qwen2.5-0.5B workflow proposal + self-evaluation analogue for MASS."""
from __future__ import annotations
import argparse, json, re
import torch, transformers
from transformers import AutoModelForCausalLM, AutoTokenizer

EVAL_CASES = [
    {"id":"e1","incumbent":"One generalist reads all files and writes the report.","candidate":"A data agent extracts measurements, an analysis agent computes statistics, and the orchestrator integrates both outputs.","truth":"CANDIDATE"},
    {"id":"e2","incumbent":"A data agent extracts measurements, an analysis agent computes statistics, and the orchestrator integrates both outputs.","candidate":"One generalist reads all files and writes the report.","truth":"INCUMBENT"},
    {"id":"e3","incumbent":"Two agents independently solve the same subproblem and the orchestrator selects one without comparison.","candidate":"One agent computes results, a second checks assumptions and errors, and the orchestrator receives both the result and explicit critique.","truth":"CANDIDATE"},
    {"id":"e4","incumbent":"One agent computes results, a second checks assumptions and errors, and the orchestrator receives both the result and explicit critique.","candidate":"Two agents independently solve the same subproblem and the orchestrator selects one without comparison.","truth":"INCUMBENT"},
    {"id":"e5","incumbent":"Researcher returns raw logs only.","candidate":"Researcher returns raw logs plus a compact table of findings and uncertainty for the orchestrator.","truth":"CANDIDATE"},
    {"id":"e6","incumbent":"Researcher returns raw logs plus a compact table of findings and uncertainty for the orchestrator.","candidate":"Researcher returns raw logs only.","truth":"INCUMBENT"},
]

PROPOSAL_CASES = [
    {"id":"p1","task":"Analyze experiment results and write a concise report.","feedback":"The previous workflow lost important measurements between analysis and reporting."},
    {"id":"p2","task":"Review a code change for correctness and produce a decision.","feedback":"The previous workflow had no independent verification step."},
    {"id":"p3","task":"Compare two technical approaches using evidence.","feedback":"The previous workflow duplicated work and returned overlapping information."},
    {"id":"p4","task":"Investigate a failed data pipeline.","feedback":"The previous workflow mixed diagnosis, repair, and validation in one agent."},
]

def generate(model,tok,prompt,max_new_tokens):
    text=tok.apply_chat_template([{"role":"user","content":prompt}],tokenize=False,add_generation_prompt=True)
    inputs=tok(text,return_tensors="pt")
    with torch.no_grad():
        out=model.generate(**inputs,max_new_tokens=max_new_tokens,do_sample=False,pad_token_id=tok.eos_token_id)
    return tok.decode(out[0][inputs["input_ids"].shape[1]:],skip_special_tokens=True)

def parse_eval(text):
    m=re.findall(r"\b(CANDIDATE|INCUMBENT)\b",text.upper())
    return m[-1] if m else None

def parse_json_object(text):
    start=text.find("{"); end=text.rfind("}")
    if start<0 or end<=start: return None
    try: return json.loads(text[start:end+1])
    except Exception: return None

def valid_workflow(obj):
    if not isinstance(obj,dict): return False
    agents=obj.get("agents"); hop=obj.get("hop")
    if not isinstance(agents,list) or len(agents)<2 or not isinstance(hop,list): return False
    for a in agents:
        if not isinstance(a,dict): return False
        if not all(isinstance(a.get(k),str) and a.get(k).strip() for k in ("role","instruction","contract")): return False
    roles={a["role"] for a in agents}
    return bool(roles) and all(isinstance(x,str) and x in roles for x in hop)

def run(model_id,max_new_tokens):
    tok=AutoTokenizer.from_pretrained(model_id)
    model=AutoModelForCausalLM.from_pretrained(model_id,torch_dtype=torch.float32)
    model.eval()

    eval_rows=[]
    for c in EVAL_CASES:
        prompt=(
            "You are the in-loop evaluator for two candidate workflows. "
            "Choose which workflow is better for reliable information flow and task completion. "
            "Return only CANDIDATE or INCUMBENT.\n"
            f"Incumbent: {c['incumbent']}\nCandidate: {c['candidate']}\n"
        )
        raw=generate(model,tok,prompt,max_new_tokens)
        choice=parse_eval(raw)
        eval_rows.append({"id":c["id"],"truth":c["truth"],"choice":choice,"valid":choice in {"CANDIDATE","INCUMBENT"},"correct":choice==c["truth"],"raw":raw})

    proposal_rows=[]
    for c in PROPOSAL_CASES:
        prompt=(
            "Design a multi-agent workflow as strict JSON with keys agents and hop. "
            "agents must be a list of at least two objects with string keys role, instruction, contract. "
            "hop must list the role names in execution order. "
            "Prioritize changing information routing and output contracts rather than merely renaming roles. "
            "Return JSON only.\n"
            f"Task: {c['task']}\nFeedback: {c['feedback']}\n"
        )
        raw=generate(model,tok,prompt,96)
        obj=parse_json_object(raw)
        valid=valid_workflow(obj)
        contracts=[a.get("contract","") for a in obj.get("agents",[])] if isinstance(obj,dict) else []
        proposal_rows.append({"id":c["id"],"valid":valid,"has_nonempty_contracts":bool(contracts) and all(x.strip() for x in contracts),"raw":raw,"parsed":obj})

    valid_eval=sum(r["valid"] for r in eval_rows)/len(eval_rows)
    eval_acc=sum(r["correct"] for r in eval_rows)/len(eval_rows)
    valid_prop=sum(r["valid"] for r in proposal_rows)/len(proposal_rows)
    contract_rate=sum(r["has_nonempty_contracts"] for r in proposal_rows)/len(proposal_rows)

    return {
        "experiment_id":"mass-qwen0.5b-workflow-eval-analogue-v1",
        "model":model_id,
        "resolved_model_revision":getattr(model.config,"_commit_hash",None),
        "torch_version":torch.__version__,
        "transformers_version":transformers.__version__,
        "evaluator":{"cases":len(eval_rows),"valid_rate":valid_eval,"accuracy":eval_acc,"rows":eval_rows},
        "optimizer":{"cases":len(proposal_rows),"valid_workflow_rate":valid_prop,"nonempty_contract_rate":contract_rate,"rows":proposal_rows},
        "claim_scope":"Frozen small-model analogue only; no model update, recursive improvement, benchmark, or coordination-internalization claim."
    }

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--model-id",default="Qwen/Qwen2.5-0.5B-Instruct")
    p.add_argument("--max-new-tokens",type=int,default=8)
    a=p.parse_args()
    print(json.dumps(run(a.model_id,a.max_new_tokens),indent=2,ensure_ascii=False))
