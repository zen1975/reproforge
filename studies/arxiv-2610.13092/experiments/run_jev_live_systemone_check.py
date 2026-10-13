"""Live Jev System One check for arXiv:2610.13092 (experiment jev-live-systemone-check-v1).

Calls the real TypeSafe Jev API (POST /v1/systemone) on a frozen candidate-choice fixture
(Test B) and inside a small deterministic workflow state machine (Test C), and records
identity (Test A). No generic LLM is used. Without TYPESAFE_API_KEY the runner prints a
SKIPPED_NO_CREDENTIAL status and exits 0 without producing evidence.

The API key is read only from the environment and is never written to any output.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import statistics
import sys
import time
import urllib.error
import urllib.request
from collections import deque
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIXTURE_PATH = HERE / "jev_live_systemone_check_v1.fixture.json"
# sha256 of the raw fixture bytes. Changing the fixture after the first live run => v2.
FIXTURE_SHA256 = "7883f4ff7f09a3e20483a5d6a323e500e6cafb5224b2d09a319335d8bcaf3a06"
EXPERIMENT_ID = "jev-live-systemone-check-v1"
DROPPED_HEADERS = {"set-cookie", "authorization", "proxy-authorization"}

CLAIM_SCOPE = (
    "Actual Jev (TypeSafe System One) live protocol check on a small frozen fixture. "
    "Not an ALFWorld/AndroidWorld reproduction, not a reproduction of the paper's effect sizes, "
    "and not paper-level reproduction. Descriptive only; no causal or generalization claim."
)


# --------------------------------------------------------------------------- fixture
def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_fixture(path: Path = FIXTURE_PATH, expected_sha: str | None = FIXTURE_SHA256) -> dict:
    raw = path.read_bytes()
    digest = sha256_bytes(raw)
    if expected_sha is not None and digest != expected_sha:
        raise SystemExit(
            f"FIXTURE_HASH_MISMATCH: {digest} != pinned {expected_sha}. "
            "The frozen fixture must not change after the first live run; create v2 instead."
        )
    fixture = json.loads(raw)
    fixture["_sha256"] = digest
    return fixture


# --------------------------------------------------------------------------- state machine
def apply_effect(state: dict, eff: dict) -> dict:
    new = dict(state)
    for key, value in eff.items():
        if value == "@flip":
            new[key] = "off" if state.get(key) == "on" else "on"
        else:
            new[key] = value
    return new


def goal_met(state: dict, goal: dict) -> bool:
    return all(state.get(k) == v for k, v in goal.items())


class Machine:
    """Deterministic workflow machine. History stack supports undo_last_action."""

    def __init__(self, workflow: dict):
        self.wf = workflow
        self.state = dict(workflow["initial"])
        self.history: list[dict] = []
        self.log: list[str] = []
        self.last_result = "(no action yet)"

    def step_action(self, action: str) -> tuple[bool, str]:
        """Apply an explicit action. Returns (valid, message). Invalid => state unchanged."""
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
                return self._result(
                    action, False,
                    f"ERROR: {action} requires {key}={value} (currently {self.state.get(key)})",
                )
        self.history.append(dict(self.state))
        self.state = apply_effect(self.state, spec["eff"])
        return self._result(action, True, "OK")

    def _result(self, action: str, valid: bool, message: str) -> tuple[bool, str]:
        self.last_result = f"{action} -> {message}"
        self.log.append(self.last_result)
        return valid, message

    def goal_met(self) -> bool:
        return goal_met(self.state, self.wf["goal"])

    def render(self) -> str:
        lines = [f"Goal: {self.wf['goal_text']}", "Current state:"]
        lines += [f"- {k}: {v}" for k, v in self.state.items()]
        lines.append(f"Last action result: {self.last_result}")
        if self.log:
            lines.append("Recent history: " + "; ".join(self.log[-4:]))
        return "\n".join(lines)


def _freeze(state: dict) -> tuple:
    return tuple(sorted(state.items()))


def distance_to_goal(wf: dict, state: dict, history: list[dict], max_depth: int = 8) -> int | None:
    """BFS over explicit actions plus undo (history-aware). None if unreachable in max_depth."""
    start = (_freeze(state), tuple(_freeze(h) for h in history))
    if goal_met(state, wf["goal"]):
        return 0
    seen = {start}
    queue = deque([(start, 0)])
    while queue:
        (st, hist), depth = queue.popleft()
        if depth >= max_depth:
            continue
        cur = dict(st)
        for name, spec in wf["actions"].items():
            if any(cur.get(k) != v for k, v in spec["pre"].items()):
                continue
            nxt = apply_effect(cur, spec["eff"])
            node = (_freeze(nxt), hist + (st,))
            if node in seen:
                continue
            if goal_met(nxt, wf["goal"]):
                return depth + 1
            seen.add(node)
            queue.append((node, depth + 1))
        if hist:
            prev = hist[-1]
            node = (prev, hist[:-1])
            if node not in seen:
                if goal_met(dict(prev), wf["goal"]):
                    return depth + 1
                seen.add(node)
                queue.append((node, depth + 1))
    return None


def on_path_actions(wf: dict, machine: Machine) -> set[str]:
    """Actions that are valid now and strictly reduce the BFS distance to the goal.
    declare_done is on-path iff the goal is met. 'abstain' is never on-path."""
    if machine.goal_met():
        return {"declare_done"}
    here = distance_to_goal(wf, machine.state, machine.history)
    result: set[str] = set()
    if here is None:
        return result
    probe_names = list(wf["actions"]) + ["undo_last_action"]
    for name in probe_names:
        trial = Machine(wf)
        trial.state = dict(machine.state)
        trial.history = [dict(h) for h in machine.history]
        valid, _ = trial.step_action(name)
        if not valid:
            continue
        there = distance_to_goal(wf, trial.state, trial.history)
        if there is not None and there == here - 1:
            result.add(name)
    return result


# --------------------------------------------------------------------------- decision records
def make_decision(choice, *, valid, probabilities=None, confidence=None, latency_s=0.0,
                  usage=None, model=None, retries=0, retry_wait_s=0.0, error=None, infra=False):
    usage = usage or {"input_tokens": 0, "output_tokens": 0}
    return {
        "choice": choice, "valid": valid, "probabilities": probabilities,
        "confidence": confidence, "latency_s": latency_s, "usage": usage,
        "model": model, "retries": retries, "retry_wait_s": retry_wait_s, "error": error,
        "infra": infra,
    }


def cost_usd(usage: dict, pricing: dict) -> float:
    return (
        usage.get("input_tokens", 0) * pricing["usd_per_million_input_tokens"]
        + usage.get("output_tokens", 0) * pricing["usd_per_million_output_tokens"]
    ) / 1_000_000


# --------------------------------------------------------------------------- live client
class ApiFailure(Exception):
    def __init__(self, status, detail):
        super().__init__(f"HTTP {status}")
        self.status = status
        self.detail = detail


class JevClient:
    """Minimal stdlib client. Own retry policy so 429/529 backoff is logged separately
    from decision latency (latency_s = last, successful HTTP round trip only)."""

    def __init__(self, api_cfg: dict, key: str, sleep=time.sleep):
        self.cfg = api_cfg
        self._key = key
        self._sleep = sleep

    def _request(self, method: str, path: str, body: dict | None):
        data = None if body is None else json.dumps(body).encode()
        headers = {"Authorization": f"Bearer {self._key}", "Accept": "application/json"}
        if data is not None:
            headers["Content-Type"] = "application/json"
        retries, waited = 0, 0.0
        while True:
            req = urllib.request.Request(self.cfg["base_url"] + path, data=data, headers=headers, method=method)
            t0 = time.perf_counter()
            try:
                with urllib.request.urlopen(req, timeout=self.cfg["timeout_seconds"]) as resp:
                    payload = resp.read()
                    latency = time.perf_counter() - t0
                    hdrs = {k.lower(): v for k, v in resp.headers.items() if k.lower() not in DROPPED_HEADERS}
                    return {
                        "status": resp.status, "headers": hdrs, "json": json.loads(payload),
                        "latency_s": latency, "retries": retries, "retry_wait_s": waited,
                    }
            except urllib.error.HTTPError as err:
                detail = err.read()[:2000].decode("utf-8", "replace")
                if err.code in self.cfg["retry_statuses"] and retries < self.cfg["max_retries"]:
                    wait = self.cfg["backoff_seconds"][retries]
                    ra = err.headers.get("retry-after")
                    if ra and ra.isdigit():
                        wait = max(wait, int(ra))
                    self._sleep(wait)
                    retries += 1
                    waited += wait
                    continue
                raise ApiFailure(err.code, detail) from None
            except (urllib.error.URLError, TimeoutError) as err:
                if retries < self.cfg["max_retries"]:
                    wait = self.cfg["backoff_seconds"][retries]
                    self._sleep(wait)
                    retries += 1
                    waited += wait
                    continue
                raise ApiFailure("connection", str(err)[:500]) from None

    def list_models(self):
        return self._request("GET", self.cfg["models_path"], None)

    def ask_choice(self, model: str, state: str, instructions: str, criteria: dict, name: str = "q"):
        body = {
            "model": model, "state": state,
            "questions": {name: {"type": "choice", "instructions": instructions, "criteria": criteria}},
        }
        try:
            r = self._request("POST", self.cfg["systemone_path"], body)
        except ApiFailure as err:
            return make_decision(None, valid=False, infra=True, error=f"{err.status}: {err.detail}"[:500])
        ans = (r["json"].get("answers") or {}).get(name) or {}
        choice = ans.get("choice")
        valid = ans.get("type") == "choice" and choice in criteria
        return make_decision(
            choice if valid else None, valid=valid,
            probabilities=ans.get("probabilities"), confidence=ans.get("confidence"),
            latency_s=r["latency_s"], usage=r["json"].get("usage"), model=r["json"].get("model"),
            retries=r["retries"], retry_wait_s=r["retry_wait_s"],
            error=None if valid else "unparseable_or_out_of_set_choice",
        )


class LiveSelector:
    def __init__(self, client: JevClient, model: str):
        self.client, self.model = client, model

    def choose(self, state: str, instructions: str, criteria: dict, oracle=None):
        # `oracle` is never sent to the API; it exists only for non-model reference policies.
        return self.client.ask_choice(self.model, state, instructions, criteria)


# --------------------------------------------------------------------------- Test B
def candidate_criteria(candidates: dict, abstain_desc: str, abstain_name: str) -> dict:
    crit = dict(candidates)
    crit[abstain_name] = abstain_desc
    return crit


def run_test_b(fixture: dict, selector, repeats: int) -> list[dict]:
    prompts, abstain = fixture["prompts"], fixture["design"]["abstain_option"]
    rows = []
    for case in fixture["test_b_cases"]:
        crit = candidate_criteria(case["candidates"], prompts["abstain_description"], abstain)
        for rep in range(repeats):
            d = selector.choose(case["state"], prompts["action_instructions"], crit)
            rows.append({
                "case_id": case["id"], "category": case["category"], "repeat": rep,
                "truth": case["truth"], "choice": d["choice"], "valid": d["valid"],
                "abstained": d["choice"] == abstain, "correct": d["choice"] == case["truth"],
                "confidence": d["confidence"], "probabilities": d["probabilities"],
                "latency_s": d["latency_s"], "retries": d["retries"], "retry_wait_s": d["retry_wait_s"],
                "usage": d["usage"], "model": d["model"], "error": d["error"],
            })
    return rows


# --------------------------------------------------------------------------- Test C
def run_episode(fixture: dict, wf: dict, selector, repeat: int) -> dict:
    prompts, design = fixture["prompts"], fixture["design"]
    abstain = design["abstain_option"]
    pricing = fixture["pricing"]
    machine = Machine(wf)
    start_distance = distance_to_goal(wf, machine.state, machine.history)
    budget = (start_distance or 0) + 1 + design["step_budget_extra"]
    criteria_base = {n: s["description"] for n, s in wf["actions"].items()}
    criteria_base.update(fixture["shared_actions"])
    criteria = candidate_criteria(criteria_base, prompts["abstain_description"], abstain)

    t_start = time.perf_counter()
    steps, calls = [], []
    initial_correct = None
    violations = deviations = invalid = verif_calls = verif_wrong = 0
    recovery_attempted = premature = infra_failure = done_accepted = False
    for step_no in range(budget):
        on_path_set = on_path_actions(wf, machine)
        d = selector.choose(machine.render(), prompts["action_instructions"], criteria,
                            oracle={"on_path": on_path_set, "goal_met": machine.goal_met()})
        calls.append(d)
        choice = d["choice"]
        on_path = bool(choice) and choice in on_path_set
        if step_no == 0:
            initial_correct = on_path
        record = {"step": step_no, "choice": choice, "valid_response": d["valid"],
                  "on_path": on_path, "outcome": None}
        stop = False
        if not d["valid"]:
            invalid += 1
            record["outcome"] = "invalid_response"
            if d["infra"]:
                infra_failure = True
                stop = True
        elif choice == abstain:
            record["outcome"] = "abstain"
        elif choice == "declare_done":
            actually_met = machine.goal_met()
            vd = selector.choose(machine.render(), prompts["verification_instructions"],
                                 prompts["verification_criteria"],
                                 oracle={"on_path": None, "goal_met": actually_met})
            calls.append(vd)
            verif_calls += 1
            expected = "goal_met" if actually_met else "goal_not_met"
            if not (vd["valid"] and vd["choice"] == expected):
                verif_wrong += 1
            if vd["infra"]:
                infra_failure = True
                stop = True
            if vd["valid"] and vd["choice"] == "goal_met":
                record["outcome"] = "done_accepted"
                stop = True
                if actually_met:
                    done_accepted = True
                else:
                    premature = True
            else:
                record["outcome"] = "done_rejected_by_verification" if vd["valid"] else "verification_invalid"
        else:
            valid, _ = machine.step_action(choice)
            record["outcome"] = "ok" if valid else "prerequisite_violation"
            if not valid:
                violations += 1
        if not on_path:
            deviations += 1
        elif deviations > 0:
            recovery_attempted = True
        steps.append(record)
        if stop:
            break
    wall = time.perf_counter() - t_start

    final_success = bool(done_accepted and machine.goal_met())
    decision_latency = sum(c["latency_s"] for c in calls if c["valid"])
    retry_wait = sum(c["retry_wait_s"] for c in calls)
    total_usage = {
        "input_tokens": sum(c["usage"].get("input_tokens", 0) for c in calls),
        "output_tokens": sum(c["usage"].get("output_tokens", 0) for c in calls),
    }
    return {
        "workflow_id": wf["id"], "category": wf["category"], "repeat": repeat,
        "start_distance": start_distance, "step_budget": budget,
        "initial_choice_correct": initial_correct,
        "prerequisite_valid": violations == 0,
        "prerequisite_violations": violations,
        "deviation_events": deviations,
        "recovery_attempted": recovery_attempted,
        "recovery_success": bool(deviations > 0 and final_success),
        "premature_completion": premature,
        "verification_calls": verif_calls, "verification_wrong": verif_wrong,
        "invalid_responses": invalid, "infrastructure_failure": infra_failure,
        "final_success": final_success,
        "number_of_steps": len(steps), "jev_calls": len(calls),
        "jev_decision_latency_total_s": decision_latency,
        "retry_wait_total_s": retry_wait,
        "workflow_latency_total_s": wall,
        "usage": total_usage, "jev_cost_usd": cost_usd(total_usage, pricing),
        "models": sorted({c["model"] for c in calls if c["model"]}),
        "steps": steps,
    }


def run_test_c(fixture: dict, selector, repeats: int) -> list[dict]:
    rows = []
    for wf in fixture["test_c_workflows"]:
        for rep in range(repeats):
            rows.append(run_episode(fixture, wf, selector, rep))
    return rows


# --------------------------------------------------------------------------- aggregation
def _rate(num, den):
    return None if den == 0 else num / den


def _quantiles(values):
    if not values:
        return {"mean": None, "p50": None, "p95": None, "max": None}
    vs = sorted(values)
    p95 = vs[min(len(vs) - 1, int(round(0.95 * (len(vs) - 1))))]
    return {"mean": statistics.fmean(vs), "p50": statistics.median(vs), "p95": p95, "max": vs[-1]}


def aggregate_test_b(rows: list[dict], pricing: dict) -> dict:
    n = len(rows)
    by_cat = {}
    for cat in sorted({r["category"] for r in rows}):
        sub = [r for r in rows if r["category"] == cat]
        by_cat[cat] = {"n": len(sub), "exact_accuracy": _rate(sum(r["correct"] for r in sub), len(sub)),
                       "valid_choice_rate": _rate(sum(r["valid"] for r in sub), len(sub)),
                       "abstain_rate": _rate(sum(r["abstained"] for r in sub), len(sub))}
    usage = {"input_tokens": sum(r["usage"].get("input_tokens", 0) for r in rows),
             "output_tokens": sum(r["usage"].get("output_tokens", 0) for r in rows)}
    return {
        "n_decisions": n,
        "valid_choice_rate": _rate(sum(r["valid"] for r in rows), n),
        "invalid_or_unparseable": sum(not r["valid"] for r in rows),
        "exact_choice_accuracy": _rate(sum(r["correct"] for r in rows), n),
        "abstain_rate": _rate(sum(r["abstained"] for r in rows), n),
        "decision_latency_s": _quantiles([r["latency_s"] for r in rows if r["valid"]]),
        "retry_events": sum(r["retries"] for r in rows),
        "usage": usage, "decision_cost_usd_total": cost_usd(usage, pricing),
        "decision_cost_usd_mean": _rate(cost_usd(usage, pricing), n),
        "by_category": by_cat,
    }


def aggregate_test_c(rows: list[dict]) -> dict:
    n = len(rows)
    succ = [r for r in rows if r["final_success"]]
    total_cost = sum(r["jev_cost_usd"] for r in rows)
    total_decision_latency = sum(r["jev_decision_latency_total_s"] for r in rows)
    total_wall = sum(r["workflow_latency_total_s"] for r in rows)
    total_retry_wait = sum(r["retry_wait_total_s"] for r in rows)
    init_ok = [r for r in rows if r["initial_choice_correct"]]
    init_bad = [r for r in rows if r["initial_choice_correct"] is False]
    dev = [r for r in rows if r["deviation_events"] > 0]
    return {
        "n_attempts": n,
        "initial_choice_correct_rate": _rate(len(init_ok), n),
        "prerequisite_valid_rate": _rate(sum(r["prerequisite_valid"] for r in rows), n),
        "deviation_attempts": len(dev),
        "recovery_attempted_among_deviations": _rate(sum(r["recovery_attempted"] for r in dev), len(dev)),
        "recovery_success_among_deviations": _rate(sum(r["recovery_success"] for r in dev), len(dev)),
        "premature_completion_count": sum(r["premature_completion"] for r in rows),
        "verification_wrong_count": sum(r["verification_wrong"] for r in rows),
        "infrastructure_failures": sum(r["infrastructure_failure"] for r in rows),
        "final_success_count": len(succ),
        "success_rate": _rate(len(succ), n),
        "initial_correct_but_final_failed": sum(not r["final_success"] for r in init_ok),
        "initial_wrong_but_final_success": sum(r["final_success"] for r in init_bad),
        "mean_steps": _rate(sum(r["number_of_steps"] for r in rows), n),
        "decision_latency_total_s": total_decision_latency,
        "decision_latency_per_attempt_s": _rate(total_decision_latency, n),
        "decision_cost_total_usd": total_cost,
        "decision_cost_per_attempt_usd": _rate(total_cost, n),
        "task_latency_total_s": total_wall,
        "task_latency_per_attempt_s": _rate(total_wall, n),
        "retry_wait_total_s_excluded_from_decision_latency": total_retry_wait,
        "task_cost_total_usd": total_cost,
        "task_cost_per_attempt_usd": _rate(total_cost, n),
        "cost_per_delivered_success_usd": _rate(total_cost, len(succ)),
        "time_per_delivered_success_s": _rate(total_wall, len(succ)),
        "boundary": "task cost counts Jev tokens only; the local state machine has no environment or auxiliary-LLM cost, so decision cost == task cost here.",
    }


# --------------------------------------------------------------------------- reference policies (non-model)
class ReferenceSelector:
    """Non-model deterministic reference policies for the workflow machine (never labelled Jev).
    They may read the oracle context; the live selector never does."""

    def __init__(self, name: str):
        if name not in ("oracle_on_path", "first_candidate", "declare_done_immediately"):
            raise ValueError(name)
        self.name = name

    def choose(self, state, instructions, criteria, oracle=None):
        if oracle["on_path"] is None:  # completion-verification question: answer truthfully
            return make_decision("goal_met" if oracle["goal_met"] else "goal_not_met", valid=True)
        if self.name == "oracle_on_path":
            on_path = sorted(oracle["on_path"])
            return make_decision(on_path[0] if on_path else next(iter(criteria)), valid=True)
        if self.name == "first_candidate":
            return make_decision(next(iter(criteria)), valid=True)
        return make_decision("declare_done", valid=True)


def run_reference_policies(fixture: dict, repeats: int = 1) -> dict:
    out = {}
    for name in ("oracle_on_path", "first_candidate", "declare_done_immediately"):
        rows = run_test_c(fixture, ReferenceSelector(name), repeats)
        out[name] = {"aggregate": aggregate_test_c(rows),
                     "note": "Non-model deterministic reference; latency and cost are zero by construction."}
    return out


# --------------------------------------------------------------------------- main
def classify(identity: dict, b_agg: dict, c_agg: dict, fixture: dict) -> dict:
    min_valid = fixture["design"]["protocol_pass_min_valid_choice_rate"]
    checks = {
        "identity_resolved_matches_pinned": identity.get("resolved_model") == fixture["api"]["pinned_model"],
        "valid_choice_rate_ok": (b_agg["valid_choice_rate"] or 0) >= min_valid,
        "no_infrastructure_failures": c_agg["infrastructure_failures"] == 0,
    }
    status = "LIVE_CHECK_PASS" if all(checks.values()) else "LIVE_CHECK_PARTIAL"
    return {"protocol_status": status, "protocol_checks": checks,
            "note": "Protocol status judges that the live check executed validly. It is not a quality verdict on Jev."}


def test_a_identity(client: JevClient, fixture: dict) -> dict:
    api = fixture["api"]
    identity = {
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "endpoint": api["base_url"] + api["systemone_path"],
        "requested_model": api["pinned_model"], "requested_alias": api["alias_probe"],
    }
    try:
        m = client.list_models()
        identity["models_list"] = {"http_status": m["status"], "body": m["json"], "headers": m["headers"]}
    except ApiFailure as err:
        identity["models_list"] = {"error": f"{err.status}: {err.detail}"[:500]}
    probe_q = {"is_ready": {"type": "choice", "instructions": "Is the system ready?",
                            "criteria": {"yes": "Ready.", "no": "Not ready."}}}
    for label, model in (("pinned", api["pinned_model"]), ("alias", api["alias_probe"])):
        body = {"model": model, "state": "The system finished booting and all checks passed.",
                "questions": probe_q}
        try:
            r = client._request("POST", api["systemone_path"], body)
            identity[f"{label}_probe"] = {
                "http_status": r["status"], "resolved_model": r["json"].get("model"),
                "usage": r["json"].get("usage"), "latency_s": r["latency_s"],
                "headers": r["headers"], "response_keys": sorted(r["json"].keys()),
            }
        except ApiFailure as err:
            identity[f"{label}_probe"] = {"error": f"{err.status}: {err.detail}"[:500]}
    identity["resolved_model"] = (identity.get("pinned_probe") or {}).get("resolved_model")
    identity["alias_resolved_model"] = (identity.get("alias_probe") or {}).get("resolved_model")
    return identity


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", help="write result JSON to this path (only when a live run happens)")
    args = ap.parse_args(argv)
    fixture = load_fixture()
    key = os.environ.get(fixture["api"]["api_key_env"], "").strip()
    if not key:
        print(json.dumps({
            "experiment_id": EXPERIMENT_ID, "status": "SKIPPED_NO_CREDENTIAL",
            "detail": f"{fixture['api']['api_key_env']} is not set; no API call was made and no evidence was produced.",
            "fixture_sha256": fixture["_sha256"],
        }, indent=2, sort_keys=True))
        return 0
    client = JevClient(fixture["api"], key)
    identity = test_a_identity(client, fixture)
    selector = LiveSelector(client, fixture["api"]["pinned_model"])
    repeats = fixture["design"]["repeats"]
    b_rows = run_test_b(fixture, selector, repeats)
    c_rows = run_test_c(fixture, selector, repeats)
    b_agg = aggregate_test_b(b_rows, fixture["pricing"])
    c_agg = aggregate_test_c(c_rows)
    result = {
        "experiment_id": EXPERIMENT_ID, "status": "LIVE_RUN_COMPLETED",
        "fixture_sha256": fixture["_sha256"],
        "runner_sha256": sha256_bytes(Path(__file__).read_bytes()),
        "git_sha": os.environ.get("GITHUB_SHA"), "github_run_id": os.environ.get("GITHUB_RUN_ID"),
        "test_a_identity": identity,
        "test_b": {"aggregate": b_agg, "rows": b_rows},
        "test_c": {"aggregate": c_agg, "rows": c_rows},
        "reference_policies_non_model": run_reference_policies(fixture),
        "control": {"status": "NOT_RUN", "reason": "No LLM candidate-interface control in v1; B-vs-C / C-vs-J separation is not tested here."},
        "classification": classify(identity, b_agg, c_agg, fixture),
        "claim_scope": CLAIM_SCOPE,
    }
    text = json.dumps(result, indent=2, sort_keys=True)
    if key in text:
        print("ABORT: credential value found in output; refusing to emit.", file=sys.stderr)
        return 2
    if args.out:
        Path(args.out).write_text(text + "\n")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
