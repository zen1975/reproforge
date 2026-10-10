"""Frozen Qwen 0.5B meta-skill update analogue for arXiv:2609.38143.

The model only proposes KEEP/ADD/REVISE and a structured meta-skill.
External frozen labels and validators determine decision correctness and
whether cited evidence is actually from the current batch.
"""
from __future__ import annotations
import argparse, json, re
import torch, transformers
from transformers import AutoModelForCausalLM, AutoTokenizer

CASES=[
 {
  "id":"add-revalidate","bank":[],
  "evidence":[
   {"id":"e1","text":"Target validated report v1, then edited the report and submitted without revalidation; evaluator rejected stale validation."},
   {"id":"e2","text":"A second task failed after a post-validation edit changed a referenced file."}
  ],
  "expected":"ADD","expected_id":"revalidate-after-edit"
 },
 {
  "id":"keep-isolated","bank":[
   {"skill_id":"revalidate-after-edit","when":"artifact changes after validation","provide":"version tracking and revalidation","use":"check current validation before submission; Target remains responsible for correction"}
  ],
  "evidence":[{"id":"e3","text":"One target mistyped a filename once; retry succeeded and no recurring support need was observed."}],
  "expected":"KEEP","expected_id":null
 },
 {
  "id":"revise-dependency","bank":[
   {"skill_id":"revalidate-after-edit","when":"artifact changes after validation","provide":"version tracking and revalidation","use":"check current validation before submission; Target remains responsible for correction"}
  ],
  "evidence":[
   {"id":"e4","text":"Target changed a dependent input without touching the final artifact; prior validation remained marked valid but output was wrong."},
   {"id":"e5","text":"A dependency-aware recheck would have caught the stale result."}
  ],
  "expected":"REVISE","expected_id":"revalidate-after-edit"
 },
 {
  "id":"add-experiment-state","bank":[],
  "evidence":[
   {"id":"e6","text":"Target repeated the same failed scientific setting because prior experiment outcomes were not persisted."},
   {"id":"e7","text":"The next task repeated another already-tested setting and exhausted the interaction budget."}
  ],
  "expected":"ADD","expected_id":"persist-experiment-state"
 },
 {
  "id":"keep-success","bank":[
   {"skill_id":"persist-experiment-state","when":"multi-step experiments require remembering tested settings","provide":"persistent experiment-state memory","use":"consult prior outcomes before the next experiment; Target remains responsible for scientific judgment"}
  ],
  "evidence":[{"id":"e8","text":"Target completed the task successfully using the existing experiment-state support; no new recurring burden or correction was observed."}],
  "expected":"KEEP","expected_id":null
 }
]

def parse_json(text):
    m=re.search(r"\{.*\}",text,re.S)
    for c in [text.strip(),m.group(0) if m else ""]:
        if not c: continue
        try:
            x=json.loads(c)
            if isinstance(x,dict): return x
        except Exception: pass
    return None

def valid_proposal(obj,case):
    if not isinstance(obj,dict): return False,False
    d=obj.get("decision")
    if d=="KEEP":
        return True,True
    if d not in {"ADD","REVISE"}: return False,False
    skill=obj.get("skill")
    if not isinstance(skill,dict): return False,False
    req=("skill_id","when","provide","use","evidence_refs")
    schema=all(skill.get(k) for k in req)
    refs=skill.get("evidence_refs",[])
    allowed={e["id"] for e in case["evidence"]}
    grounded=isinstance(refs,list) and len(refs)>0 and set(refs).issubset(allowed)
    return bool(schema),bool(grounded)

def run(model_id,max_new_tokens):
    tok=AutoTokenizer.from_pretrained(model_id)
    model=AutoModelForCausalLM.from_pretrained(model_id,torch_dtype=torch.float32)
    model.eval()
    rows=[]
    for c in CASES:
        prompt=(
          "You are reviewing one development-task execution batch to update a Builder meta-skill bank.\n"
          "Choose exactly one decision: KEEP, ADD, or REVISE. Use KEEP when no reusable evidence-grounded change is justified.\n"
          "ADD/REVISE must produce one structured skill with fields skill_id, when, provide, use, evidence_refs. "
          "evidence_refs may contain ONLY IDs from the current batch. The use field must state what the Target should do while retaining responsibility for final judgment.\n"
          "For REVISE, use an existing skill_id. For ADD, create a short reusable skill_id.\n"
          "Return ONLY JSON.\n"
          "KEEP: {\"decision\":\"KEEP\",\"reason\":\"...\"}\n"
          "ADD/REVISE: {\"decision\":\"ADD\",\"skill\":{\"skill_id\":\"...\",\"when\":\"...\",\"provide\":\"...\",\"use\":\"...\",\"evidence_refs\":[\"e1\"]},\"reason\":\"...\"}\n"
          f"Current bank: {json.dumps(c['bank'],ensure_ascii=False)}\n"
          f"Current batch evidence: {json.dumps(c['evidence'],ensure_ascii=False)}\n"
        )
        txt=tok.apply_chat_template([{"role":"user","content":prompt}],tokenize=False,add_generation_prompt=True)
        inp=tok(txt,return_tensors="pt")
        with torch.no_grad():
            out=model.generate(**inp,max_new_tokens=max_new_tokens,do_sample=False,pad_token_id=tok.eos_token_id)
        raw=tok.decode(out[0][inp["input_ids"].shape[1]:],skip_special_tokens=True).strip()
        obj=parse_json(raw)
        schema,grounded=valid_proposal(obj,c)
        decision=obj.get("decision") if isinstance(obj,dict) else None
        sid=(obj.get("skill") or {}).get("skill_id") if isinstance(obj,dict) and isinstance(obj.get("skill"),dict) else None
        decision_ok=decision==c["expected"]
        id_ok=(c["expected_id"] is None or sid==c["expected_id"])
        rows.append({
          "case_id":c["id"],"raw_output":raw,"parsed":obj,
          "schema_valid":schema,"evidence_grounded":grounded,
          "expected_decision":c["expected"],"decision_correct":decision_ok,
          "expected_skill_id":c["expected_id"],"skill_id_correct":id_ok
        })
    n=len(rows)
    mutated=[r for r in rows if r["expected_decision"] in {"ADD","REVISE"}]
    return {
      "experiment_id":"meta-skill-qwen0.5b-update-analogue-v1",
      "model":model_id,
      "resolved_model_revision":getattr(model.config,"_commit_hash",None),
      "torch_version":torch.__version__,
      "transformers_version":transformers.__version__,
      "cases":n,
      "schema_valid_rate":sum(r["schema_valid"] for r in rows)/n,
      "decision_accuracy":sum(r["decision_correct"] for r in rows)/n,
      "grounded_rate_on_expected_mutations":sum(r["evidence_grounded"] for r in mutated)/len(mutated),
      "skill_id_accuracy_on_expected_mutations":sum(r["skill_id_correct"] for r in mutated)/len(mutated),
      "rows":rows,
      "claim_scope":"Frozen 0.5B update-proposal analogue only; no Builder harness construction or benchmark-performance claim."
    }

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--model-id",default="Qwen/Qwen2.5-0.5B-Instruct")
    p.add_argument("--max-new-tokens",type=int,default=192)
    a=p.parse_args()
    print(json.dumps(run(a.model_id,a.max_new_tokens),indent=2,ensure_ascii=False))
