"""Mechanism tests for the independent FAOP-like static verifier."""

from __future__ import annotations

import importlib.util
from pathlib import Path

MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "capabilities"
    / "agent.faop-workflow-static-verifier"
    / "verifier.py"
)
SPEC = importlib.util.spec_from_file_location("faop_static_verifier", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
verify_registry = MODULE.verify_registry


def base_workflow() -> dict:
    return {
        "id": "main.v1",
        "inputs": ["request"],
        "outputs": ["report"],
        "scope": ["crm.read", "files.write"],
        "steps": [
            {
                "id": "load",
                "kind": "action",
                "reads": ["request"],
                "writes": ["customer"],
                "effects": ["http.get"],
                "tool": "crm.read",
                "time_bound_ms": 100,
                "cost_bound_usd": 0.01,
            },
            {
                "id": "write",
                "kind": "action",
                "reads": ["customer"],
                "writes": ["report"],
                "effects": ["file.write"],
                "tool": "files.write",
                "time_bound_ms": 100,
                "cost_bound_usd": 0.01,
            },
        ],
    }


def codes(result: dict) -> set[str]:
    return {item["code"] for item in result["violations"]}


def test_valid_linear_workflow_passes_all_four_normal_forms_and_extensions() -> None:
    result = verify_registry([base_workflow()], require_termination=True, require_bounds=True)
    assert result["valid"] is True
    assert result["normal_forms"] == {"FNF-1": True, "FNF-2": True, "FNF-3": True, "FNF-4": True}
    assert result["extensions"] == {"+V": True, "+B": True}
    assert result["highest_normal_form"] == 4


def test_multiple_effects_break_atomicity() -> None:
    workflow = base_workflow()
    workflow["steps"][0]["effects"] = ["http.get", "llm.call"]
    assert "FNF1_MULTIPLE_EFFECTS" in codes(verify_registry([workflow]))


def test_unproduced_field_is_rejected() -> None:
    workflow = base_workflow()
    workflow["steps"][1]["reads"] = ["missing_customer"]
    assert "FNF2_UNPRODUCED_FIELD" in codes(verify_registry([workflow]))


def test_unknown_call_target_is_rejected() -> None:
    workflow = base_workflow()
    workflow["steps"] = [{"id": "call", "kind": "call", "target": "absent.v1"}]
    assert "FNF3_UNKNOWN_CALL" in codes(verify_registry([workflow]))


def test_recursive_call_graph_is_rejected() -> None:
    a = {"id": "a.v1", "inputs": [], "outputs": [], "scope": [], "steps": [{"id": "to-b", "kind": "call", "target": "b.v1"}]}
    b = {"id": "b.v1", "inputs": [], "outputs": [], "scope": [], "steps": [{"id": "to-a", "kind": "call", "target": "a.v1"}]}
    assert "FNF3_CALL_CYCLE" in codes(verify_registry([a, b]))


def test_tool_outside_parent_scope_is_rejected() -> None:
    workflow = base_workflow()
    workflow["steps"][0]["tool"] = "payments.write"
    assert "FNF4_TOOL_OUT_OF_SCOPE" in codes(verify_registry([workflow]))


def test_callee_scope_escalation_is_rejected() -> None:
    child = {"id": "child.v1", "inputs": ["request"], "outputs": ["customer"], "scope": ["payments.write"], "steps": []}
    parent = base_workflow()
    parent["steps"] = [{"id": "call-child", "kind": "call", "target": "child.v1"}]
    assert "FNF4_SCOPE_ESCALATION" in codes(verify_registry([parent, child]))


def test_unbounded_loop_is_rejected_when_termination_is_required() -> None:
    workflow = base_workflow()
    workflow["steps"] = [{"id": "repeat", "kind": "loop", "reads": [], "body": []}]
    assert "V_UNBOUNDED_LOOP" in codes(verify_registry([workflow], require_termination=True))


def test_missing_time_and_cost_bounds_are_rejected() -> None:
    workflow = base_workflow()
    del workflow["steps"][0]["time_bound_ms"]
    del workflow["steps"][0]["cost_bound_usd"]
    assert "B_MISSING_BOUND" in codes(verify_registry([workflow], require_bounds=True))


def test_branch_only_guaranteed_outputs_flow_forward() -> None:
    workflow = base_workflow()
    workflow["steps"] = [
        {"id": "branch", "kind": "if", "reads": ["request"], "then": [{"id": "yes", "kind": "value", "reads": [], "writes": ["token"]}], "else": []},
        {"id": "use", "kind": "value", "reads": ["token"], "writes": ["report"]},
    ]
    assert "FNF2_UNPRODUCED_FIELD" in codes(verify_registry([workflow]))


def test_duplicate_registry_ids_are_rejected() -> None:
    workflow = base_workflow()
    duplicate = dict(workflow)
    assert "FNF3_DUPLICATE_ID" in codes(verify_registry([workflow, duplicate]))


def test_callee_inputs_must_exist_at_call_site() -> None:
    child = {"id": "child.v1", "inputs": ["secret"], "outputs": ["result"], "scope": [], "steps": []}
    parent = base_workflow()
    parent["steps"] = [{"id": "call-child", "kind": "call", "target": "child.v1"}]
    assert "FNF2_UNPRODUCED_FIELD" in codes(verify_registry([parent, child]))


def test_loop_body_writes_are_not_assumed_after_zero_or_more_iterations() -> None:
    workflow = base_workflow()
    workflow["steps"] = [
        {"id": "repeat", "kind": "loop", "max_iterations": 3, "body": [{"id": "produce", "kind": "value", "reads": [], "writes": ["token"]}]},
        {"id": "use", "kind": "value", "reads": ["token"], "writes": ["report"]},
    ]
    assert "FNF2_UNPRODUCED_FIELD" in codes(verify_registry([workflow]))


def test_call_outputs_are_available_after_return() -> None:
    child = {"id": "child.v1", "inputs": ["request"], "outputs": ["customer"], "scope": ["crm.read"], "steps": []}
    parent = {
        "id": "parent.v1",
        "inputs": ["request"],
        "outputs": ["report"],
        "scope": ["crm.read"],
        "steps": [
            {"id": "call-child", "kind": "call", "target": "child.v1"},
            {"id": "use-customer", "kind": "value", "reads": ["customer"], "writes": ["report"]},
        ],
    }
    result = verify_registry([parent, child])
    assert "FNF2_UNPRODUCED_FIELD" not in codes(result)
