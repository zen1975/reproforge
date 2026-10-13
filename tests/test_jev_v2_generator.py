"""Offline checks for the jev-live-systemone-check-v2 generator and core (no API, no keys)."""
import importlib.util
import sys
import time
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
PRICING = {"usd_per_million_input_tokens": 0.042, "usd_per_million_output_tokens": 0.0}


class Policy:
    """Scripted selector. `first` (if given) is chosen at step 0, then the oracle path is followed."""

    def __init__(self, first=None, verify=None):
        self.first, self.verify, self.n = first, verify, 0

    def choose(self, state, instructions, criteria, oracle=None):
        if oracle["on_path"] is None:
            ans = self.verify or ("goal_met" if oracle["goal_met"] else "goal_not_met")
            return core.v1.make_decision(ans, valid=True, usage={"input_tokens": 50, "output_tokens": 2})
        self.n += 1
        if self.n == 1 and self.first:
            choice = self.first
        else:
            on = sorted(oracle["on_path"])
            choice = on[0] if on else "abstain"
        return core.v1.make_decision(choice, valid=True, usage={"input_tokens": 50, "output_tokens": 2})


def test_counts_and_seed_disjointness():
    assert set(gen.PILOT_SEEDS).isdisjoint(gen.TEST_SEEDS)
    assert len(gen.generate(gen.TEST_SEEDS)) == 8 * 12
    assert len(gen.generate(gen.PILOT_SEEDS)) == 8 * 4
    assert set(gen.FAMILIES) == set(gen.GENERATORS)


def test_generation_is_deterministic_and_seed_sensitive():
    assert gen.generate(gen.TEST_SEEDS) == gen.generate(gen.TEST_SEEDS)
    a = gen.gen_indirection(2000)
    b = gen.gen_indirection(2002)
    assert a != b
    ids = [w["id"] for w in gen.generate(list(gen.TEST_SEEDS) + list(gen.PILOT_SEEDS))]
    assert len(ids) == len(set(ids))


def test_oracle_succeeds_on_every_instance_and_order_quickly():
    t0 = time.perf_counter()
    for wf in gen.generate(list(gen.PILOT_SEEDS) + list(gen.TEST_SEEDS)):
        for order in range(3):
            row = core.run_episode_v2(wf, Policy(), order, PRICING)
            assert row["final_success"], (wf["id"], order)
            assert row["initial_choice_correct"] is True
            assert row["deviation_events"] == 0
        assert 1 <= row["start_distance"] <= 6, wf["id"]
    assert time.perf_counter() - t0 < 60


def test_trap_is_off_path_at_start_for_every_instance():
    for wf in gen.generate(gen.TEST_SEEDS):
        m = core.MachineV2(wf)
        assert wf["trap"] in list(wf["actions"]) + ["declare_done"], wf["id"]
        assert wf["trap"] not in core.on_path_actions(wf, m), wf["id"]


def test_each_family_trap_produces_intended_failure_mode():
    for wf in gen.generate(gen.TEST_SEEDS):
        row = core.run_episode_v2(wf, Policy(first=wf["trap"]), 0, PRICING)
        fam = wf["family"]
        assert row["initial_choice_correct"] is False, wf["id"]
        assert row["deviation_events"] >= 1, wf["id"]
        if fam == "irreversible":
            assert row["final_success"] is False, wf["id"]  # unrecoverable by design
        else:
            assert row["final_success"] is True, wf["id"]  # recoverable by design
            assert row["recovery_attempted"] and row["recovery_success"], wf["id"]
    ind = next(w for w in gen.generate([2000], ["indirection"]))
    assert core.run_episode_v2(ind, Policy(first=ind["trap"]), 0, PRICING)["prerequisite_violations"] == 1


def test_premature_completion_only_with_dishonest_verifier():
    wf = gen.gen_premature(2000)
    honest = core.run_episode_v2(wf, Policy(first="declare_done"), 0, PRICING)
    assert honest["premature_completion"] is False and honest["final_success"] is True
    liar = core.run_episode_v2(wf, Policy(first="declare_done", verify="goal_met"), 0, PRICING)
    assert liar["premature_completion"] is True and liar["final_success"] is False


def test_irreversible_blocks_undo_and_goal():
    wf = gen.gen_irreversible(2000)
    m = core.MachineV2(wf)
    ok, _ = m.step_action(wf["trap"])
    assert ok and m.history == []
    ok, msg = m.step_action("undo_last_action")
    assert not ok and "nothing to undo" in msg
    assert core.distance_to_goal(wf, m.state, m.history) is None


def test_candidate_rotation_is_balanced_and_abstain_last():
    for wf in gen.generate(gen.PILOT_SEEDS):
        orders = [core.candidate_order(wf, i) for i in range(3)]
        assert all(sorted(o) == sorted(orders[0]) for o in orders)
        assert len({tuple(o) for o in orders}) == 3
        n = len(orders[0])
        firsts = {o[0] for o in orders}
        assert len(firsts) == 3 and n >= 4
        assert list(core.build_criteria(wf, 1))[-1] == core.ABSTAIN


def test_rendering_hides_hidden_keys_shows_distractors_and_no_oracle_text():
    num = gen.gen_numeric(2000)
    text = core.MachineV2(num).render()
    assert "lead_time_ok" not in text and "days_remaining" in text
    dis = gen.gen_distractors(2000)
    dtext = core.MachineV2(dis).render()
    assert dtext.count("noise_") >= 24 and "System log:" in dtext
    for wf in gen.generate(gen.PILOT_SEEDS):
        t = core.MachineV2(wf).render()
        assert "on_path" not in t and "trap" not in t and "oracle" not in t


def test_numeric_family_covers_both_sides_of_threshold():
    days = [int(gen.gen_numeric(s)["initial"]["days_remaining"]) for s in gen.TEST_SEEDS]
    assert any(d >= 7 for d in days) and any(d < 7 for d in days)


def test_v1_runner_and_fixture_untouched_by_v2_core_import():
    assert core.v1.FIXTURE_SHA256 == "7883f4ff7f09a3e20483a5d6a323e500e6cafb5224b2d09a319335d8bcaf3a06"
