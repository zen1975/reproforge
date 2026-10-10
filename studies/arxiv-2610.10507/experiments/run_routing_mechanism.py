"""Independent RECAST routing mechanism verification for arXiv:2610.10507."""
from __future__ import annotations
from dataclasses import dataclass, field
import json

ACTIONS={"CALL_PRIMITIVE","SYNTHESIZE","ACCEPT_CONTEXT"}
PRIMITIVES={"lexical","semantic","relational"}

@dataclass
class State:
    evidence:list[dict]=field(default_factory=list)
    history:list[dict]=field(default_factory=list)

def validate_action(a):
    if a.get("action") not in ACTIONS:
        return False,"unknown action"
    if a["action"]=="CALL_PRIMITIVE":
        if not a.get("evidence_goal") or a.get("primitive") not in PRIMITIVES:
            return False,"invalid primitive action"
        if not isinstance(a.get("arguments"),dict):
            return False,"missing arguments"
    elif a["action"]=="SYNTHESIZE":
        if a.get("level")!="code" or not a.get("evidence_goal") or not a.get("required_output"):
            return False,"incomplete synthesis specification"
        for token in a.get("required_constraints",[]):
            if token.lower() not in (a["evidence_goal"]+" "+a["required_output"]).lower():
                return False,f"constraint omitted: {token}"
    elif a["action"]=="ACCEPT_CONTEXT":
        if not a.get("reason"):
            return False,"accept requires reason"
    return True,"ok"

def transition(state,action,outcome):
    valid,msg=validate_action(action)
    if not valid:
        raise ValueError(msg)
    state.history.append({"action":action,"outcome":outcome})
    if action["action"] in {"CALL_PRIMITIVE","SYNTHESIZE"} and outcome.get("success"):
        for item in outcome.get("evidence",[]):
            if not item.get("source_ids"):
                raise ValueError("evidence missing source_ids")
            key=json.dumps(item,sort_keys=True)
            if all(json.dumps(x,sort_keys=True)!=key for x in state.evidence):
                state.evidence.append(item)
    return state

def sufficient(state,required_kind):
    return any(e.get("kind")==required_kind for e in state.evidence)

def can_accept(state,required_kind):
    return sufficient(state,required_kind)

def run():
    # Computed-answer route: operands -> derived computation -> accept.
    s=State()
    retrieve={
        "action":"CALL_PRIMITIVE","evidence_goal":"retrieve monthly revenue and operating income",
        "primitive":"relational","arguments":{"query":"SELECT month,revenue,income FROM records"},
        "reason":"exact structured operands"
    }
    transition(s,retrieve,{"success":True,"count":3,"evidence":[
        {"kind":"operands","value":[[1,100,10],[2,100,12],[3,100,18]],"source_ids":["r1","r2","r3"]}
    ]})
    premature_accept_blocked=not can_accept(s,"derived_margin_change")

    synth={
        "action":"SYNTHESIZE","level":"code",
        "evidence_goal":"compute 3-month operating margin change and identify largest increase",
        "required_output":"return period, margin increase, and source IDs in chronological order",
        "required_constraints":["3-month","margin","source IDs","chronological"],
        "reason":"requires sliding-window computation"
    }
    transition(s,synth,{"success":True,"evidence":[
        {"kind":"derived_margin_change","value":{"period":"m1-m3","increase":8.0},"source_ids":["r1","r2","r3"]}
    ]})
    accept_after_compute=can_accept(s,"derived_margin_change")

    accept={"action":"ACCEPT_CONTEXT","reason":"derived margin evidence is present"}
    ok_accept,_=validate_action(accept)

    # Failed operations are recorded but cannot silently expand evidence.
    before=len(s.evidence)
    failed={
        "action":"CALL_PRIMITIVE","evidence_goal":"find missing record","primitive":"lexical",
        "arguments":{"query":"missing","top_k":3},"reason":"exact token"
    }
    transition(s,failed,{"success":False,"error":"no match","count":0,"evidence":[]})
    failed_no_evidence=len(s.evidence)==before and s.history[-1]["outcome"]["success"] is False

    # Deduplication.
    duplicate={"kind":"derived_margin_change","value":{"period":"m1-m3","increase":8.0},"source_ids":["r1","r2","r3"]}
    transition(s,synth,{"success":True,"evidence":[duplicate]})
    deduplicated=len([e for e in s.evidence if e["kind"]=="derived_margin_change"])==1

    # Negative contract fixtures.
    malformed_ok,_=validate_action({"action":"CALL_PRIMITIVE","primitive":"relational","arguments":{}})
    incomplete_synth_ok,_=validate_action({
        "action":"SYNTHESIZE","level":"code","evidence_goal":"compute result",
        "required_output":"return result","required_constraints":["units"],"reason":"custom"
    })
    mixed_ok,_=validate_action({"action":"SEARCH","reason":"not in action space"})

    # Provenance must be fail-closed.
    provenance_rejected=False
    try:
        transition(State(),retrieve,{"success":True,"evidence":[{"kind":"operands","value":[1,2,3]}]})
    except ValueError:
        provenance_rejected=True

    checks={
        "primitive_contract_valid":validate_action(retrieve)[0],
        "synthesis_contract_valid":validate_action(synth)[0],
        "accept_contract_valid":ok_accept,
        "premature_accept_blocked":premature_accept_blocked,
        "accept_after_derived_evidence":accept_after_compute,
        "failed_operation_no_evidence":failed_no_evidence,
        "evidence_deduplicated":deduplicated,
        "malformed_primitive_rejected":not malformed_ok,
        "missing_synthesis_constraint_rejected":not incomplete_synth_ok,
        "unknown_action_rejected":not mixed_ok,
        "missing_provenance_rejected":provenance_rejected,
        "history_records_failure":any(not h["outcome"].get("success",False) for h in s.history),
    }
    return {
        "experiment_id":"recast-routing-mechanism-v1",
        "checks":checks,
        "all_pass":all(checks.values()),
        "final_evidence":s.evidence,
        "history_length":len(s.history),
        "claim_scope":"Independent routing/state/provenance mechanism verification only; no trained RouterLM, CompilerLM quality, benchmark success, SFT or GRPO claim.",
    }

if __name__=="__main__":
    print(json.dumps(run(),indent=2,sort_keys=True))
