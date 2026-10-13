"""Workflow core for jev-live-systemone-check-v2 (design: ../design/jev-live-systemone-check-v2.md).

A superset of the frozen v1 machine (kept untouched): hidden state keys, custom prerequisite
messages, irreversible actions, system-log/distractor rendering and candidate rotation.
Stdlib only. Truth always comes from the BFS oracle over the machine, never from a model.
"""
from __future__ import annotations

import importlib.util
import time
from collections import deque
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("jev_v1_runner", HERE / "run_jev_live_systemone_check.py")
v1 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(v1)  # reuse apply_effect, goal_met, make_decision, cost_usd, aggregate_test_c

SHARED_ACTIONS = {
    "undo_last_action": "Revert the most recent state-changing action (not possible after an irreversible action).",
    "declare_done": "Declare the goal complete and end the workflow (completion is then verified).",
}
ABSTAIN = "abstain"
ABSTAIN_DESC = "No candidate is applicable, or the information given is insufficient to choose."
ACTION_INSTRUCTIONS = (
    "You are the action selector in a software workflow. Choose the single best next action toward the "
    "stated goal given the current state. Respect prerequisites: an action whose prerequisites are not met "
    "will fail. Choose 'abstain' only if no candidate action is applicable or the information given is "
    "insufficient."
)
VERIFICATION_INSTRUCTIONS = (
    "Based only on the current state, are ALL conditions of the stated goal satisfied right now? "
    "Answer goal_met only if every condition holds; otherwise answer goal_not_met."
)
VERIFICATION_CRITERIA = {
    "goal_met": "Every condition of the goal is satisfied in the current state.",
    "goal_not_met": "At least one condition of the goal is not yet satisfied.",
}


def _freeze(state: dict) -> tuple:
    return tuple(sorted(state.items()))


def relevant_keys(wf: dict) -> frozenset:
    keys = set(wf["goal"])
    for spec in wf["actions"].values():
        keys |= set(spec["pre"])
    return frozenset(keys)


class MachineV2:
    def __init__(self, wf: dict):
        self.wf = wf
        self.state = dict(wf["initial"])
        self.history: list[dict] = []
        self.log: list[str] = []
        self.last_result = "(no action yet)"

    def step_action(self, action: str) -> tuple[bool, str]:
        if action == "undo_last_action":
            if not self.history:
                return self._result(action, False, "ERROR: nothing to undo")
            self.state = self.history.pop()
            return self._result(action, True, "OK")
        spec = self.wf["actions"].get(action)
        if spec is None:
            return self._result(action, False, f"ERROR: unknown action {action}")
        for key, value in spec["pre"].items():
            if self.state.get(key) != value:
                msg = spec.get("pre_text") or f"{action} requires {key}={value} (currently {self.state.get(key)})"
                return self._result(action, False, f"ERROR: {msg}")
        self.history.append(dict(self.state))
        self.state = v1.apply_effect(self.state, spec["eff"])
        if spec.get("irreversible"):
            self.history.clear()
        return self._result(action, True, "OK")

    def _result(self, action: str, valid: bool, message: str) -> tuple[bool, str]:
        self.last_result = f"{action} -> {message}"
        self.log.append(self.last_result)
        return valid, message

    def goal_met(self) -> bool:
        return v1.goal_met(self.state, self.wf["goal"])

    def render(self) -> str:
        hidden = set(self.wf.get("hidden", []))
        lines = [f"Goal: {self.wf['goal_text']}", "Current state:"]
        lines += [f"- {k}: {v}" for k, v in self.state.items() if k not in hidden]
        if self.wf.get("log_lines"):
            lines.append("System log:")
            lines += [f"  {x}" for x in self.wf["log_lines"]]
        lines.append(f"Last action result: {self.last_result}")
        if self.log:
            lines.append("Recent history: " + "; ".join(self.log[-4:]))
        return "\n".join(lines)


def distance_to_goal(wf: dict, state: dict, history: list[dict], max_depth: int = 9) -> int | None:
    """BFS over relevant-key projection (irrelevant actions never help). Honors irreversible actions."""
    rel = relevant_keys(wf)

    def proj(s: dict) -> tuple:
        return tuple(sorted((k, v) for k, v in s.items() if k in rel))

    start_state = dict(state)
    if v1.goal_met(start_state, wf["goal"]):
        return 0
    useful = {n: sp for n, sp in wf["actions"].items() if set(sp["eff"]) & rel}
    start = (proj(start_state), tuple(proj(h) for h in history))
    seen = {start}
    queue = deque([(start, dict(state), 0)])
    while queue:
        (_, hist), cur, depth = queue.popleft()
        if depth >= max_depth:
            continue
        for name, spec in useful.items():
            if any(cur.get(k) != v for k, v in spec["pre"].items()):
                continue
            nxt = v1.apply_effect(cur, spec["eff"])
            new_hist = () if spec.get("irreversible") else hist + (proj(cur),)
            if v1.goal_met(nxt, wf["goal"]):
                return depth + 1
            node = (proj(nxt), new_hist)
            if node not in seen:
                seen.add(node)
                queue.append((node, nxt, depth + 1))
        if hist:  # undo: restores the projected relevant keys of the previous state
            prev = dict(hist[-1])
            restored = {**cur, **prev}
            node = (proj(restored), hist[:-1])
            if v1.goal_met(restored, wf["goal"]):
                return depth + 1
            if node not in seen:
                seen.add(node)
                queue.append((node, restored, depth + 1))
    return None


def on_path_actions(wf: dict, machine: MachineV2) -> set[str]:
    if machine.goal_met():
        return {"declare_done"}
    here = distance_to_goal(wf, machine.state, machine.history)
    if here is None:
        return set()
    result: set[str] = set()
    for name in list(wf["actions"]) + ["undo_last_action"]:
        trial = MachineV2(wf)
        trial.state, trial.history = dict(machine.state), [dict(h) for h in machine.history]
        valid, _ = trial.step_action(name)
        if not valid:
            continue
        there = distance_to_goal(wf, trial.state, trial.history)
        if there is not None and there == here - 1:
            result.add(name)
    return result


def truth_at_start(wf: dict) -> str:
    on = sorted(on_path_actions(wf, MachineV2(wf)))
    return on[0]


def candidate_order(wf: dict, order_idx: int) -> list[str]:
    """Three fixed position conditions over [instance actions + shared actions] (abstain stays last):
    0 = trap first, 1 = step-0 truth first, 2 = neither truth nor trap first. Rest keeps base order."""
    names = list(wf["actions"]) + list(SHARED_ACTIONS)
    truth, trap = truth_at_start(wf), wf["trap"]
    if order_idx == 0:
        front = trap
    elif order_idx == 1:
        front = truth
    else:
        front = next(n for n in names if n not in (truth, trap))
    return [front] + [n for n in names if n != front]


def build_criteria(wf: dict, order_idx: int) -> dict:
    desc = {n: s["description"] for n, s in wf["actions"].items()}
    desc.update(SHARED_ACTIONS)
    crit = {n: desc[n] for n in candidate_order(wf, order_idx)}
    crit[ABSTAIN] = ABSTAIN_DESC
    return crit


def run_episode_v2(wf: dict, selector, order_idx: int, pricing: dict, arm: str, extra_steps: int = 3,
                   forced_first: bool = False) -> dict:
    """forced_first=True is a forced-error recovery probe: step 0 is the instance's trap action, chosen by
    the harness (no selector call), so every arm continues from the identical error state."""
    machine = MachineV2(wf)
    start_distance = distance_to_goal(wf, machine.state, machine.history)
    budget = (start_distance or 0) + 1 + extra_steps
    criteria = build_criteria(wf, order_idx)
    order_list = list(criteria)
    truth0 = truth_at_start(wf)
    t0 = time.perf_counter()
    steps, calls = [], []
    initial_correct = None
    violations = deviations = invalid = verif_calls = verif_wrong = 0
    recovery_attempted = premature = infra = done_ok = False
    for step_no in range(budget):
        on_path_set = on_path_actions(wf, machine)
        if forced_first and step_no == 0:
            d = v1.make_decision(wf["trap"], valid=True)  # harness-forced error: not a selector decision
        else:
            d = selector.choose(machine.render(), ACTION_INSTRUCTIONS, criteria,
                                oracle={"on_path": on_path_set, "goal_met": machine.goal_met()})
            calls.append(d)
        choice = d["choice"]
        on_path = bool(choice) and choice in on_path_set
        if step_no == 0 and not forced_first:
            initial_correct = on_path
        rec = {"step": step_no, "choice": choice, "valid_response": d["valid"], "on_path": on_path, "outcome": None}
        stop = False
        if not d["valid"]:
            invalid += 1
            rec["outcome"] = "invalid_response"
            if d["infra"]:
                infra, stop = True, True
        elif choice == ABSTAIN:
            rec["outcome"] = "abstain"
        elif choice == "declare_done":
            met = machine.goal_met()
            vd = selector.choose(machine.render(), VERIFICATION_INSTRUCTIONS, VERIFICATION_CRITERIA,
                                 oracle={"on_path": None, "goal_met": met})
            calls.append(vd)
            verif_calls += 1
            if not (vd["valid"] and vd["choice"] == ("goal_met" if met else "goal_not_met")):
                verif_wrong += 1
            if vd["infra"]:
                infra, stop = True, True
            if vd["valid"] and vd["choice"] == "goal_met":
                rec["outcome"] = "done_accepted"
                stop = True
                if met:
                    done_ok = True
                else:
                    premature = True
            else:
                rec["outcome"] = "done_rejected_by_verification" if vd["valid"] else "verification_invalid"
        else:
            valid, _ = machine.step_action(choice)
            rec["outcome"] = "ok" if valid else "prerequisite_violation"
            violations += 0 if valid else 1
        if not on_path:
            deviations += 1
        elif deviations > 0:
            recovery_attempted = True
        steps.append(rec)
        if stop:
            break
    wall = time.perf_counter() - t0
    success = bool(done_ok and machine.goal_met())
    usage = {"input_tokens": sum(c["usage"].get("input_tokens", 0) for c in calls),
             "output_tokens": sum(c["usage"].get("output_tokens", 0) for c in calls)}
    return {
        "arm": arm, "episode_type": "forced_trap" if forced_first else "natural",
        "workflow_id": wf["id"], "family": wf["family"], "order_idx": order_idx,
        "truth_pos": order_list.index(truth0), "trap_pos": order_list.index(wf["trap"]),
        "start_distance": start_distance, "step_budget": budget,
        "initial_choice_correct": initial_correct,
        "prerequisite_valid": violations == 0, "prerequisite_violations": violations,
        "deviation_events": deviations, "recovery_attempted": recovery_attempted,
        "recovery_success": bool(deviations > 0 and success), "premature_completion": premature,
        "verification_calls": verif_calls, "verification_wrong": verif_wrong,
        "invalid_responses": invalid, "infrastructure_failure": infra, "final_success": success,
        "number_of_steps": len(steps), "n_selector_calls": len(calls),
        "decision_latency_total_s": sum(c["latency_s"] for c in calls if c["valid"]),
        "retry_wait_total_s": sum(c["retry_wait_s"] for c in calls),
        "workflow_latency_total_s": wall, "usage": usage, "cost_usd": v1.cost_usd(usage, pricing),
        "models": sorted({c["model"] for c in calls if c["model"]}), "steps": steps,
    }
