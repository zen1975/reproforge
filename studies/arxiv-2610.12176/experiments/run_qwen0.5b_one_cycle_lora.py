"""Tiny one-cycle MASS analogue: task-solving-only LoRA, then cross-role re-evaluation."""
from __future__ import annotations
import argparse, json, re, random
import torch
import torch.nn.functional as F
import transformers
from peft import LoraConfig, get_peft_model
from transformers import AutoModelForCausalLM, AutoTokenizer

SEED=261012176

TRAIN_TRACES=[
    {
      "user":"Task: analyze experiment results and produce a reliable short report.",
      "assistant":"I will coordinate two bounded roles. Analyst: compute the measurements and return a table with uncertainty. Verifier: inspect the table for inconsistencies and return explicit issues. I will integrate only the checked measurements into the final report."
    },
    {
      "user":"Task: review a code change and decide whether it is safe.",
      "assistant":"I will delegate implementation review and independent verification separately. Reviewer: identify logic risks and return file, line, risk, evidence. Tester: run focused checks and return failing cases and observed output. I will reconcile both reports before the decision."
    },
    {
      "user":"Task: compare two technical approaches using evidence.",
      "assistant":"I will separate evidence collection from comparison. Researcher A returns measured strengths, limits, and sources for approach A. Researcher B does the same for B. A verifier checks that criteria match across both reports. I will synthesize the comparison from those contracts."
    },
    {
      "user":"Task: diagnose and repair a failed data pipeline.",
      "assistant":"I will use staged coordination. Diagnoser returns the failing stage, evidence, and likely cause. Repairer receives that diagnosis and returns the minimal patch plus changed files. Validator receives both and returns pass or fail with concrete checks. I will stop if validation fails."
    }
]

EVAL_CASES=[
    {"id":"e1","incumbent":"One generalist reads all files and writes the report.","candidate":"A data agent extracts measurements, an analysis agent computes statistics, and the orchestrator integrates both outputs.","truth":"CANDIDATE"},
    {"id":"e2","incumbent":"A data agent extracts measurements, an analysis agent computes statistics, and the orchestrator integrates both outputs.","candidate":"One generalist reads all files and writes the report.","truth":"INCUMBENT"},
    {"id":"e3","incumbent":"Two agents independently solve the same subproblem and the orchestrator selects one without comparison.","candidate":"One agent computes results, a second checks assumptions and errors, and the orchestrator receives both the result and explicit critique.","truth":"CANDIDATE"},
    {"id":"e4","incumbent":"One agent computes results, a second checks assumptions and errors, and the orchestrator receives both the result and explicit critique.","candidate":"Two agents independently solve the same subproblem and the orchestrator selects one without comparison.","truth":"INCUMBENT"},
    {"id":"e5","incumbent":"Researcher returns raw logs only.","candidate":"Researcher returns raw logs plus a compact table of findings and uncertainty for the orchestrator.","truth":"CANDIDATE"},
    {"id":"e6","incumbent":"Researcher returns raw logs plus a compact table of findings and uncertainty for the orchestrator.","candidate":"Researcher returns raw logs only.","truth":"INCUMBENT"},
]

PROPOSAL_CASES=[
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
    s=text.find("{"); e=text.rfind("}")
    if s<0 or e<=s: return None
    try: return json.loads(text[s:e+1])
    except Exception: return None

def valid_workflow(obj):
    if not isinstance(obj,dict): return False
    agents=obj.get("agents"); hop=obj.get("hop")
    if not isinstance(agents,list) or len(agents)<2 or not isinstance(hop,list): return False
    for a in agents:
        if not isinstance(a,dict): return False
        if not all(isinstance(a.get(k),str) and a.get(k).strip() for k in ("role","instruction","contract")): return False
    roles={a["role"] for a in agents}
    return all(isinstance(x,str) and x in roles for x in hop)

def evaluate_roles(model,tok):
    eval_rows=[]
    for c in EVAL_CASES:
        prompt=("You are the in-loop evaluator for two candidate workflows. Choose which workflow is better for reliable information flow and task completion. Return only CANDIDATE or INCUMBENT.\n"
                f"Incumbent: {c['incumbent']}\nCandidate: {c['candidate']}\n")
        raw=generate(model,tok,prompt,8)
        ch=parse_eval(raw)
        eval_rows.append({"id":c["id"],"truth":c["truth"],"choice":ch,"valid":ch in {"CANDIDATE","INCUMBENT"},"correct":ch==c["truth"]})
    prop_rows=[]
    for c in PROPOSAL_CASES:
        prompt=("Design a multi-agent workflow as strict JSON with keys agents and hop. agents must be a list of at least two objects with string keys role, instruction, contract. hop must list the role names in execution order. Prioritize information routing and output contracts. Return JSON only.\n"
                f"Task: {c['task']}\nFeedback: {c['feedback']}\n")
        raw=generate(model,tok,prompt,96)
        obj=parse_json_object(raw)
        prop_rows.append({"id":c["id"],"valid":valid_workflow(obj)})
    return {
      "evaluator":{"valid_rate":sum(r["valid"] for r in eval_rows)/len(eval_rows),"accuracy":sum(r["correct"] for r in eval_rows)/len(eval_rows),"rows":eval_rows},
      "optimizer":{"valid_workflow_rate":sum(r["valid"] for r in prop_rows)/len(prop_rows),"rows":prop_rows}
    }

def train_example(model,tok,row):
    prompt=tok.apply_chat_template([{"role":"user","content":row["user"]}],tokenize=False,add_generation_prompt=True)
    target=row["assistant"]+tok.eos_token
    p=tok(prompt,add_special_tokens=False)["input_ids"]
    t=tok(target,add_special_tokens=False)["input_ids"]
    ids=torch.tensor([p+t],dtype=torch.long)
    labels=torch.tensor([[-100]*len(p)+t],dtype=torch.long)
    attn=torch.ones_like(ids)
    return model(input_ids=ids,attention_mask=attn,labels=labels).loss

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--model-id",default="Qwen/Qwen2.5-0.5B-Instruct")
    ap.add_argument("--steps",type=int,default=4)
    ap.add_argument("--lr",type=float,default=2e-5)
    args=ap.parse_args()

    random.seed(SEED); torch.manual_seed(SEED)
    tok=AutoTokenizer.from_pretrained(args.model_id)
    if tok.pad_token_id is None: tok.pad_token=tok.eos_token
    base=AutoModelForCausalLM.from_pretrained(args.model_id,torch_dtype=torch.float32)
    model=get_peft_model(base,LoraConfig(r=4,lora_alpha=8,target_modules=["q_proj","v_proj"],task_type="CAUSAL_LM"))
    params=[p for p in model.parameters() if p.requires_grad]
    opt=torch.optim.AdamW(params,lr=args.lr)
    model.eval()
    before=evaluate_roles(model,tok)
    model.train()
    history=[]
    for i in range(args.steps):
        row=TRAIN_TRACES[i%len(TRAIN_TRACES)]
        opt.zero_grad(set_to_none=True)
        loss=train_example(model,tok,row)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(params,1.0)
        opt.step()
        history.append(float(loss.detach().item()))
    model.eval()
    after=evaluate_roles(model,tok)
    print(json.dumps({
      "experiment_id":"mass-qwen0.5b-one-cycle-lora-v1",
      "model":args.model_id,
      "resolved_model_revision":getattr(model.base_model.config,"_commit_hash",None),
      "torch_version":torch.__version__,
      "transformers_version":transformers.__version__,
      "training":{"source":"coordination-rich task-solving traces only","examples":len(TRAIN_TRACES),"steps":args.steps,"learning_rate":args.lr,"losses":history},
      "before":before,
      "after":after,
      "delta":{"evaluator_accuracy":after["evaluator"]["accuracy"]-before["evaluator"]["accuracy"],"optimizer_valid_workflow_rate":after["optimizer"]["valid_workflow_rate"]-before["optimizer"]["valid_workflow_rate"]},
      "claim_scope":"Tiny synthetic one-cycle LoRA analogue. It tests cross-role transfer after task-solving-only supervision but does not demonstrate paper-scale recursive self-improvement."
    },indent=2,ensure_ascii=False))

if __name__=="__main__":
    main()
