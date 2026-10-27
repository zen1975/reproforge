"""Synthetic mechanism benchmark for arXiv 2610.26793."""
from __future__ import annotations
import argparse
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any,Sequence

ROOT=Path(__file__).resolve().parents[3]
CONTROLLER_PATH=ROOT/"studies/arxiv-2610.26793/experiments/controller.py"
FIXTURE_PATH=ROOT/"studies/arxiv-2610.26793/fixtures/soma-synthetic-v1.json"
DEFAULT_OUTPUT=ROOT/"studies/arxiv-2610.26793/evidence/soma-synthetic-v1.evidence.json"

def _load_controller():
    spec=importlib.util.spec_from_file_location("soma_controller_for_synthetic",CONTROLLER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {CONTROLLER_PATH}")
    module=importlib.util.module_from_spec(spec)
    sys.modules[spec.name]=module
    spec.loader.exec_module(module)
    return module

def _evaluate(probabilities:Sequence[float],threshold:float,controller_type:Any,
              reminder_first:bool,enabled:bool)->dict[str,Any]:
    gate=controller_type(threshold=threshold,reminder_first=reminder_first,
                         intervention_enabled=enabled)
    actions=[];intervention_scan=None
    for scan,p in enumerate(probabilities,start=1):
        action=gate.observe(p);actions.append(action)
        if action=="INTERVENE":
            intervention_scan=scan
            break
    return {"actions":actions,"intervention_scan":intervention_scan,
            "reminders":actions.count("REMIND")}

def run()->dict[str,Any]:
    fixture=json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    module=_load_controller()
    grid=tuple(float(x) for x in fixture["threshold_grid"])
    calibration=[]
    keys=[module.threshold_key(x) for x in grid]
    calibration=[
        {"id":"cal-01","baseline_correct":True,
         "correct_by_threshold":{k:k!="0.25" for k in keys}},
        {"id":"cal-02","baseline_correct":True,
         "correct_by_threshold":{k:True for k in keys}},
        {"id":"cal-03","baseline_correct":False,
         "correct_by_threshold":{k:False for k in keys}},
        {"id":"cal-04","baseline_correct":True,
         "correct_by_threshold":{k:True for k in keys}},
    ]
    test_cases=[]
    for i in range(int(fixture["persistent_case_count"])):
        p=round(0.70+i*0.01,2)
        test_cases.append({"id":f"persistent-{i+1:02d}","scenario":"persistent","probabilities":[p,p]})
    for i in range(int(fixture["recovery_case_count"])):
        p1,p2=round(0.70+i*0.01,2),round(0.30-i*0.01,2)
        test_cases.append({"id":f"recovery-{i+1:02d}","scenario":"recovery","probabilities":[p1,p2,0.80]})
    selected,harms=module.choose_threshold(calibration,grid,delta=0.0)
    disjoint={x["id"] for x in calibration}.isdisjoint({x["id"] for x in test_cases})
    rows=[]
    for case in test_cases:
        p=case["probabilities"]
        rows.append({"id":case["id"],"scenario":case["scenario"],
            "soma":_evaluate(p,selected,module.SomaController,True,True),
            "no_reminder":_evaluate(p,selected,module.SomaController,False,True),
            "remind_only":_evaluate(p,selected,module.SomaController,True,False),
            "vanilla":_evaluate(p,selected,module.SomaController,False,False)})
    def count(scenario:str,mode:str)->int:
        return sum(x[mode]["intervention_scan"] is not None for x in rows if x["scenario"]==scenario)
    scans=[x["soma"]["intervention_scan"] for x in rows
           if x["scenario"]=="persistent" and x["soma"]["intervention_scan"] is not None]
    n_p=int(fixture["persistent_case_count"]);n_r=int(fixture["recovery_case_count"])
    metrics={"persistent_case_count":n_p,"recovery_case_count":n_r,
        "soma_persistent_interventions":count("persistent","soma"),
        "soma_recovery_interventions":count("recovery","soma"),
        "soma_mean_scan_to_intervention_persistent":round(sum(scans)/len(scans),6) if scans else None,
        "soma_recovery_intervention_rate":count("recovery","soma")/max(1,n_r),
        "no_reminder_persistent_interventions":count("persistent","no_reminder"),
        "no_reminder_recovery_interventions":count("recovery","no_reminder"),
        "no_reminder_recovery_intervention_rate":count("recovery","no_reminder")/max(1,n_r),
        "remind_only_persistent_interventions":count("persistent","remind_only"),
        "remind_only_recovery_interventions":count("recovery","remind_only"),
        "vanilla_interventions":sum(x["vanilla"]["intervention_scan"] is not None for x in rows)}
    passed=(disjoint and metrics["soma_persistent_interventions"]==n_p==10
        and metrics["soma_recovery_interventions"]==0
        and metrics["no_reminder_recovery_interventions"]==n_r==10
        and metrics["remind_only_persistent_interventions"]==0
        and metrics["vanilla_interventions"]==0 and selected==0.5)
    return {"experiment_id":"soma-synthetic-mechanism-v1","fixture_id":fixture["fixture_id"],
        "source":"https://arxiv.org/abs/2610.26793",
        "calibration":{"split_id":fixture["calibration_split_id"],"case_count":len(calibration),
            "test_split_id":fixture["test_split_id"],"test_case_count":len(test_cases),
            "disjoint":disjoint,"threshold_grid":list(grid),"delta":0.0,
            "harm_by_threshold":harms,"selected_threshold":selected,
            "selected_threshold_is_synthetic_only":True},
        "protocol_constants":{"scan_interval_thinking_tokens":256,"max_extra_tokens_to_line_break":128,
            "state_window_tokens":2048,"generation_limit_tokens":32768,"temperature":0.6,"top_p":0.95,
            "top_k_qwen3":20,"threshold_grid":list(grid),"calibration_delta":0.0},
        "metrics":metrics,"paper_level_reproduction":False,
        "verdict":"PASS" if passed else "FAIL"}

def build_evidence()->dict[str,Any]:
    return {"evidence_schema_version":"1.0","study_id":"arxiv-2610.26793",
        "evidence_id":"soma-synthetic-mechanism-v1","evidence_type":"synthetic_mechanism_test",
        "created_on":"2026-10-21","reproduction_status":"PARTIAL","paper_level_reproduction":False,
        "result":run(),
        "interpretation":"This synthetic test checks controller transitions and threshold selection, not model accuracy or token savings.",
        "limitations":["All monitor probabilities and correctness labels are synthetic.",
            "No hosted monitor API or reasoning model was called.",
            "No paper benchmark data, author code, model weights, or PDF assets were copied."]}

def main()->None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,default=DEFAULT_OUTPUT)
    args=parser.parse_args()
    evidence=build_evidence()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(evidence,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(evidence,indent=2,sort_keys=True))

if __name__=="__main__":
    main()
