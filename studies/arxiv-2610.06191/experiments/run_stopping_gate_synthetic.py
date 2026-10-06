"""Frozen synthetic mechanism benchmark for evidence-aware stopping."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CAP = ROOT / "capabilities" / "agent.evidence-aware-stopping-gate" / "gate.py"


def _load_gate():
    spec = importlib.util.spec_from_file_location("evidence_stopping_gate", CAP)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load gate")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SCENARIOS = [
    {"id":"persistent-8","judgments":["USELESS"]*8,"baseline_calls":8,"expected_gate_calls":5,"should_fire":True},
    {"id":"recover-1","judgments":["USELESS","USEFUL","USEFUL","USEFUL","USEFUL","USEFUL"],"baseline_calls":6,"expected_gate_calls":6,"should_fire":False},
    {"id":"recover-3","judgments":["USELESS","USELESS","USELESS","USEFUL","USELESS","USELESS"],"baseline_calls":6,"expected_gate_calls":6,"should_fire":False},
    {"id":"exact-5","judgments":["USELESS"]*5,"baseline_calls":5,"expected_gate_calls":5,"should_fire":True},
    {"id":"intermittent","judgments":["USELESS","USELESS","USEFUL","USELESS","USELESS","USELESS","USELESS","USEFUL"],"baseline_calls":8,"expected_gate_calls":8,"should_fire":False},
    {"id":"late-persistent","judgments":["USEFUL","USEFUL","USELESS","USELESS","USELESS","USELESS","USELESS","USELESS"],"baseline_calls":8,"expected_gate_calls":7,"should_fire":True},
]


def run():
    mod = _load_gate()
    rows = []
    saved = 0
    correct = 0
    for scenario in SCENARIOS:
        gate = mod.EvidenceStoppingGate(threshold=5)
        calls = 0
        fired = False
        for judgment in scenario["judgments"]:
            calls += 1
            fired = gate.update(judgment)
            if fired:
                break
        ok = fired is scenario["should_fire"] and calls == scenario["expected_gate_calls"]
        correct += int(ok)
        saved += scenario["baseline_calls"] - calls
        rows.append({
            "id":scenario["id"],
            "fired":fired,
            "gate_calls":calls,
            "baseline_calls":scenario["baseline_calls"],
            "saved_calls":scenario["baseline_calls"]-calls,
            "expected_gate_calls":scenario["expected_gate_calls"],
            "pass":ok,
        })

    # sticky behavior after firing
    sticky = mod.EvidenceStoppingGate(threshold=5)
    for _ in range(5):
        sticky.update("USELESS")
    sticky_pass = sticky.update("USEFUL") is True and sticky.fired is True

    return {
        "experiment_id":"stopping-gate-synthetic-v1",
        "threshold":5,
        "scenario_count":len(SCENARIOS),
        "scenario_pass_rate":correct/len(SCENARIOS),
        "total_tool_calls_saved_vs_deadline_baseline":saved,
        "sticky_after_fire_pass":sticky_pass,
        "all_pass":correct==len(SCENARIOS) and sticky_pass,
        "rows":rows,
        "boundary":"Independent synthetic mechanism test only; not a reproduction of agent behavior or paper benchmark results."
    }


if __name__=="__main__":
    print(json.dumps(run(),indent=2,sort_keys=True))
