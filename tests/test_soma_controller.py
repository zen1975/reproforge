from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT=Path(__file__).resolve().parents[1]
STUDY=ROOT/"studies/arxiv-2610.26793"
CONTROLLER=STUDY/"experiments/controller.py"
RUNNER=STUDY/"experiments/run_soma_synthetic.py"

def load(path:Path,name:str):
    spec=importlib.util.spec_from_file_location(name,path)
    assert spec is not None and spec.loader is not None
    module=importlib.util.module_from_spec(spec)
    sys.modules[name]=module
    spec.loader.exec_module(module)
    return module

def test_log_odds_clips_extremes_and_rejects_invalid_values():
    mod=load(CONTROLLER,"soma_test_extremes")
    assert mod.log_odds(0.0)<0 and mod.log_odds(1.0)>0
    with pytest.raises(ValueError):mod.log_odds(-0.01)
    with pytest.raises(ValueError):mod.log_odds(float("nan"))

def test_reminder_precedes_intervention_and_terminal_state_is_sticky():
    mod=load(CONTROLLER,"soma_test_order")
    gate=mod.SomaController(threshold=0.5)
    assert gate.observe(0.8)=="REMIND" and gate.score==0.0
    assert gate.observe(0.8)=="INTERVENE"
    assert gate.observe(0.8)=="STOPPED"

def test_recovery_resets_the_reminder_episode():
    mod=load(CONTROLLER,"soma_test_recovery")
    gate=mod.SomaController(threshold=0.5)
    assert gate.observe(0.8)=="REMIND"
    assert gate.observe(0.2)=="CONTINUE" and gate.reminded is False
    assert gate.observe(0.8)=="REMIND"
    assert gate.observe(0.2)=="CONTINUE" and gate.stopped is False

def test_no_reminder_variant_can_intervene_on_first_positive_scan():
    mod=load(CONTROLLER,"soma_test_no_reminder")
    gate=mod.SomaController(threshold=0.5,reminder_first=False)
    assert gate.observe(0.8)=="INTERVENE"

def test_threshold_grid_and_synthetic_split_are_frozen():
    mod=load(CONTROLLER,"soma_test_grid")
    fixture=json.loads((STUDY/"fixtures/soma-synthetic-v1.json").read_text(encoding="utf-8"))
    assert list(mod.THRESHOLD_GRID)==fixture["threshold_grid"]
    assert fixture["persistent_case_count"]==10 and fixture["recovery_case_count"]==10
    threshold,harms=mod.choose_threshold([
        {"baseline_correct":True,"correct_by_threshold":{"0.25":False,"0.5":True}},
        {"baseline_correct":True,"correct_by_threshold":{"0.25":True,"0.5":True}}
    ],(0.25,0.5),delta=0)
    assert threshold==0.5 and harms["0.25"]==1 and harms["0.5"]==0

def test_synthetic_benchmark_passes_without_paper_level_claims():
    runner=load(RUNNER,"soma_test_benchmark")
    result=runner.run()
    assert result["verdict"]=="PASS" and result["paper_level_reproduction"] is False
    assert result["metrics"]["soma_persistent_interventions"]==10
    assert result["metrics"]["soma_recovery_interventions"]==0
    assert result["metrics"]["no_reminder_recovery_interventions"]==10
    assert result["metrics"]["vanilla_interventions"]==0

def test_saved_evidence_matches_core_metrics_and_stays_partial():
    runner=load(RUNNER,"soma_test_evidence")
    evidence=json.loads((STUDY/"evidence/soma-synthetic-v1.evidence.json").read_text(encoding="utf-8"))
    metrics=runner.run()["metrics"]
    assert evidence["reproduction_status"]=="PARTIAL"
    assert evidence["result"]["verdict"]=="PASS"
    assert evidence["result"]["soma_persistent_interventions"]==metrics["soma_persistent_interventions"]
    assert evidence["result"]["soma_recovery_interventions"]==metrics["soma_recovery_interventions"]
    assert evidence["result"]["no_reminder_recovery_interventions"]==metrics["no_reminder_recovery_interventions"]

def test_manifest_status_and_capability_candidate_validate():
    from reproforge.validation import load_document, validate_document
    manifest=load_document(STUDY/"manifest.yaml")
    assert validate_document(manifest,load_document(ROOT/"schemas/paper-manifest.schema.json"))==[]
    status=load_document(STUDY/"status.yaml")
    assert validate_document(status,load_document(ROOT/"schemas/study-status.schema.json"))==[]
    assert status["lifecycle"]=="PROTOCOL_VERIFIED" and status["reproduction_status"]=="PARTIAL"
    capability=load_document(STUDY/"capability-candidate.yaml")
    assert validate_document(capability,load_document(ROOT/"schemas/capability.schema.json"))==[]
    assert capability["status"]=="experimental"
