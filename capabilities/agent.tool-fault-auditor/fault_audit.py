"""Independent deterministic fault-injection mechanism; not paper reproduction."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

FAULTS = {"clean", "timeout", "missing_tool", "schema_drift", "silent_corruption"}


@dataclass(frozen=True)
class ToolResult:
    value: Any = None
    error: str | None = None
    fault_fired: bool = False


def corrupt_value(value: Any) -> Any:
    """Independently declared synthetic corruption, not an author parameter."""
    if isinstance(value, bool):
        return not value
    if isinstance(value, (int, float)):
        return value + 1
    if isinstance(value, str):
        return value + "!"
    if isinstance(value, list) and value:
        return [corrupt_value(value[0]), *value[1:]]
    if isinstance(value, dict) and value:
        first = next(iter(value))
        return {key: corrupt_value(item) if key == first else item for key, item in value.items()}
    raise ValueError("unsupported corruption shape; refuse silent mutation")


class FaultInjector:
    """Fire at most once on the first eligible call; loud faults do not execute."""

    def __init__(self, kind: str, first_step: int, target_tool: str | None = None):
        if kind not in FAULTS or first_step < 1:
            raise ValueError("invalid fault plan")
        self.kind = kind
        self.first_step = first_step
        self.target_tool = target_tool
        self.fired = False

    def call(self, step: int, tool: str, execute: Callable[[], Any]) -> ToolResult:
        eligible = (
            self.kind != "clean"
            and not self.fired
            and step >= self.first_step
            and (self.target_tool is None or tool == self.target_tool)
        )
        if not eligible:
            return ToolResult(value=execute())
        if self.kind == "silent_corruption":
            real = execute()
            altered = corrupt_value(real)
            self.fired = True
            return ToolResult(value=altered, fault_fired=True)
        self.fired = True
        return ToolResult(error=self.kind, fault_fired=True)


def state_agreement(observed: dict[str, Any], reference: dict[str, Any]) -> float:
    if not reference:
        raise ValueError("empty reference state")
    return sum(observed.get(key, object()) == value for key, value in reference.items()) / len(
        reference
    )


def repeated_calls(actions: list[tuple[str, Any]]) -> dict[str, bool]:
    same_tool = any(
        actions[i][0] == actions[i + 1][0] == actions[i + 2][0]
        for i in range(len(actions) - 2)
    )
    identical = any(
        actions[i] == actions[i + 1] == actions[i + 2]
        for i in range(len(actions) - 2)
    )
    return {"same_tool_three": same_tool, "identical_three": identical}


def synthetic_trial(kind: str, policy: str) -> dict[str, Any]:
    """Counter fixture with clean end state 3; policies are scripted, not LLMs."""
    if policy not in {"no_retry", "error_retry", "invariant_check"}:
        raise ValueError("invalid scripted policy")
    state = {"count": 0}
    injector = FaultInjector(kind, first_step=2, target_tool="increment")
    detected = False
    calls = 0
    for _ in range(3):
        calls += 1

        def execute() -> dict[str, int]:
            state["count"] += 1
            return {"count": state["count"]}

        result = injector.call(calls, "increment", execute)
        if result.error is not None:
            detected = True
            if policy != "no_retry":
                calls += 1
                result = injector.call(calls, "increment", execute)
        elif policy == "invariant_check" and result.value != {"count": state["count"]}:
            detected = True
    return {
        "fault": kind,
        "policy": policy,
        "fired": injector.fired,
        "detected": detected if kind != "clean" else None,
        "recovered": state_agreement(state, {"count": 3}) == 1.0,
        "end_state": dict(state),
        "calls": calls,
    }


def run_synthetic() -> dict[str, Any]:
    policies = ("no_retry", "error_retry", "invariant_check")
    trials = [synthetic_trial(fault, policy) for fault in sorted(FAULTS) for policy in policies]
    loud = {"timeout", "missing_tool", "schema_drift"}
    return {
        "protocol": "independent-synthetic-fault-mechanism-v1",
        "kind": "synthetic_mechanism_test_not_paper_benchmark",
        "trials": trials,
        "total": len(trials),
        "fired": sum(bool(row["fired"]) for row in trials),
        "loud_detected": sum(row["detected"] is True for row in trials if row["fault"] in loud),
        "loud_total": sum(row["fault"] in loud for row in trials),
        "quiet_detected": sum(
            row["detected"] is True for row in trials if row["fault"] == "silent_corruption"
        ),
        "quiet_total": sum(row["fault"] == "silent_corruption" for row in trials),
        "recovered": sum(row["recovered"] for row in trials),
    }
