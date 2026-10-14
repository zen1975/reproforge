"""Offline checks for jev-live-systemone-check-v3b (auxiliary stage, runner, analysis, verifier). No keys, no network."""
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
v3arms = _load("jev_v3_arms")
v3run = _load("jev_v3_run")
v3an = _load("jev_v3_analysis")
cm = _load("jev_closure_metrics")
aux = _load("jev_v3b_arms")
run = _load("jev_v3b_run")
an = _load("jev_v3b_analysis")
ver = _load("verify_jev_v3b_evidence")


def text_resp(text, inp=300, out=40):
    return SimpleNamespace(content=[SimpleNamespace(type="text", text=text)], model="claude-haiku-5-5",
                           usage=SimpleNamespace(input_tokens=inp, output_tokens=out), stop_reason="end_turn")


class FakeAux:
    def __init__(self, script=()):
        self.script, self.calls = list(script), []
        self.messages = SimpleNamespace(create=self._create)

    def _create(self, **kw):
        self.calls.append(kw)
        item = self.script.pop(0) if self.script else text_resp("Goal not met yet.")
        if isinstance(item, Exception):
            raise item
        return item


class Recorder:
    """Selector that records what it was shown and picks the oracle's first on-path action."""

    def __init__(self):
        self.seen = []

    def choose(self, state, instructions, criteria, oracle=None):
        self.seen.append((state, set(criteria)))
        if oracle["on_path"] is None:
            return core.v1.make_decision("goal_met" if oracle["goal_met"] else "goal_not_met", valid=True,
                                         usage={"input_tokens": 100, "output_tokens": 2}, latency_s=0.2)
        on = sorted(oracle["on_path"])
        return core.v1.make_decision(on[0] if on else "abstain", valid=True,
                                     usage={"input_tokens": 100, "output_tokens": 2}, latency_s=0.2)


# ---------------------------------------------------------------- auxiliary stage
def test_aux_request_sees_only_the_state_and_never_the_oracle():
    req = aux.build_aux_request("STATE")
    text = req["messages"][0]["content"]
    assert text.startswith("STATE") and "recommend" in text and req["max_tokens"] == 150
    assert not {"tools", "tool_choice", "temperature", "top_p", "top_k", "thinking"} & set(req)


def test_note_is_appended_for_action_decisions_only_and_accounting_is_separate():
    sel, client = Recorder(), FakeAux([text_resp("Note A.", 300, 40)])
    w = aux.AuxWrapped(sel, client, v2arms.SpendGuard(1.0, aux.AUX_PRICING))
    crit = {"a": "A.", "abstain": "None."}
    d = w.choose("S", "I", crit, oracle={"on_path": {"a"}, "goal_met": False})
    assert sel.seen[0][0] == f"S\n\n{aux.NOTE_HEADER}\nNote A." and d["usage"] == {"input_tokens": 100, "output_tokens": 2}
    w.choose("S2", "V", core.VERIFICATION_CRITERIA, oracle={"on_path": None, "goal_met": True})
    assert sel.seen[1][0] == "S2" and len(client.calls) == 1  # verification: raw state, no aux call
    acc = w.drain()
    assert acc["aux_calls"] == 1 and acc["aux_usage"] == {"input_tokens": 300, "output_tokens": 40}
    assert abs(acc["aux_cost_usd"] - (300 * 0.10 + 40 * 0.50) / 1e6) < 1e-12
    assert w.drain()["aux_calls"] == 0  # drain resets


def test_aux_failure_is_an_infrastructure_failure_and_the_selector_is_not_called():
    class Bad(Exception):
        status_code = 401
    sel = Recorder()
    d = aux.AuxWrapped(sel, FakeAux([Bad()]), sleep=lambda s: None).choose(
        "S", "I", {"a": "A."}, oracle={"on_path": {"a"}, "goal_met": False})
    assert d["infra"] is True and d["valid"] is False and sel.seen == []


def test_aux_retries_transient_errors_and_spend_cap_raises():
    class Busy(Exception):
        status_code = 529
    slept = []
    w = aux.AuxWrapped(Recorder(), FakeAux([Busy(), text_resp("ok")]), sleep=slept.append)
    w.choose("S", "I", {"a": "A."}, oracle={"on_path": {"a"}, "goal_met": False})
    assert slept == [1] and w.drain()["aux_calls"] == 1
    tiny = v2arms.SpendGuard(0.00001, aux.AUX_PRICING)
    try:
        aux.AuxWrapped(Recorder(), FakeAux([text_resp("x", 1000, 0)]), tiny).choose(
            "S", "I", {"a": "A."}, oracle={"on_path": {"a"}, "goal_met": False})
    except v2arms.SpendCapReached:
        return
    raise AssertionError("expected SpendCapReached")


# ---------------------------------------------------------------- runner
def test_grid_seeds_families_and_pins():
    insts = run.instances_for("test")
    assert len(insts) == 36 and {w["family"] for w in insts} == {"anchor", "injected", "indirection"}
    assert run.expected_rows("test") == 216 and not set(run.TEST_SEEDS) & run.USED_SEEDS
    assert run.pins_intact(), "v3b imports v2 and v3a read-only; their pins must still verify"


def test_runner_skips_without_keys_and_refuses_wrong_pin_and_smoke_into_evidence(tmp_path, monkeypatch):
    env = {k: v for k, v in os.environ.items() if k not in ("TYPESAFE_API_KEY", "ANTHROPIC_API_KEY")}
    r = subprocess.run([sys.executable, str(EXP / "jev_v3b_run.py"), "--arm", "jev", "--overhead", "O1", "--phase",
                        "test", "--out", str(tmp_path / "x.json")], check=False, env=env, capture_output=True, text=True)
    assert r.returncode == 0 and "SKIPPED_NO_CREDENTIAL" in r.stdout
    monkeypatch.setenv("TYPESAFE_API_KEY", "sk-test-1")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-2")
    monkeypatch.setattr(run, "FREEZE_SHA256", "0" * 64)
    assert run.main(["--arm", "jev", "--overhead", "O1", "--phase", "test", "--out", str(tmp_path / "y.json")]) == 4
    ev_dir = EXP.parent / "evidence" / "smoke_must_not_exist.json"
    assert run.main(["--arm", "b", "--overhead", "O0", "--phase", "smoke", "--out", str(ev_dir)]) == 6
    assert not ev_dir.exists()


def make_rows(arm, level, selector, aux_client=None, phase="test"):
    wrapper = aux.AuxWrapped(selector, aux_client) if level == "O1" else None
    rows, status = run.run_phase(selector, wrapper, arm, level, run.instances_for(phase), v3run.PRICING[arm])
    assert status == "COMPLETED"
    return rows


def evidence(arm, level, selector, aux_client=None):
    rows = make_rows(arm, level, selector, aux_client)
    ident = {"resolved_model": v3run.RESOLVED[arm]}
    if arm == "jev":
        ident |= {"pinned_probe": {"headers": {}}, "alias_probe": {"headers": {}}}
    if level == "O1":
        ident["aux_identity"] = {"resolved_model": aux.AUX_MODEL}
    return run.build_evidence(arm, level, "test", rows, "COMPLETED", ident, 0.01, 0.01 if level == "O1" else 0.0,
                              run.CELL_CAP_USD[arm])


class Slow(Recorder):
    """Selector with controllable latency/success so the transfer classes are predictable."""

    def __init__(self, lat, wrong_first=False):
        super().__init__()
        self.lat, self.wrong_first = lat, wrong_first

    def choose(self, state, instructions, criteria, oracle=None):
        d = super().choose(state, instructions, criteria, oracle)
        d["latency_s"] = self.lat
        if self.wrong_first and oracle["on_path"] is not None and "(no action yet)" in state:
            d["choice"] = next(n for n in criteria if n not in oracle["on_path"] and n != "abstain")
        return d


def all_cells(monkeypatch):
    monkeypatch.setattr(run, "FREEZE_SHA256", run.freeze_sha256())
    evs = {}
    for arm, lat in (("jev", 0.2), ("control", 1.4), ("b", 1.3)):
        for level in run.LEVELS:
            evs[(arm, level)] = evidence(arm, level, Slow(lat), FakeAux() if level == "O1" else None)
    return evs


def test_rows_carry_separate_aux_accounting_and_o0_has_none(monkeypatch):
    ev0, ev1 = evidence("jev", "O0", Slow(0.2)), evidence("jev", "O1", Slow(0.2), FakeAux())
    assert all(r["aux_calls"] == 0 and r["aux_cost_usd"] == 0 and r["overhead"] == "O0" for r in ev0["rows"])
    for r in ev1["rows"]:
        assert r["aux_calls"] == r["n_selector_calls"] - r["verification_calls"] and r["aux_calls"] >= 1
        assert r["aux_cost_usd"] > 0 and r["overhead"] == "O1"
    nat = next(r for r in ev1["rows"] if r["episode_type"] == "natural")
    forced = next(r for r in ev1["rows"] if r["episode_type"] == "forced_trap")
    assert forced["aux_calls"] == forced["n_selector_calls"] - forced["verification_calls"]  # no aux on the forced step
    assert nat["decision_latency_total_s"] == 0.2 * nat["n_selector_calls"]  # aux time not in decision latency


def test_verifier_accepts_clean_cells_and_detects_tampering(monkeypatch):
    evs = all_cells(monkeypatch)
    for ev in evs.values():
        assert an.verify_cell(ev) == []
    bad = copy.deepcopy(evs[("b", "O1")])
    bad["rows"][0]["aux_calls"] = 0
    assert any("aux calls fewer" in e for e in an.verify_cell(bad))
    bad = copy.deepcopy(evs[("jev", "O0")])
    bad["rows"][0]["aux_calls"] = 2
    assert any("aux fields set" in e for e in an.verify_cell(bad))
    bad = copy.deepcopy(evs[("control", "O1")])
    bad["identity"]["aux_identity"]["resolved_model"] = "other"
    assert any("aux model" in e for e in an.verify_cell(bad))
    bad = copy.deepcopy(evs[("control", "O0")])
    bad["freeze_sha256"] = "0" * 64
    assert any("pinned v3b freeze" in e for e in an.verify_cell(bad))
    bad = copy.deepcopy(evs[("b", "O0")])
    bad["rows"][1]["final_success"] = not bad["rows"][1]["final_success"]
    assert any("aggregate does not match rows" in e for e in an.verify_cell(bad))


def test_analysis_classifies_transfer_and_recomputes(monkeypatch):
    evs = all_cells(monkeypatch)
    out = an.analyze(evs)
    assert set(out["pairings"]) == {f"{p}@{o}" for p in ("C_vs_J", "C_vs_B", "J_vs_B") for o in run.LEVELS}
    assert set(out["transfer"]) == {f"{p}@{o}" for p in ("J_vs_C", "J_vs_B", "C_vs_B") for o in run.LEVELS}
    t = out["transfer"]["J_vs_C@O1"]
    # fake clients: wall clock is ~0 so the class itself is noise here; the rule is pinned in the next test
    assert t["time"]["class"] in {"TRANSFERRED", "OVERHEAD_ABSORPTION", "DELIVERY_PARADOX", "NO_LOCAL_SAVING"}
    assert t["cost"] is not None and t["new_success_natural"] == t["base_success_natural"]
    assert out["aux_effect"]["J"]["final_success__natural"]["n_pairs"] > 0
    assert out["cells"]["J@O1"]["overall"]["aux_cost_usd"] > 0
    assert an.verify_analysis(out, evs) == []
    out2 = copy.deepcopy(out)
    out2["transfer"]["J_vs_C@O1"]["time"]["class"] = "DELIVERY_PARADOX"
    assert an.verify_analysis(out2, evs)


def test_classification_rule_covers_absorption_and_delivery_paradox():
    def rows(lat, wall, ok_frac, aux_cost=0.0):
        r = []
        for i in range(10):
            r.append({"episode_type": "natural", "final_success": i < ok_frac * 10, "n_selector_calls": 2,
                      "decision_latency_total_s": lat * 2, "cost_usd": 0.001, "workflow_latency_total_s": wall,
                      "aux_cost_usd": aux_cost, "aux_latency_total_s": 0.0})
        return r
    base = rows(1.0, 4.0, 1.0)
    assert an.transfer(rows(0.2, 4.0, 1.0), base)["time"]["class"] == "OVERHEAD_ABSORPTION"  # task time unchanged
    assert an.transfer(rows(0.2, 3.0, 0.5), base)["time"]["class"] == "DELIVERY_PARADOX"     # 3.0/0.5 = 6.0 > 4.0
    assert an.transfer(rows(0.2, 3.0, 1.0), base)["time"]["class"] == "TRANSFERRED"
    assert an.transfer(rows(1.0, 4.0, 1.0), base)["time"]["class"] == "NO_LOCAL_SAVING"
    assert an.transfer(rows(0.2, 3.0, 0.0), base)["time"] is None  # no successes => undefined, not a class


def test_committed_v3b_evidence_if_any_is_valid():
    assert an.verify_dir()["status"] in ("NOT_RUN", "EVIDENCE_VERIFIED")


def test_pinned_v3b_freeze_hash_matches_the_frozen_files():
    pin = json.loads((EXP / "jev_v3b_freeze.json").read_text())
    assert pin["freeze_sha256"] == run.freeze_sha256() == run.FREEZE_SHA256
    assert pin["files"] == list(run.FREEZE_FILES)
    assert pin["v3a_freeze_sha256"] == v3run.FREEZE_SHA256 and pin["v2_freeze_sha256"] == v3run.v2run.FREEZE_SHA256
    assert run.pins_intact()
