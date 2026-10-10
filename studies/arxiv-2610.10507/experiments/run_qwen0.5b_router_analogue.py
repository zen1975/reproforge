"""Frozen 0.5B RouterLM analogue for arXiv:2610.10507 RECAST.

The model only selects/formulates one action. Expected routing labels, evidence
sufficiency, primitive availability, and execution truth are external/frozen.
"""
from __future__ import annotations
import argparse, json, re
import torch, transformers
from transformers import AutoModelForCausalLM, AutoTokenizer

CASES=[
 {"id":"lex","task":"Find the document containing exact identifier ZX-481.","evidence":"No evidence yet.","expected_action":"CALL_PRIMITIVE","expected_primitive":"lexical"},
 {"id":"sem","task":"Find passages discussing employee burnout even if they use different wording.","evidence":"No evidence yet.","expected_action":"CALL_PRIMITIVE","expected_primitive":"semantic"},
 {"id":"rel","task":"From the records table, find 2026 orders above 500 and group by region.","evidence":"No evidence yet.","expected_action":"CALL_PRIMITIVE","expected_primitive":"relational"},
 {"id":"syn","task":"Using monthly revenue and income records, compute the largest 3-month operating-margin increase.","evidence":"Raw monthly operands are available but the 3-month margin-change result has not been computed.","expected_action":"SYNTHESIZE","expected_primitive":None},
 {"id":"accept","task":"Report the largest 3-month operating-margin increase.","evidence":"Derived evidence: period=m1-m3, increase=8.0 percentage points, sources=r1,r2,r3.","expected_action":"ACCEPT_CONTEXT","expected_primitive":None},
 {"id":"no-premature","task":"Report the largest 3-month operating-margin increase.","evidence":"Only raw monthly revenue and income operands are available; no derived margin-change result exists.","expected_action":"SYNTHESIZE","expected_primitive":None},
 {"id":"failed","task":"Find exact contract clause K-19.","evidence":"Previous lexical call failed with no match; required clause evidence is still absent.","expected_action":"CALL_PRIMITIVE","expected_primitive":"lexical"},
 {"id":"irregular","task":"Parse irregular nested event logs and compute the longest dependency chain.","evidence":"Raw log records exist; no primitive directly computes nested dependency chains.","expected_action":"SYNTHESIZE","expected_primitive":None},
]

def parse_json(text):
    candidates=[text.strip()]
    m=re.search(r"\{.*\}",text,re.S)
    if m: candidates.append(m.group(0))
    for c in candidates:
        try:
            x=json.loads(c)
            if isinstance(x,dict): return x
        except Exception: pass
    return None

def contract(x):
    if not isinstance(x,dict): return False
    a=x.get("action")
    if a=="CALL_PRIMITIVE":
        return x.get("primitive") in {"lexical","semantic","relational"} and bool(x.get("evidence_goal")) and isinstance(x.get("arguments"),dict)
    if a=="SYNTHESIZE":
        return x.get("level")=="code" and bool(x.get("evidence_goal")) and bool(x.get("required_output"))
    if a=="ACCEPT_CONTEXT":
        return bool(x.get("reason"))
    return False

def run(model_id,max_new_tokens):
    tok=AutoTokenizer.from_pretrained(model_id)
    model=AutoModelForCausalLM.from_pretrained(model_id,torch_dtype=torch.float32)
    model.eval()
    rows=[]
    for c in CASES:
        prompt=(
          "You are an evidence router, not the answer model. Select exactly one next action and return ONLY one JSON object.\n"
          "Actions:\n"
          "CALL_PRIMITIVE: {\"action\":\"CALL_PRIMITIVE\",\"primitive\":\"lexical|semantic|relational\",\"evidence_goal\":\"...\",\"arguments\":{},\"reason\":\"...\"}\n"
          "SYNTHESIZE: {\"action\":\"SYNTHESIZE\",\"level\":\"code\",\"evidence_goal\":\"...\",\"required_output\":\"...\",\"reason\":\"...\"}\n"
          "ACCEPT_CONTEXT: {\"action\":\"ACCEPT_CONTEXT\",\"reason\":\"...\"}\n"
          "Use ACCEPT_CONTEXT only when the evidence already contains the final evidence required by the task. "
          "If the task requires a computed result and only operands exist, do not accept; request computation.\n"
          "Primitive guidance: lexical=exact token/identifier; semantic=concept/paraphrase; relational=structured table filtering/grouping. "
          "Use SYNTHESIZE for deterministic computation/parsing not naturally provided by one primitive.\n"
          f"Task: {c['task']}\nCurrent evidence/history: {c['evidence']}\n"
        )
        txt=tok.apply_chat_template([{"role":"user","content":prompt}],tokenize=False,add_generation_prompt=True)
        inp=tok(txt,return_tensors="pt")
        with torch.no_grad():
            out=model.generate(**inp,max_new_tokens=max_new_tokens,do_sample=False,pad_token_id=tok.eos_token_id)
        raw=tok.decode(out[0][inp["input_ids"].shape[1]:],skip_special_tokens=True).strip()
        obj=parse_json(raw)
        valid=contract(obj)
        action=obj.get("action") if isinstance(obj,dict) else None
        primitive=obj.get("primitive") if isinstance(obj,dict) else None
        action_correct=action==c["expected_action"]
        primitive_correct=(c["expected_primitive"] is None or primitive==c["expected_primitive"])
        rows.append({"case_id":c["id"],"raw_output":raw,"parsed":obj,"valid_contract":valid,
                     "expected_action":c["expected_action"],"action_correct":action_correct,
                     "expected_primitive":c["expected_primitive"],"primitive_correct":primitive_correct})
    n=len(rows)
    premature=[r for r in rows if r["case_id"]=="no-premature"]
    return {
      "experiment_id":"recast-qwen0.5b-router-analogue-v1",
      "model":model_id,
      "resolved_model_revision":getattr(model.config,"_commit_hash",None),
      "torch_version":torch.__version__,
      "transformers_version":transformers.__version__,
      "cases":n,
      "valid_contract_rate":sum(r["valid_contract"] for r in rows)/n,
      "action_accuracy":sum(r["action_correct"] for r in rows)/n,
      "primitive_accuracy_on_primitive_cases":sum(r["primitive_correct"] for r in rows if r["expected_primitive"] is not None)/sum(1 for r in rows if r["expected_primitive"] is not None),
      "premature_accept_rate":sum(r["parsed"] is not None and r["parsed"].get("action")=="ACCEPT_CONTEXT" for r in premature)/len(premature),
      "rows":rows,
      "claim_scope":"Frozen 0.5B routing analogue only; no SFT/GRPO, compiler quality, AnswerLM, or paper benchmark claim."
    }

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--model-id",default="Qwen/Qwen2.5-0.5B-Instruct")
    p.add_argument("--max-new-tokens",type=int,default=96)
    a=p.parse_args()
    print(json.dumps(run(a.model_id,a.max_new_tokens),indent=2,ensure_ascii=False))
