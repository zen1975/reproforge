"""Independent, deliberately bounded static checks for FAOP-like workflow IR.

This is a mechanism implementation, not the author's SkillBase compiler and not a
complete implementation of the FAOP formalism.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


NORMAL_FORM_CODES = {
    "FNF-1": ("FNF1_",),
    "FNF-2": ("FNF2_",),
    "FNF-3": ("FNF3_",),
    "FNF-4": ("FNF4_",),
}


def _strings(value: Any) -> list[str] | None:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        return None
    return value


def verify_registry(
    workflows: Sequence[Mapping[str, Any]],
    *,
    require_termination: bool = False,
    require_bounds: bool = False,
) -> dict[str, Any]:
    """Check a list of workflow declarations and return machine-readable findings.

    Supported IR nodes: action, value, call, interrupt, checkpoint, if, and loop.
    Branch outputs are intersected; loop outputs are not assumed to exist after the
    loop because the body may execute zero times. Declared effects/scopes are checked,
    not verified against the actual external implementation.
    """
    violations: list[dict[str, str]] = []
    if not isinstance(workflows, Sequence) or isinstance(workflows, (str, bytes)):
        return {
            "valid": False,
            "workflow_count": 0,
            "normal_forms": {name: False for name in NORMAL_FORM_CODES},
            "extensions": {"+V": False, "+B": False},
            "highest_normal_form": 0,
            "violations": [{"code": "FNF3_INVALID_REGISTRY", "workflow_id": "", "step_id": "", "message": "workflows must be a sequence of workflow objects"}],
        }

    by_id: dict[str, Mapping[str, Any]] = {}
    for index, workflow in enumerate(workflows):
        if not isinstance(workflow, Mapping):
            violations.append({"code": "FNF3_INVALID_WORKFLOW", "workflow_id": str(index), "step_id": "", "message": "workflow entry must be an object"})
            continue
        workflow_id = workflow.get("id")
        if not isinstance(workflow_id, str) or not workflow_id:
            violations.append({"code": "FNF3_MISSING_ID", "workflow_id": str(index), "step_id": "", "message": "workflow id must be a non-empty string"})
            continue
        if workflow_id in by_id:
            violations.append({"code": "FNF3_DUPLICATE_ID", "workflow_id": workflow_id, "step_id": "", "message": "registry id must have exactly one canonical definition"})
        else:
            by_id[workflow_id] = workflow

    call_graph: dict[str, set[str]] = {workflow_id: set() for workflow_id in by_id}

    def add(code: str, workflow_id: str, step_id: str, message: str) -> None:
        violations.append({"code": code, "workflow_id": workflow_id, "step_id": step_id, "message": message})

    def check_nodes(
        nodes: Any,
        available: set[str],
        workflow_id: str,
        parent_scope: set[str],
    ) -> set[str]:
        if not isinstance(nodes, list):
            add("FNF2_INVALID_BODY", workflow_id, "", "steps/body must be a list")
            return set(available)
        state = set(available)
        for index, node in enumerate(nodes):
            if not isinstance(node, Mapping):
                add("FNF2_INVALID_NODE", workflow_id, str(index), "step must be an object")
                continue
            step_id = node.get("id") if isinstance(node.get("id"), str) else str(index)
            kind = node.get("kind")
            if kind not in {"action", "value", "call", "interrupt", "checkpoint", "if", "loop"}:
                add("FNF2_UNKNOWN_NODE_KIND", workflow_id, step_id, "unsupported or missing node kind")
                continue

            declared_scope = node.get("scope")
            if declared_scope is not None:
                scope_list = _strings(declared_scope)
                if scope_list is None:
                    add("FNF4_INVALID_SCOPE", workflow_id, step_id, "node scope must be a list of tool names")
                elif not set(scope_list).issubset(parent_scope):
                    add("FNF4_SCOPE_ESCALATION", workflow_id, step_id, "node scope exceeds its parent workflow scope")

            if kind == "call":
                target = node.get("target")
                if not isinstance(target, str) or target not in by_id:
                    add("FNF3_UNKNOWN_CALL", workflow_id, step_id, "call target must resolve to one registered workflow")
                    reads: list[str] = []
                    writes: list[str] = []
                else:
                    call_graph.setdefault(workflow_id, set()).add(target)
                    callee = by_id[target]
                    reads = _strings(callee.get("inputs")) or []
                    writes = _strings(callee.get("outputs")) or []
                    callee_scope = _strings(callee.get("scope"))
                    if callee_scope is None:
                        add("FNF4_INVALID_SCOPE", workflow_id, step_id, f"callee {target} must declare a scope list")
                    elif not set(callee_scope).issubset(parent_scope):
                        add("FNF4_SCOPE_ESCALATION", workflow_id, step_id, f"callee {target} requires tools outside caller scope")
            else:
                reads_value = node.get("reads", [])
                writes_value = node.get("writes", [])
                reads = _strings(reads_value)
                writes = _strings(writes_value)
                if reads is None:
                    add("FNF2_INVALID_READS", workflow_id, step_id, "reads must be a list of field names")
                    reads = []
                if writes is None:
                    add("FNF2_INVALID_WRITES", workflow_id, step_id, "writes must be a list of field names")
                    writes = []

            missing = sorted(set(reads) - state)
            if missing:
                add("FNF2_UNPRODUCED_FIELD", workflow_id, step_id, f"reads fields not guaranteed available: {', '.join(missing)}")

            tool = node.get("tool")
            if tool is not None:
                if not isinstance(tool, str) or tool not in parent_scope:
                    add("FNF4_TOOL_OUT_OF_SCOPE", workflow_id, step_id, "step tool is not granted by the parent workflow scope")

            if kind not in {"if", "loop", "call"}:
                effects = _strings(node.get("effects", []))
                if effects is None:
                    add("FNF1_INVALID_EFFECTS", workflow_id, step_id, "effects must be a list of effect identifiers")
                elif len(effects) > 1:
                    add("FNF1_MULTIPLE_EFFECTS", workflow_id, step_id, "leaf declares more than one mutating effect")
                if kind == "value" and effects:
                    add("FNF1_VALUE_HAS_EFFECT", workflow_id, step_id, "value leaves must not declare mutating effects")
                if require_bounds and kind == "action":
                    time_bound = node.get("time_bound_ms")
                    cost_bound = node.get("cost_bound_usd")
                    if not isinstance(time_bound, (int, float)) or isinstance(time_bound, bool) or time_bound < 0:
                        add("B_MISSING_BOUND", workflow_id, step_id, "action requires a non-negative time_bound_ms")
                    if not isinstance(cost_bound, (int, float)) or isinstance(cost_bound, bool) or cost_bound < 0:
                        add("B_MISSING_BOUND", workflow_id, step_id, "action requires a non-negative cost_bound_usd")
                state.update(writes)
            elif kind == "call":
                state.update(writes)
            elif kind == "if":
                then_state = check_nodes(node.get("then", []), set(state), workflow_id, parent_scope)
                else_state = check_nodes(node.get("else", []), set(state), workflow_id, parent_scope)
                state.update(then_state.intersection(else_state) - state)
            elif kind == "loop":
                max_iterations = node.get("max_iterations")
                if require_termination and (not isinstance(max_iterations, int) or isinstance(max_iterations, bool) or max_iterations < 1):
                    add("V_UNBOUNDED_LOOP", workflow_id, step_id, "loop requires a positive integer max_iterations")
                elif max_iterations is not None and (not isinstance(max_iterations, int) or isinstance(max_iterations, bool) or max_iterations < 1):
                    add("V_INVALID_LOOP_BOUND", workflow_id, step_id, "max_iterations must be a positive integer when provided")
                check_nodes(node.get("body", []), set(state), workflow_id, parent_scope)
                # Deliberately do not propagate loop writes: the body may run zero times.
        return state

    for workflow_id, workflow in by_id.items():
        inputs = _strings(workflow.get("inputs"))
        outputs = _strings(workflow.get("outputs"))
        scope_list = _strings(workflow.get("scope"))
        if inputs is None or outputs is None:
            add("FNF2_INVALID_INTERFACE", workflow_id, "", "inputs and outputs must be lists of field names")
            inputs = inputs or []
        if scope_list is None:
            add("FNF4_INVALID_SCOPE", workflow_id, "", "workflow must declare a scope list")
            scope_list = []
        check_nodes(workflow.get("steps"), set(inputs), workflow_id, set(scope_list))
        if outputs is not None:
            # The interface is declarative; this bounded checker does not infer all outputs
            # through complex control flow. It does verify that declared outputs are strings.
            if any(not isinstance(field, str) for field in outputs):
                add("FNF2_INVALID_INTERFACE", workflow_id, "", "outputs must contain only field names")

    visiting: set[str] = set()
    visited: set[str] = set()
    reported_cycles: set[tuple[str, ...]] = set()

    def visit(workflow_id: str, stack: list[str]) -> None:
        if workflow_id in visiting:
            cycle = tuple(stack[stack.index(workflow_id):] + [workflow_id])
            if cycle not in reported_cycles:
                reported_cycles.add(cycle)
                add("FNF3_CALL_CYCLE", workflow_id, "", "call graph must be acyclic: " + " -> ".join(cycle))
            return
        if workflow_id in visited:
            return
        visiting.add(workflow_id)
        stack.append(workflow_id)
        for target in sorted(call_graph.get(workflow_id, set())):
            if target in by_id:
                visit(target, stack)
        stack.pop()
        visiting.remove(workflow_id)
        visited.add(workflow_id)

    for workflow_id in sorted(by_id):
        visit(workflow_id, [])

    normal_forms = {
        name: not any(v["code"].startswith(prefix) for v in violations for prefix in prefixes)
        for name, prefixes in NORMAL_FORM_CODES.items()
    }
    extensions = {
        "+V": not any(violation["code"].startswith("V_") for violation in violations),
        "+B": not any(violation["code"].startswith("B_") for violation in violations),
    }
    highest = 0
    for level, name in enumerate(("FNF-1", "FNF-2", "FNF-3", "FNF-4"), start=1):
        if normal_forms[name]:
            highest = level
        else:
            break
    return {
        "valid": not violations,
        "workflow_count": len(by_id),
        "normal_forms": normal_forms,
        "extensions": extensions,
        "highest_normal_form": highest,
        "violations": sorted(violations, key=lambda item: (item["workflow_id"], item["step_id"], item["code"])),
    }
