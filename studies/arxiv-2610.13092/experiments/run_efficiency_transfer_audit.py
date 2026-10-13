"""Independent efficiency-transfer and published-aggregate audit for arXiv:2610.13092."""
from __future__ import annotations
import json

PAPER = {
    "ReAct": {
        "attempts": 402, "succ_b": 392, "succ_j": 386,
        "task_cost_b": 7.74, "task_cost_j": 3.80,
        "task_time_b": 71.17, "task_time_j": 37.33,
        "decision_cost_b": 468, "decision_cost_j": 122,
        "decision_time_b": 4.13, "decision_time_j": 1.08,
        "paper_cost_per_success_b": 7.93, "paper_cost_per_success_j": 3.96,
        "paper_time_per_success_b": 73.0, "paper_time_per_success_j": 38.9,
    },
    "Reflexion": {
        "attempts": 402, "succ_b": 401, "succ_j": 394,
        "task_cost_b": 8.98, "task_cost_j": 6.05,
        "task_time_b": 99.55, "task_time_j": 61.90,
        "decision_cost_b": 479, "decision_cost_j": 124,
        "decision_time_b": 5.14, "decision_time_j": 1.04,
        "paper_cost_per_success_b": 9.00, "paper_cost_per_success_j": 6.18,
        "paper_time_per_success_b": 99.8, "paper_time_per_success_j": 63.2,
    },
    "T3A": {
        "attempts": 348, "succ_b": 200, "succ_j": 154,
        "task_cost_b": 39.48, "task_cost_j": 32.73,
        "task_time_b": 213.00, "task_time_j": 190.36,
        "decision_cost_b": 1413, "decision_cost_j": 480,
        "decision_time_b": 7.24, "decision_time_j": 1.34,
        "paper_cost_per_success_b": 68.70, "paper_cost_per_success_j": 73.97,
        "paper_time_per_success_b": 370.6, "paper_time_per_success_j": 430.2,
    },
    "AutoDroid": {
        "attempts": 348, "succ_b": 65, "succ_j": 57,
        "task_cost_b": 5.22, "task_cost_j": 1.63,
        "task_time_b": 261.20, "task_time_j": 246.27,
        "decision_cost_b": 436, "decision_cost_j": 94,
        "decision_time_b": 8.13, "decision_time_j": 1.75,
        "paper_cost_per_success_b": 27.93, "paper_cost_per_success_j": 9.93,
        "paper_time_per_success_b": 1398.4, "paper_time_per_success_j": 1503.5,
    },
    "FastAgent": {
        "attempts": 348, "succ_b": 174, "succ_j": 111,
        "task_cost_b": 10.98, "task_cost_j": 6.26,
        "task_time_b": 119.68, "task_time_j": 120.50,
        "decision_cost_b": 1102, "decision_cost_j": 346,
        "decision_time_b": 5.40, "decision_time_j": 1.41,
        "paper_cost_per_success_b": 21.96, "paper_cost_per_success_j": 19.62,
        "paper_time_per_success_b": 239.4, "paper_time_per_success_j": 377.8,
    },
}

def pct_change(new, old):
    return (new / old - 1.0) * 100.0

def delivered(total_per_attempt, attempts, successes):
    return total_per_attempt * attempts / successes

def classify_transfer(decision_delta, task_delta, delivery_delta):
    if decision_delta >= 0:
        return "NO_LOCAL_SAVING"
    if task_delta >= 0:
        return "OVERHEAD_ABSORPTION"
    if delivery_delta >= 0:
        return "DELIVERY_PARADOX"
    return "TRANSFERRED"

def paper_audit():
    rows=[]
    decision_cost_reductions=[]
    decision_time_reductions=[]
    for name,d in PAPER.items():
        dc=pct_change(d["decision_cost_j"],d["decision_cost_b"])
        dt=pct_change(d["decision_time_j"],d["decision_time_b"])
        tc=pct_change(d["task_cost_j"],d["task_cost_b"])
        tt=pct_change(d["task_time_j"],d["task_time_b"])
        cps_b=delivered(d["task_cost_b"],d["attempts"],d["succ_b"])
        cps_j=delivered(d["task_cost_j"],d["attempts"],d["succ_j"])
        tps_b=delivered(d["task_time_b"],d["attempts"],d["succ_b"])
        tps_j=delivered(d["task_time_j"],d["attempts"],d["succ_j"])
        decision_cost_reductions.append(-dc)
        decision_time_reductions.append(-dt)
        rows.append({
            "family":name,
            "decision_cost_delta_pct":dc,
            "decision_time_delta_pct":dt,
            "task_cost_delta_pct":tc,
            "task_time_delta_pct":tt,
            "computed_cost_per_success_b":cps_b,
            "computed_cost_per_success_j":cps_j,
            "computed_time_per_success_b":tps_b,
            "computed_time_per_success_j":tps_j,
            "delivery_class_cost":classify_transfer(dc,tc,pct_change(cps_j,cps_b)),
            "delivery_class_time":classify_transfer(dt,tt,pct_change(tps_j,tps_b)),
            "rounded_table_match": (
                abs(cps_b-d["paper_cost_per_success_b"]) <= 0.03
                and abs(cps_j-d["paper_cost_per_success_j"]) <= 0.03
                and abs(tps_b-d["paper_time_per_success_b"]) <= 0.2
                and abs(tps_j-d["paper_time_per_success_j"]) <= 0.2
            )
        })
    return {
        "rows":rows,
        "decision_cost_reduction_range_pct":[min(decision_cost_reductions),max(decision_cost_reductions)],
        "decision_time_reduction_range_pct":[min(decision_time_reductions),max(decision_time_reductions)],
        "reported_range_compatible": (
            min(decision_cost_reductions) >= 65.8
            and max(decision_cost_reductions) <= 78.7
            and min(decision_time_reductions) >= 73.6
            and max(decision_time_reductions) <= 81.8
        ),
        "all_rounded_table_matches":all(r["rounded_table_match"] for r in rows),
    }

def mechanism_fixture():
    cases=[
        {"id":"direct_transfer","decision_b":100,"decision_j":25,"aux_b":0,"aux_j":5,"env_b":5,"env_j":5,"cost_b":10,"cost_j":4,"success_b":10,"success_j":10},
        {"id":"overhead_absorption","decision_b":100,"decision_j":20,"aux_b":5,"aux_j":90,"env_b":5,"env_j":20,"cost_b":10,"cost_j":8,"success_b":10,"success_j":10},
        {"id":"delivery_paradox","decision_b":100,"decision_j":25,"aux_b":0,"aux_j":10,"env_b":5,"env_j":5,"cost_b":10,"cost_j":7,"success_b":10,"success_j":6},
    ]
    out=[]
    for c in cases:
        total_b=c["decision_b"]+c["aux_b"]+c["env_b"]
        total_j=c["decision_j"]+c["aux_j"]+c["env_j"]
        decision_delta=pct_change(c["decision_j"],c["decision_b"])
        task_delta=pct_change(total_j,total_b)
        cps_b=c["cost_b"]*10/c["success_b"]
        cps_j=c["cost_j"]*10/c["success_j"]
        delivery_delta=pct_change(cps_j,cps_b)
        out.append({
            "id":c["id"],
            "decision_delta_pct":decision_delta,
            "task_time_delta_pct":task_delta,
            "cost_per_success_delta_pct":delivery_delta,
            "classification":classify_transfer(decision_delta,task_delta,delivery_delta),
        })
    recovery={
        "baseline":{"initial_success":8,"initial_fail":2,"recovered":2,"final_success":10},
        "fast_selector":{"initial_success":9,"initial_fail":1,"recovered":0,"final_success":9},
    }
    checks={
        "direct_transfer_detected":out[0]["classification"]=="TRANSFERRED",
        "overhead_absorption_detected":out[1]["classification"]=="OVERHEAD_ABSORPTION",
        "delivery_paradox_detected":out[2]["classification"]=="DELIVERY_PARADOX",
        "better_initial_can_end_worse": (
            recovery["fast_selector"]["initial_success"] > recovery["baseline"]["initial_success"]
            and recovery["fast_selector"]["final_success"] < recovery["baseline"]["final_success"]
        ),
    }
    return {"cases":out,"recovery_fixture":recovery,"checks":checks,"all_pass":all(checks.values())}

def main():
    paper=paper_audit()
    mechanism=mechanism_fixture()
    result={
        "experiment_id":"jev-efficiency-transfer-audit-v1",
        "paper_aggregate_audit":paper,
        "independent_mechanism_fixture":mechanism,
        "all_pass":paper["reported_range_compatible"] and paper["all_rounded_table_matches"] and mechanism["all_pass"],
        "claim_scope":"Published aggregate arithmetic plus independent accounting semantics only. No Jev API execution, ALFWorld/AndroidWorld rerun, GPT-5.6 Luna trajectory reproduction, or paper-level reproduction claim."
    }
    print(json.dumps(result,indent=2,sort_keys=True))

if __name__=="__main__":
    main()
