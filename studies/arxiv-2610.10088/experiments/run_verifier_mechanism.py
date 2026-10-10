"""Independent mechanism verification for arXiv:2610.10088 SkillSandbox."""
from __future__ import annotations
import json
from dataclasses import dataclass

GAMMA = 0.9  # analogue parameter; paper specifies only 0 < gamma < 1 in public text.

@dataclass(frozen=True)
class Scenario:
    condition: str
    source_context: tuple[str, ...]
    new_context: tuple[str, ...]
    required_features: tuple[str, ...]

def validate_scenario(s: Scenario) -> dict:
    relevant = all(feature in s.new_context for feature in s.required_features)
    novel = s.new_context != s.source_context
    return {"relevant": relevant, "novel": novel, "valid": relevant and novel}

def delta_u(r_plus, r_minus, remaining_plus, remaining_minus, gamma=GAMMA):
    return r_plus * (gamma ** remaining_plus) - r_minus * (gamma ** remaining_minus)

def pair_score(executable, r_plus, r_minus, remaining_plus, remaining_minus):
    return int(bool(executable)) * delta_u(
        r_plus, r_minus, remaining_plus, remaining_minus
    )

def skill_score(scenarios):
    per_scenario = []
    for pairs in scenarios:
        values = [pair_score(**p) for p in pairs]
        per_scenario.append(sum(values) / len(values) if values else 0.0)
    score = sum(per_scenario) / len(per_scenario) if per_scenario else 0.0
    return score, ("KEEP" if score > 0 else "REJECT")

def run():
    source=("multipack","compare-total-volume","brand-A")
    scenario_checks={
        "relevant_novel": validate_scenario(Scenario(
            "compare multipack by total volume", source,
            ("multipack","compare-total-volume","brand-B"),
            ("multipack","compare-total-volume"),
        )),
        "irrelevant_novel": validate_scenario(Scenario(
            "compare multipack by total volume", source,
            ("single-item","compare-price","brand-B"),
            ("multipack","compare-total-volume"),
        )),
        "relevant_not_novel": validate_scenario(Scenario(
            "compare multipack by total volume", source, source,
            ("multipack","compare-total-volume"),
        )),
    }

    helpful=[
        [{"executable":1,"r_plus":1,"r_minus":0,"remaining_plus":2,"remaining_minus":3}],
        [{"executable":1,"r_plus":1,"r_minus":1,"remaining_plus":1,"remaining_minus":4}],
    ]
    harmful=[
        [{"executable":1,"r_plus":0,"r_minus":1,"remaining_plus":2,"remaining_minus":2}],
        [{"executable":1,"r_plus":1,"r_minus":1,"remaining_plus":5,"remaining_minus":2}],
    ]
    nonexec=[
        [{"executable":0,"r_plus":1,"r_minus":0,"remaining_plus":1,"remaining_minus":4}]
    ]
    scores={}
    for name,data in (("helpful",helpful),("harmful",harmful),("nonexec",nonexec)):
        score,verdict=skill_score(data)
        scores[name]={"score":score,"verdict":verdict}

    checks={
        "scenario_relevant_novel_valid": scenario_checks["relevant_novel"]["valid"],
        "scenario_irrelevant_rejected": not scenario_checks["irrelevant_novel"]["valid"],
        "scenario_source_identical_rejected": not scenario_checks["relevant_not_novel"]["valid"],
        "helpful_positive_keep": scores["helpful"]["score"] > 0 and scores["helpful"]["verdict"]=="KEEP",
        "harmful_negative_reject": scores["harmful"]["score"] < 0 and scores["harmful"]["verdict"]=="REJECT",
        "nonexec_zero_reject": scores["nonexec"]["score"] == 0 and scores["nonexec"]["verdict"]=="REJECT",
    }
    return {
        "experiment_id":"skillsandbox-verifier-mechanism-v1",
        "gamma":GAMMA,
        "gamma_scope":"Analogue parameter only; public paper text constrains 0<gamma<1 but does not expose a numeric value in the inspected HTML.",
        "scenario_checks":scenario_checks,
        "scores":scores,
        "checks":checks,
        "all_pass":all(checks.values()),
        "claim_scope":"Independent mechanism verification only; no ALFWorld/WebShop or paper-scale performance claim.",
    }

if __name__=="__main__":
    print(json.dumps(run(),indent=2,sort_keys=True))
