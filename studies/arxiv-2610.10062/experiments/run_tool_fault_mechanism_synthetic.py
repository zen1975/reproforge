"""Independent synthetic verification of arXiv:2610.10062 fault and metric semantics."""
from __future__ import annotations
from copy import deepcopy
import json

class ToyEnvironment:
    def __init__(self):
        self.state = {"balance": 10, "log": []}
    def call(self, tool, args):
        if tool == "add":
            amount = args["amount"]
            self.state["balance"] += amount
            self.state["log"].append(["add", amount])
            return {"ok": True, "value": self.state["balance"]}
        if tool == "read":
            return {"ok": True, "value": self.state["balance"]}
        raise KeyError(tool)

class FaultInjector:
    def __init__(self, kind, target_step=2):
        self.kind = kind
        self.target_step = target_step
        self.fired = False
    def call(self, env, tool, args, step):
        if self.kind == "clean" or self.fired or step < self.target_step:
            return env.call(tool, args), None
        self.fired = True
        if self.kind == "timeout":
            return {"error": "timeout"}, {"visibility": "loud"}
        if self.kind == "missing_tool":
            return {"error": f"tool unavailable: {tool}"}, {"visibility": "loud"}
        if self.kind == "schema_drift":
            return {"error": "unknown argument: amount"}, {"visibility": "loud"}
        if self.kind == "silent_corruption":
            before = deepcopy(env.state)
            real = env.call(tool, args)
            after = deepcopy(env.state)
            corrupted = deepcopy(real)
            corrupted["value"] += 7
            return corrupted, {"visibility": "quiet", "before": before, "after": after, "real": real}
        raise ValueError(self.kind)

def same_shape_types(a, b):
    if type(a) is not type(b):
        return False
    if isinstance(a, dict):
        return list(a.keys()) == list(b.keys()) and all(same_shape_types(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return len(a) == len(b) and all(same_shape_types(x, y) for x, y in zip(a, b))
    return type(a) is type(b)

def replanned(failed_action, next_action):
    return failed_action["tool"] != next_action["tool"] or failed_action["args"] != next_action["args"]

def repeated_same_tool(actions, threshold=3):
    run = 0
    previous = None
    for action in actions:
        tool = action["tool"]
        run = run + 1 if tool == previous else 1
        previous = tool
        if run >= threshold:
            return True
    return False

def state_agreement(actual, reference):
    keys = list(reference.keys())
    return 1.0 if not keys else sum(actual.get(k) == reference[k] for k in keys) / len(keys)

def run():
    fault_rows = []
    for kind in ["clean", "timeout", "missing_tool", "schema_drift", "silent_corruption"]:
        env = ToyEnvironment()
        injector = FaultInjector(kind, target_step=2)
        fire_count = 0
        quiet_checks = None
        for step in (1, 2, 3):
            output, meta = injector.call(env, "add", {"amount": 1}, step)
            if meta is not None:
                fire_count += 1
            if kind == "silent_corruption" and step == 2:
                quiet_checks = {
                    "shape_type_preserved": same_shape_types(output, meta["real"]),
                    "payload_changed": output != meta["real"],
                    "state_matches_successful_call": env.state == meta["after"] and env.state != meta["before"],
                }
        fault_rows.append({"fault": kind, "fire_count": fire_count, "final_state": env.state, "quiet_checks": quiet_checks})
    metric_checks = {
        "replan_tool_change": replanned({"tool":"add","args":{"amount":1}}, {"tool":"read","args":{}}),
        "replan_arg_change": replanned({"tool":"add","args":{"amount":1}}, {"tool":"add","args":{"amount":2}}),
        "no_replan_same_action": not replanned({"tool":"add","args":{"amount":1}}, {"tool":"add","args":{"amount":1}}),
        "repetition_three_same": repeated_same_tool([{"tool":"add"},{"tool":"add"},{"tool":"add"}]),
        "no_repetition_two_same": not repeated_same_tool([{"tool":"add"},{"tool":"add"},{"tool":"read"}]),
        "agreement_exact": state_agreement({"x":1,"y":2}, {"x":1,"y":2}) == 1.0,
        "agreement_partial": state_agreement({"x":1,"y":9}, {"x":1,"y":2}) == 0.5,
    }
    all_pass = (
        all(row["fire_count"] == (0 if row["fault"] == "clean" else 1) for row in fault_rows)
        and all(metric_checks.values())
        and all(row["quiet_checks"] is None or all(row["quiet_checks"].values()) for row in fault_rows)
    )
    return {
        "experiment_id": "tool-fault-mechanism-synthetic-v1",
        "fault_rows": fault_rows,
        "metric_checks": metric_checks,
        "all_pass": all_pass,
        "boundary": "Synthetic mechanism/protocol verification only; does not reproduce model behavioral rates.",
    }

if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
