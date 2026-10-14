"""Offline checks for jev-live-systemone-check-v3a (B arm, runner, three-arm analysis, verifier). No keys, no network."""
import copy
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "studies" / "arxiv-2610.13092" / "experiments"
sys.path.insert(0, str(EXP))


def _load(name):
    spec = importlib.util.spec_from_file_location(name, EXP / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


core = _load("jev_v2_core")
gen = _load("jev_v2_generator")
v2arms = _load("jev_v2_arms")
v2run = _load("jev_v2_run")
v2an = _load("jev_v2_analysis")
arms = _load("jev_v3_arms")
run = _load("jev_v3_run")
an = _load("jev_v3_analysis")
ver = _load("verify_jev_v3_evidence")
CRIT = {"zeta": "Z thing.", "alpha": "A thing.", "abstain": "None."}


def text_resp(text, inp=500, out=60):
    return SimpleNamespace(content=[SimpleNamespace(type="text", text=text)], model="claude-haiku-5-5",
                           usage=SimpleNamespace(input_tokens=inp, output_tokens=out), stop_reason="end_turn",
                           _request_id="req_b")


class FakeClient:
    def __init__(self, script):
        self.script, self.calls = list(script), []
        self.messages = SimpleNamespace(create=self._create)

    def _create(self, **kw):
        self.calls.append(kw)
        item = self.script.pop(0) if self.script else text_resp("ok\nACTION: alpha")
        if isinstance(item, Exception):
            raise item
        return item


# ---------------------------------------------------------------- parser
def test_parse_action_table():
    allowed = ["alpha", "beta_2"]
    p = arms.parse_action
    assert p("reason\nACTION: alpha", allowed) == "alpha"
    assert p("ACTION: `beta_2`.", allowed) == "beta_2"
    assert p("I think ACTION: alpha is wrong\nACTION: beta_2", allowed) == "beta_2"  # last line wins
    assert p("ACTION: alpha\nACTION: nonsense", allowed) is None  # last line is out of set
    assert p("ACTION: alpha beta_2", allowed) is None  # multiple tokens never match
    assert p("ACTION: Alpha", allowed) is None  # exact, case-sensitive
    assert p("no action line", allowed) is None and p("", allowed) is None and p(None, allowed) is None
    assert p("action: alpha", allowed) == "alpha"  # label is case-insensitive, command is not


# ---------------------------------------------------------------- request
def test_b_request_has_descriptions_alphabetical_no_abstain_no_tools_and_no_sampling():
    req = arms.build_b_request("STATE", "INSTR", CRIT)
    text = req["messages"][0]["content"]
    assert text.index("- alpha: A thing.") < text.index("- zeta: Z thing.")
    assert "abstain" not in text.split("Command reference:")[1]
    assert not {"tools", "tool_choice", "temperature", "top_p", "top_k", "thinking"} & set(req)
    assert req["model"] == "claude-haiku-5-5" and req["max_tokens"] == arms.B_MAX_TOKENS


def test_b_prompt_is_independent_of_candidate_order_and_oracle_never_leaks():
    wf = gen.gen_indirection(4000)
    prompts = []
    for o in (0, 1, 2):
        crit = core.build_criteria(wf, o)
        prompts.append(arms.build_b_request(core.MachineV2(wf).render(), core.ACTION_INSTRUCTIONS, crit))
    assert prompts[0] == prompts[1] == prompts[2]  # B rows over order_idx are replicates, same prompt
    client = FakeClient([])
    arms.BArm(client).choose("s", "i", CRIT, oracle={"on_path": {"alpha"}, "goal_met": True})
    assert "on_path" not in json.dumps(client.calls[0]) and "alpha" in client.calls[0]["messages"][0]["content"]


# ---------------------------------------------------------------- arm behaviour
def test_b_valid_decision_cost_and_usage():
    guard = v2arms.SpendGuard(1.0, arms.B_PRICING)
    d = arms.BArm(FakeClient([text_resp("think\nACTION: zeta", 1000, 100)]), guard).choose("s", "i", CRIT)
    assert d["valid"] and d["choice"] == "zeta" and d["model"] == "claude-haiku-5-5" and d["infra"] is False
    assert d["usage"] == {"input_tokens": 1000, "output_tokens": 100}
    assert abs(guard.spent - (1000 * 0.10 + 100 * 0.50) / 1e6) < 1e-12


def test_b_unparsable_output_is_invalid_not_infra_and_abstain_is_not_offered():
    d = arms.BArm(FakeClient([text_resp("I cannot decide.")])).choose("s", "i", CRIT)
    assert d["valid"] is False and d["infra"] is False and d["choice"] is None
    d2 = arms.BArm(FakeClient([text_resp("ACTION: abstain")])).choose("s", "i", CRIT)
    assert d2["valid"] is False  # B has no abstain token


def test_b_retries_then_infra_failure_like_the_control():
    class Err(Exception):
        status_code = 529
    slept = []
    d = arms.BArm(FakeClient([Err(), text_resp("ACTION: alpha")]), sleep=slept.append).choose("s", "i", CRIT)
    assert d["valid"] and d["retries"] == 1 and slept == [1]

    class Bad(Exception):
        status_code = 401
    d2 = arms.BArm(FakeClient([Bad()]), sleep=lambda s: None).choose("s", "i", CRIT)
    assert d2["infra"] is True and d2["valid"] is False


def test_b_spend_cap_raises():
    guard = v2arms.SpendGuard(0.00001, arms.B_PRICING)
    try:
        arms.BArm(FakeClient([text_resp("ACTION: alpha", 1000, 0)]), guard).choose("s", "i", CRIT)
    except v2arms.SpendCapReached:
        return
    raise AssertionError("expected SpendCapReached")


def test_invalid_b_response_consumes_a_step_without_state_change_in_a_real_episode():
    wf = gen.gen_anchor(4000)
    seq = []

    class Scripted(FakeClient):
        def _create(self, **kw):
            self.calls.append(kw)
            if not seq:
                seq.append(1)
                return text_resp("hmm")  # invalid first reply
            names = [ln[2:].split(":")[0] for ln in kw["messages"][0]["content"].split("Command reference:\n")[1].splitlines()]
            on = sorted(core.on_path_actions(wf, state_ref[0]))
            return text_resp(f"ACTION: {on[0] if on else names[0]}")

    state_ref = [None]
    client = Scripted([])
    selector = arms.BArm(client)

    class Spy:
        def choose(self, state, instructions, criteria, oracle=None):
            return selector.choose(state, instructions, criteria, oracle)
    machine_probe = core.MachineV2(wf)
    state_ref[0] = machine_probe
    row = core.run_episode_v2(wf, Spy(), 0, arms.B_PRICING, "b")
    assert row["steps"][0]["outcome"] == "invalid_response" and row["invalid_responses"] >= 1
    assert row["initial_choice_correct"] is False and row["steps"][0]["choice"] is None


# ---------------------------------------------------------------- seeds, pins, runner
def test_seeds_are_disjoint_from_every_earlier_run_and_the_v2_pin_is_intact():
    new = set(run.PILOT_SEEDS) | set(run.TEST_SEEDS)
    assert not new & (set(gen.PILOT_SEEDS) | set(gen.TEST_SEEDS) | set(range(1000, 1004)))
    assert not set(run.PILOT_SEEDS) & set(run.TEST_SEEDS)
    assert run.v2_pin_intact(), "v3a imports v2 files read-only; the v2 freeze pin must still verify"
    pilot_ids = {w["id"] for w in run.instances_for("pilot")}
    test_ids = {w["id"] for w in run.instances_for("test")}
    v2_ids = {w["id"] for w in v2run.instances_for("test")} | {w["id"] for w in v2run.instances_for("pilot")}
    assert not pilot_ids & test_ids and not (pilot_ids | test_ids) & v2_ids


def test_runner_skips_without_key_and_refuses_test_when_the_pin_does_not_match(tmp_path, monkeypatch):
    env = {k: v for k, v in os.environ.items() if k not in ("TYPESAFE_API_KEY", "ANTHROPIC_API_KEY")}
    out = tmp_path / "x.json"
    r = subprocess.run([sys.executable, str(EXP / "jev_v3_run.py"), "--arm", "b", "--phase", "test", "--out", str(out)],
                       check=False, env=env, capture_output=True, text=True)
    assert r.returncode == 0 and "SKIPPED_NO_CREDENTIAL" in r.stdout and not out.exists()
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-not-a-real-key")
    monkeypatch.setattr(run, "FREEZE_SHA256", "0" * 64)  # a wrong pin must refuse before any client is built
    assert run.main(["--arm", "b", "--phase", "test", "--out", str(out)]) == 4 and not out.exists()


def test_pinned_v3a_freeze_hash_matches_the_frozen_files():
    pin = json.loads((EXP / "jev_v3a_freeze.json").read_text())
    assert pin["freeze_sha256"] == run.freeze_sha256() == run.FREEZE_SHA256
    assert pin["files"] == list(run.FREEZE_FILES) and pin["v2_freeze_sha256"] == v2run.FREEZE_SHA256
    assert run.v2_pin_intact()


# ---------------------------------------------------------------- end to end (scripted selectors)
class Oracle:
    def choose(self, state, instructions, criteria, oracle=None):
        if oracle["on_path"] is None:
            return core.v1.make_decision("goal_met" if oracle["goal_met"] else "goal_not_met", valid=True,
                                         usage={"input_tokens": 100, "output_tokens": 2}, latency_s=0.2)
        on = sorted(oracle["on_path"])
        return core.v1.make_decision(on[0] if on else "abstain", valid=True,
                                     usage={"input_tokens": 100, "output_tokens": 2}, latency_s=0.2)


class FirstListed:
    def choose(self, state, instructions, criteria, oracle=None):
        if oracle["on_path"] is None:
            return core.v1.make_decision("goal_met" if oracle["goal_met"] else "goal_not_met", valid=True,
                                         usage={"input_tokens": 300, "output_tokens": 5}, latency_s=0.9)
        return core.v1.make_decision(next(iter(criteria)), valid=True,
                                     usage={"input_tokens": 300, "output_tokens": 5}, latency_s=0.9)


class InvalidFirst:
    """B stand-in: unparsable first reply, then on-path; long outputs (rationale)."""

    def choose(self, state, instructions, criteria, oracle=None):
        if oracle["on_path"] is None:
            return core.v1.make_decision("goal_met" if oracle["goal_met"] else "goal_not_met", valid=True,
                                         usage={"input_tokens": 500, "output_tokens": 60}, latency_s=2.0)
        if "(no action yet)" in state:
            return core.v1.make_decision(None, valid=False, usage={"input_tokens": 500, "output_tokens": 60},
                                         latency_s=2.0, error="no_parsable_action")
        on = sorted(oracle["on_path"])
        return core.v1.make_decision(on[0] if on else "abstain", valid=True,
                                     usage={"input_tokens": 500, "output_tokens": 60}, latency_s=2.0)


def evidence(arm, selector, phase="pilot"):
    rows, status = v2run.run_phase(selector, arm, run.instances_for(phase), run.PRICING[arm])
    ident = {"resolved_model": run.RESOLVED[arm]}
    if arm == "jev":
        ident |= {"pinned_probe": {"headers": {}}, "alias_probe": {"headers": {}}}
    return run.build_evidence(arm, phase, rows, status, ident, 0.01, run.ARM_CAP_USD[arm])


def triple():
    return {"jev": evidence("jev", Oracle()), "control": evidence("control", FirstListed()),
            "b": evidence("b", InvalidFirst())}


def test_row_grid_matches_three_orders_times_two_episode_types_for_every_arm():
    evs = triple()
    for ev in evs.values():
        assert ev["status"] == "COMPLETED" and len(ev["rows"]) == ev["expected_rows"] == run.expected_rows("pilot")
    assert evs["b"]["aggregate"]["natural"]["initial_error_rate"] == 1.0  # invalid first reply = initial error
    assert evs["b"]["aggregate"]["natural"]["invalid_responses"] > 0
    assert evs["jev"]["aggregate"]["natural"]["initial_error_rate"] == 0.0


def test_analysis_has_three_pairings_arm_summary_and_clean_verification():
    evs = triple()
    for ev in evs.values():
        assert an.verify_arm(ev) == []
    out = an.analyze(evs)
    assert set(out["pairings"]) == {"C_vs_J", "C_vs_B", "J_vs_B"}
    c = {x["name"]: x for x in out["pairings"]["C_vs_B"]["contrasts"]}
    prim = c["C_vs_B:" + an.V2_PRIMARY]
    assert "diff_C_minus_B" in prim and {"C_only", "B_only"} <= set(prim["mcnemar"])
    assert out["arm_summary"]["B"]["output_tokens_per_call"] > out["arm_summary"]["J"]["output_tokens_per_call"]
    assert out["pairings"]["C_vs_J"]["n_paired_units"] == run.expected_rows("pilot")
    assert an.verify_analysis(out, evs) == []
    assert set(out["transfer_classification"]) == {"J_vs_B", "C_vs_B", "J_vs_C", "note"}


def test_replication_block_reads_the_pinned_v2_result():
    rep = an.replication(an.analyze(triple())["pairings"]["C_vs_J"])
    assert abs(rep["v2_diff_control_minus_jev"] - 0.1006944) < 1e-4 and rep["v2_ci95"][0] > 0
    assert isinstance(rep["replicated"], bool)


def test_verifier_detects_tampering():
    evs = triple()
    bad = copy.deepcopy(evs["b"])
    bad["rows"][0]["final_success"] = not bad["rows"][0]["final_success"]
    assert any("aggregate does not match rows" in e for e in an.verify_arm(bad))
    bad = copy.deepcopy(evs["jev"])
    bad["identity"]["resolved_model"] = "something-else"
    assert an.verify_arm(bad)
    bad = copy.deepcopy(evs["control"])
    bad["rows"].append(copy.deepcopy(bad["rows"][0]))
    assert any("duplicate row" in e for e in an.verify_arm(bad))
    bad = copy.deepcopy(evs["b"])
    bad["identity"]["note"] = "Authorization: Bearer abcdefghijklmnop"
    assert any("credential-like" in e for e in an.verify_arm(bad))
    out = an.analyze(evs)
    out["pairings"]["C_vs_J"]["contrasts"][0]["C"] = 0.123
    assert an.verify_analysis(out, evs)


def test_test_evidence_requires_the_pin():
    ev = evidence("jev", Oracle(), phase="test")
    assert an.verify_arm(ev) == []
    ev["freeze_sha256"] = "0" * 64
    assert any("pinned v3a freeze hash" in e for e in an.verify_arm(ev))


def test_committed_v3a_evidence_if_any_is_valid():
    assert ver.an.verify_dir()["status"] in ("NOT_RUN", "EVIDENCE_VERIFIED")
