"""Offline end-to-end checks of the v2 runner loop, aggregation, paired analysis and verifier (no keys)."""
import copy
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

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
arms = _load("jev_v2_arms")
run = _load("jev_v2_run")
an = _load("jev_v2_analysis")
ver = _load("verify_jev_v2_evidence")


class Oracle:
    def choose(self, state, instructions, criteria, oracle=None):
        if oracle["on_path"] is None:
            return core.v1.make_decision("goal_met" if oracle["goal_met"] else "goal_not_met", valid=True,
                                         usage={"input_tokens": 100, "output_tokens": 2}, latency_s=0.2)
        on = sorted(oracle["on_path"])
        return core.v1.make_decision(on[0] if on else "abstain", valid=True,
                                     usage={"input_tokens": 100, "output_tokens": 2}, latency_s=0.2)


class FirstListed:
    """Position-biased selector: always the first candidate; honest verification."""

    def choose(self, state, instructions, criteria, oracle=None):
        if oracle["on_path"] is None:
            return core.v1.make_decision("goal_met" if oracle["goal_met"] else "goal_not_met", valid=True,
                                         usage={"input_tokens": 300, "output_tokens": 5}, latency_s=0.9)
        return core.v1.make_decision(next(iter(criteria)), valid=True,
                                     usage={"input_tokens": 300, "output_tokens": 5}, latency_s=0.9)


def evidence(arm, selector, phase="pilot"):
    rows, status = run.run_phase(selector, arm, run.instances_for(phase), run.PRICING[arm])
    ident = {"resolved_model": an.RESOLVED[arm]}
    if arm == "jev":
        ident |= {"pinned_probe": {"headers": {}}, "alias_probe": {"headers": {}}}
    return run.build_evidence(arm, phase, rows, status, ident, 0.01)


def pair():
    return evidence("jev", Oracle()), evidence("control", FirstListed())


def test_run_phase_produces_expected_row_grid_with_both_episode_types():
    ev = evidence("jev", Oracle())
    assert ev["status"] == "COMPLETED" and len(ev["rows"]) == ev["expected_rows"] == run.expected_rows("pilot")
    assert {r["episode_type"] for r in ev["rows"]} == {"natural", "forced_trap"}
    assert {r["order_idx"] for r in ev["rows"]} == {0, 1, 2}
    agg = ev["aggregate"]
    assert agg["natural"]["success_rate"] == 1.0 and agg["natural"]["initial_error_rate"] == 0.0
    assert agg["forced_trap_recoverable_primary_c5"]["success_rate"] == 1.0
    assert agg["forced_trap_irreversible_negative_control"]["success_rate"] == 0.0
    assert agg["difficulty_window"]["initial_error_rate"] == 0.0


def test_position_biased_arm_shows_order_effect_in_the_same_fixture():
    ev = evidence("control", FirstListed())
    by = ev["aggregate"]["by_order_natural"]
    # order 0 = trap first (position-biased selector falls for it), order 1 = truth first (it is right)
    assert by["0"]["initial_choice_correct_rate"] == 0.0 and by["1"]["initial_choice_correct_rate"] == 1.0


def test_arm_evidence_verifies_and_rejects_tampering():
    jev, ctrl = pair()
    assert an.verify_arm(jev) == [] and an.verify_arm(ctrl) == []
    bad = copy.deepcopy(jev)
    bad["rows"][0]["final_success"] = not bad["rows"][0]["final_success"]
    assert an.verify_arm(bad)
    bad = copy.deepcopy(jev)
    bad["rows"].pop()
    assert an.verify_arm(bad)
    bad = copy.deepcopy(ctrl)
    bad["identity"]["resolved_model"] = "something-else"
    assert an.verify_arm(bad)
    bad = copy.deepcopy(ctrl)
    bad["note"] = "x-api-key: abcdef123456"
    assert an.verify_arm(bad)
    bad = copy.deepcopy(jev)
    bad["rows"][1]["truth_pos"] += 1
    assert an.verify_arm(bad)


class CapAfter:
    """Raises SpendCapReached after n selector calls (simulates the runner-enforced spend cap)."""

    def __init__(self, n):
        self.n, self.inner = n, Oracle()

    def choose(self, *a, **kw):
        if self.n <= 0:
            raise arms.SpendCapReached("cap")
        self.n -= 1
        return self.inner.choose(*a, **kw)


def test_incomplete_evidence_is_kept_but_flagged_and_not_analyzable():
    rows, status = run.run_phase(CapAfter(10), "jev", run.instances_for("pilot"), run.PRICING["jev"])
    assert status == "INCOMPLETE_SPEND_CAP" and 0 < len(rows) < run.expected_rows("pilot")
    ev = run.build_evidence("jev", "pilot", rows, status, {"resolved_model": "jev-1.13.0",
                            "pinned_probe": {"headers": {}}, "alias_probe": {"headers": {}}}, 0.01)
    assert an.verify_arm(ev) == []  # partial rows are valid evidence of an incomplete run
    assert an.verify_analysis({}, ev, ev)  # but analysis refuses incomplete evidence


def test_paired_analysis_and_verification():
    jev, ctrl = pair()
    out = an.analyze(jev, ctrl)
    assert out["n_paired_units"] == len(jev["rows"])
    names = {c["name"]: c for c in out["contrasts"]}
    d = names["decision_initial_correct__stress_natural"]
    assert d["jev"] == 1.0 and d["control"] < 1.0 and d["diff_control_minus_jev"] < 0
    lo, hi = d["ci95_cluster_bootstrap"]
    assert lo <= d["diff_control_minus_jev"] <= hi
    assert d["mcnemar"]["control_only"] == 0 and d["mcnemar"]["jev_only"] > 0
    assert d["mcnemar"]["p_exact_two_sided"] < 0.05
    tc = out["transfer_classification"]  # None when one arm has zero delivered successes (undefined)
    assert tc is None or tc["class_time"] in {"TRANSFERRED", "NO_LOCAL_SAVING", "DELIVERY_PARADOX",
                                              "OVERHEAD_ABSORPTION"}
    assert an.verify_analysis(json.loads(json.dumps(out)), jev, ctrl) == []
    tampered = json.loads(json.dumps(out))
    tampered["contrasts"][0]["diff_control_minus_jev"] += 0.1
    assert an.verify_analysis(tampered, jev, ctrl)
    assert an.analyze(jev, ctrl) == out  # bootstrap is seeded and deterministic


def test_verify_dir_not_run_then_verified_then_invalid(tmp_path):
    assert ver.verify_dir(tmp_path)["status"] == "NOT_RUN"
    jev, ctrl = pair()
    (tmp_path / "jev_v2_pilot2_jev.result.json").write_text(json.dumps(jev))
    (tmp_path / "jev_v2_pilot2_control.result.json").write_text(json.dumps(ctrl))
    (tmp_path / "jev_v2_pilot2_analysis.json").write_text(json.dumps(an.analyze(jev, ctrl)))
    assert ver.verify_dir(tmp_path)["status"] == "EVIDENCE_VERIFIED"
    jev["rows"][0]["cost_usd"] += 1
    (tmp_path / "jev_v2_pilot2_jev.result.json").write_text(json.dumps(jev))
    assert ver.verify_dir(tmp_path)["status"] == "EVIDENCE_INVALID"


def test_cli_skips_without_key_and_refuses_test_phase_before_freeze(tmp_path):
    env = {k: v for k, v in os.environ.items() if k not in ("TYPESAFE_API_KEY", "ANTHROPIC_API_KEY")}
    out = tmp_path / "x.json"
    p = subprocess.run([sys.executable, str(EXP / "jev_v2_run.py"), "--arm", "jev", "--phase", "pilot", "--out",
                        str(out)], check=False, env=env, capture_output=True, text=True)
    assert p.returncode == 0 and json.loads(p.stdout)["status"] == "SKIPPED_NO_CREDENTIAL" and not out.exists()
    env2 = dict(env, TYPESAFE_API_KEY="fake-key-not-used")
    p = subprocess.run([sys.executable, str(EXP / "jev_v2_run.py"), "--arm", "jev", "--phase", "test", "--out",
                        str(out)], check=False, env=env2, capture_output=True, text=True)
    assert p.returncode == 4 and not out.exists()
    assert run.FREEZE_SHA256 is None


def test_no_secret_literals_and_freeze_hash_is_stable():
    assert run.freeze_sha256() == run.freeze_sha256()
    for f in ("jev_v2_core.py", "jev_v2_generator.py", "jev_v2_arms.py", "jev_v2_run.py", "jev_v2_analysis.py"):
        text = (EXP / f).read_text()
        assert "sk-ant" not in text and "Bearer " not in text.replace('"Bearer', "")


class SlowOracle(Oracle):
    def choose(self, *a, **kw):
        d = super().choose(*a, **kw)
        d["latency_s"] = 0.9
        return d


def test_transfer_classification_defined_when_both_arms_deliver():
    jev, ctrl = evidence("jev", Oracle()), evidence("control", SlowOracle())
    tc = an.analyze(jev, ctrl)["transfer_classification"]
    assert tc["jev_vs_control_pct"]["decision_latency"] < -50  # Jev decisions are faster in this scripted setup
    assert tc["class_time"] in {"TRANSFERRED", "NO_LOCAL_SAVING", "DELIVERY_PARADOX", "OVERHEAD_ABSORPTION"}
