"""Independent meta-skill bank contract for arXiv:2609.38143."""
from __future__ import annotations
from dataclasses import dataclass, asdict
import json, re
from collections import Counter

@dataclass(frozen=True)
class MetaSkill:
    skill_id:str
    when:str
    provide:str
    use:str
    evidence_refs:tuple[str,...]

def validate_skill(s:MetaSkill):
    fields=[s.when.strip(),s.provide.strip(),s.use.strip()]
    return all(fields) and len(" ".join(fields).split()) <= 192

class Bank:
    def __init__(self):
        self.skills={}
        self.frozen=False
        self._mutated_batches=set()
    def apply(self,batch_id,decision,skill,current_evidence):
        if self.frozen:
            raise ValueError("bank frozen")
        if decision=="KEEP":
            return
        if decision not in {"ADD","REVISE"}:
            raise ValueError("unknown decision")
        if batch_id in self._mutated_batches:
            raise ValueError("only one mutation per batch")
        if skill is None or not validate_skill(skill):
            raise ValueError("invalid skill")
        if not skill.evidence_refs or not set(skill.evidence_refs).issubset(set(current_evidence)):
            raise ValueError("mutation not grounded in current batch evidence")
        if decision=="ADD" and skill.skill_id in self.skills:
            raise ValueError("ADD requires new id")
        if decision=="REVISE" and skill.skill_id not in self.skills:
            raise ValueError("REVISE requires existing id")
        self.skills[skill.skill_id]=skill
        self._mutated_batches.add(batch_id)
    def freeze(self):
        self.frozen=True

TOKEN=re.compile(r"[a-z0-9]+")
def tokens(s): return TOKEN.findall(s.lower())
def retrieve(bank,query,k=2):
    q=Counter(tokens(query))
    scored=[]
    for sid,s in bank.skills.items():
        doc=Counter(tokens(s.when+" "+s.provide+" "+s.use))
        score=sum(min(q[t],doc[t]) for t in q)
        if score>0: scored.append((score,sid,s))
    scored.sort(key=lambda x:(-x[0],x[1]))
    return [x[2] for x in scored[:k]]

def run():
    b=Bank()
    s1=MetaSkill(
      "revalidate-after-edit",
      "artifact is modified after an earlier validation",
      "version tracking plus a fresh validation hook",
      "check the validation result for the current artifact version before submission; Target retains responsibility for correction",
      ("e1","e2"),
    )
    b.apply("batch1","ADD",s1,["e1","e2","e3"])
    add_ok="revalidate-after-edit" in b.skills

    second_mutation_blocked=False
    try:
        b.apply("batch1","ADD",MetaSkill("x","x","x","x",("e1",)),["e1"])
    except ValueError: second_mutation_blocked=True

    ungrounded_blocked=False
    try:
        b.apply("batch2","ADD",MetaSkill("y","when y","provide y","use y",("old",)),["e4"])
    except ValueError: ungrounded_blocked=True

    s1r=MetaSkill(
      "revalidate-after-edit",
      "artifact or dependent input changes after validation",
      "version tracking and dependency-aware revalidation",
      "verify the current version and affected dependencies before submission; Target retains responsibility for final correction",
      ("e4","e5"),
    )
    b.apply("batch2","REVISE",s1r,["e4","e5"])
    revise_ok=b.skills["revalidate-after-edit"].provide.startswith("version tracking")

    s2=MetaSkill(
      "persist-experiment-state",
      "multi-step scientific task requires coordinating repeated experiments",
      "persistent state for tested settings and observed outcomes",
      "consult prior experiment state before selecting the next experiment; Target remains responsible for scientific judgment",
      ("e6",),
    )
    b.apply("batch3","ADD",s2,["e6"])

    full_before=[asdict(x) for x in b.skills.values()]
    retrieved=retrieve(b,"artifact changed after validation; need current check",2)
    retrieval_ok=len(retrieved)<=2 and retrieved and retrieved[0].skill_id=="revalidate-after-edit"

    b.freeze()
    frozen_blocked=False
    try:
        b.apply("test1","ADD",MetaSkill("z","z","z","z",("t1",)),["t1"])
    except ValueError: frozen_blocked=True
    full_after=[asdict(x) for x in b.skills.values()]
    freeze_integrity=full_before==full_after

    checks={
      "valid_schema":validate_skill(s1) and validate_skill(s2),
      "evidence_grounded_add":add_ok,
      "second_mutation_same_batch_blocked":second_mutation_blocked,
      "ungrounded_update_blocked":ungrounded_blocked,
      "evidence_grounded_revision":revise_ok,
      "retrieval_top_k_and_relevant":retrieval_ok,
      "freeze_blocks_mutation":frozen_blocked,
      "freeze_preserves_bank":freeze_integrity,
      "full_bank_readable_after_freeze":len(b.skills)==2,
    }
    return {
      "experiment_id":"meta-skill-bank-mechanism-v1",
      "checks":checks,
      "all_pass":all(checks.values()),
      "bank_size":len(b.skills),
      "retrieved_ids":[x.skill_id for x in retrieved],
      "claim_scope":"Independent schema/update/freeze/selection semantics only; no Harness-Bench/NewtonBench or Builder-enactment performance claim."
    }

if __name__=="__main__":
    print(json.dumps(run(),indent=2,sort_keys=True))
