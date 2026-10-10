"""Independent ablation-validity audit for arXiv:2610.07782."""
from __future__ import annotations
import json
from math import sqrt

ALLOWED_AXIS = "kv_enabled"

def c1_component_executed(summary):
    enabled=summary["enabled"]
    return {
        "pass": enabled["trace_write_count"] > 0 and enabled["trace_recall_probe_count"] > 0,
        "write_count": enabled["trace_write_count"],
        "recall_probe_count": enabled["trace_recall_probe_count"],
    }

def c2_pre_run_contamination(store_hits, threshold=0):
    hits=sum(1 for x in store_hits if x)
    return {"pass": hits <= threshold, "hits": hits, "threshold": threshold}

def c3_single_axis(req_on, req_off, order):
    keys=sorted(set(req_on)|set(req_off))
    differing=[k for k in keys if req_on.get(k)!=req_off.get(k)]
    counterbalanced=(len(order)%2==0 and order.count("on-first")==order.count("off-first"))
    return {
        "pass": differing == [ALLOWED_AXIS] and counterbalanced,
        "differing_fields": differing,
        "counterbalanced": counterbalanced,
    }

def sample_sd(xs):
    m=sum(xs)/len(xs)
    return sqrt(sum((x-m)**2 for x in xs)/(len(xs)-1))

def c4_measurement_floor(effect, replicate_scores):
    sd=sample_sd(replicate_scores)
    band=1.96*sd
    return {
        "pass": abs(effect) > band,
        "effect": effect,
        "replicate_sd": sd,
        "approx_95_band": band,
        "resolvable": abs(effect)>band,
    }

def structural_applicability(items):
    reachable=sum(1 for x in items if x["recall_reachable"])
    useful=sum(1 for x in items if x["recall_reachable"] and x["prior_state_relevant"])
    return {
        "n":len(items),
        "reachable":reachable,
        "useful_recall":useful,
        "itt_reachability":reachable/len(items),
        "useful_reachability":useful/len(items),
        "efficacy_testable":useful>0,
    }

def run():
    clean_summary={"enabled":{"trace_write_count":8,"trace_recall_probe_count":8}}
    inert_summary={"enabled":{"trace_write_count":8,"trace_recall_probe_count":0}}

    clean_on={"dataset":"toy","seed":42,"endpoint":"local","parser":"v1","evidence":"fixed","kv_enabled":True}
    clean_off={**clean_on,"kv_enabled":False}
    confounded_off={**clean_off,"parser":"v0","endpoint":"other"}

    # Fixed replicate scores: effect=0.02 is smaller than replicate-scale band.
    replicates=[0.61,0.70,0.63,0.68,0.60,0.69]

    independent_items=[
        {"id":"q1","recall_reachable":False,"prior_state_relevant":False},
        {"id":"q2","recall_reachable":True,"prior_state_relevant":False},
        {"id":"q3","recall_reachable":False,"prior_state_relevant":False},
        {"id":"q4","recall_reachable":True,"prior_state_relevant":False},
        {"id":"q5","recall_reachable":False,"prior_state_relevant":False},
        {"id":"q6","recall_reachable":False,"prior_state_relevant":False},
        {"id":"q7","recall_reachable":True,"prior_state_relevant":False},
        {"id":"q8","recall_reachable":False,"prior_state_relevant":False},
    ]
    shared_state_items=[
        {"id":"s1","recall_reachable":True,"prior_state_relevant":True},
        {"id":"s2","recall_reachable":True,"prior_state_relevant":True},
        {"id":"s3","recall_reachable":False,"prior_state_relevant":False},
        {"id":"s4","recall_reachable":True,"prior_state_relevant":True},
    ]

    cases={
        "clean":{
            "c1":c1_component_executed(clean_summary),
            "c2":c2_pre_run_contamination([False]*8),
            "c3":c3_single_axis(clean_on,clean_off,["on-first","off-first","on-first","off-first"]),
            "c4":c4_measurement_floor(0.20,replicates),
        },
        "c1_inert_component": c1_component_executed(inert_summary),
        "c2_contaminated_store": c2_pre_run_contamination([False,True,False,True]),
        "c3_confounded_arm": c3_single_axis(clean_on,confounded_off,["on-first"]*4),
        "c4_under_measurement_floor": c4_measurement_floor(0.02,replicates),
        "independent_item_regime": structural_applicability(independent_items),
        "shared_state_regime": structural_applicability(shared_state_items),
    }

    checks={
        "clean_c1_pass":cases["clean"]["c1"]["pass"],
        "clean_c2_pass":cases["clean"]["c2"]["pass"],
        "clean_c3_pass":cases["clean"]["c3"]["pass"],
        "clean_large_effect_resolvable":cases["clean"]["c4"]["pass"],
        "detect_inert_component":not cases["c1_inert_component"]["pass"],
        "detect_contamination":not cases["c2_contaminated_store"]["pass"],
        "detect_multi_axis_and_order_confound":not cases["c3_confounded_arm"]["pass"],
        "detect_effect_below_replicate_floor":not cases["c4_under_measurement_floor"]["pass"],
        "independent_items_not_efficacy_testable":not cases["independent_item_regime"]["efficacy_testable"],
        "shared_state_can_test_efficacy":cases["shared_state_regime"]["efficacy_testable"],
    }
    return {
        "experiment_id":"persistent-memory-ablation-audit-v1",
        "cases":cases,
        "checks":checks,
        "all_pass":all(checks.values()),
        "claim_scope":"Independent deterministic audit semantics only; no COA-PKV, KV-cache, benchmark-accuracy, or paper hardware reproduction claim.",
    }

if __name__=="__main__":
    print(json.dumps(run(),indent=2,sort_keys=True))
