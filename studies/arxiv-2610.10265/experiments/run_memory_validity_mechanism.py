"""Independent memory-state mechanism verification for arXiv:2610.10265."""
from __future__ import annotations
from dataclasses import dataclass
import json

INF=10**9

@dataclass
class Fact:
    text:str
    entity:str
    slot:str
    value:str
    key:str|None
    active_from:int
    active_to:int=INF

class Store:
    def __init__(self):
        self.facts=[]
    def commit(self,f:Fact):
        if f.key is not None:
            for old in self.facts:
                if old.key==f.key and old.active_to==INF:
                    old.active_to=f.active_from
        self.facts.append(f)
    def active(self,t):
        return [f for f in self.facts if f.active_from<=t<f.active_to]

def eval_block(block,target_entity,target_slot,current_value,deadline_ms,latency_ms):
    related=[f for f in block if f.slot==target_slot]
    intended=[f for f in related if f.entity==target_entity]
    current=any(f.value==current_value for f in intended)
    stale=any(f.value!=current_value for f in intended)
    wrong=any(f.entity!=target_entity for f in related)
    answerable=current_value is not None
    if answerable:
        clean=int(current and not stale and not wrong)
    else:
        clean=int(len(related)==0)
    abstain=int(len(block)==0)
    clean_by_deadline=clean*int(latency_ms<=deadline_ms)
    return {
        "current":int(current),"stale":int(stale),"wrong_person":int(wrong),
        "clean":clean,"abstain":abstain,"clean_by_deadline":clean_by_deadline,
    }

def run():
    # Correct keyed supersession.
    s=Store()
    s.commit(Fact("Alex standup 09:30","alex-1","standup","09:30","alex-1:standup",1))
    s.commit(Fact("Alex standup 10:45","alex-1","standup","10:45","alex-1:standup",2))
    active=s.active(3)
    correct_key={
        "active_values":[f.value for f in active],
        "history_values":[f.value for f in s.facts],
        "one_active_per_key":sum(f.key=="alex-1:standup" for f in active)==1,
    }

    # Missed merge: revision gets a different key, leaving stale+current active.
    missed=Store()
    missed.commit(Fact("Alex standup 09:30","alex-1","standup","09:30","alex-1:standup:v1",1))
    missed.commit(Fact("Alex standup 10:45","alex-1","standup","10:45","alex-1:standup:v2",2))
    missed_eval=eval_block(missed.active(3),"alex-1","standup","10:45",10,1)

    # False merge: unrelated slot shares key and closes the current standup.
    false=Store()
    false.commit(Fact("Alex standup 10:45","alex-1","standup","10:45","alex-1:shared",1))
    false.commit(Fact("Alex sync Friday","alex-1","sync","Friday","alex-1:shared",2))
    false_eval=eval_block(false.active(3),"alex-1","standup","10:45",10,1)

    # Same surface name, different identity.
    identity=[
        Fact("Alex standup 10:45","alex-1","standup","10:45","a",1),
        Fact("Alex standup 08:00","alex-2","standup","08:00","b",1),
    ]
    id_unfiltered=eval_block(identity,"alex-1","standup","10:45",10,1)
    id_filtered=eval_block([f for f in identity if f.entity=="alex-1"],"alex-1","standup","10:45",10,1)

    # Unanswerable query: correct behavior is empty block.
    no_answer_good=eval_block([],"alex-1","lunch",None,10,1)
    no_answer_bad=eval_block(
        [Fact("Alex standup 10:45","alex-1","lunch","12:00","x",1)],
        "alex-1","lunch",None,10,1
    )

    # Same clean block, but missed deadline.
    deadline_ok=eval_block([Fact("Alex standup 10:45","alex-1","standup","10:45","a",1)],
                           "alex-1","standup","10:45",10,4)
    deadline_late=eval_block([Fact("Alex standup 10:45","alex-1","standup","10:45","a",1)],
                             "alex-1","standup","10:45",10,12)

    checks={
        "keyed_one_active":correct_key["one_active_per_key"],
        "history_retained":correct_key["history_values"]==["09:30","10:45"],
        "missed_merge_stale_exposure":missed_eval["current"]==1 and missed_eval["stale"]==1,
        "false_merge_loses_current":false_eval["current"]==0,
        "identity_filter_removes_wrong_person":id_unfiltered["wrong_person"]==1 and id_filtered["wrong_person"]==0,
        "unanswerable_empty_is_clean":no_answer_good["clean"]==1 and no_answer_good["abstain"]==1,
        "unanswerable_injected_fact_is_not_clean":no_answer_bad["clean"]==0,
        "deadline_separate_from_prompt_clean":deadline_ok["clean"]==1 and deadline_ok["clean_by_deadline"]==1 and deadline_late["clean"]==1 and deadline_late["clean_by_deadline"]==0,
    }
    return {
        "experiment_id":"memory-validity-mechanism-v1",
        "correct_key":correct_key,
        "missed_merge":missed_eval,
        "false_merge":false_eval,
        "identity_unfiltered":id_unfiltered,
        "identity_filtered":id_filtered,
        "unanswerable_empty":no_answer_good,
        "unanswerable_bad":no_answer_bad,
        "deadline_ok":deadline_ok,
        "deadline_late":deadline_late,
        "checks":checks,
        "all_pass":all(checks.values()),
        "claim_scope":"Independent memory-state and prompt-level metric semantics only; no benchmark-rate or response-model reproduction claim.",
    }

if __name__=="__main__":
    print(json.dumps(run(),indent=2,sort_keys=True))
