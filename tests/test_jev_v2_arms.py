"""Offline checks for the v2 arms (fake clients only; no keys, no network)."""
import importlib.util
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
arms = _load("jev_v2_arms")
CRIT = {"alpha": "A.", "beta": "B.", "abstain": "None."}


def resp(choice, inp=120, out=9, rid="req_x"):
    block = SimpleNamespace(type="tool_use", name=arms.TOOL_NAME, input={"choice": choice})
    return SimpleNamespace(content=[block], usage=SimpleNamespace(input_tokens=inp, output_tokens=out),
                           model="claude-haiku-5-5", stop_reason="tool_use", _request_id=rid)


class FakeClient:
    def __init__(self, script):
        self.script, self.calls = list(script), []
        self.messages = SimpleNamespace(create=self._create)

    def _create(self, **kw):
        self.calls.append(kw)
        item = self.script.pop(0) if self.script else resp("alpha")
        if isinstance(item, Exception):
            raise item
        return item


class Err(Exception):
    def __init__(self, status):
        super().__init__(str(status))
        self.status_code = status


def test_request_is_pinned_forced_and_free_of_unsupported_sampling():
    req = arms.build_control_request("state text", "do it", CRIT)
    assert req["model"] == "claude-haiku-5-5"
    assert not {"temperature", "top_p", "top_k", "thinking"} & set(req)  # haiku-5-5 rejects non-default sampling
    assert req["tool_choice"] == {"type": "tool", "name": arms.TOOL_NAME}
    assert req["tools"][0]["input_schema"]["properties"]["choice"]["enum"] == list(CRIT)
    assert req["tools"][0]["strict"] is True and req["output_config"] == {"effort": "low"}
    text = req["messages"][0]["content"]
    assert text.index("- alpha") < text.index("- beta") < text.index("- abstain")  # same order Jev receives


def test_control_valid_decision_with_usage_cost_and_request_id():
    guard = arms.SpendGuard(1.0, arms.CONTROL_PRICING)
    arm = arms.ControlArm(FakeClient([resp("beta", 1000, 10)]), guard)
    d = arm.choose("s", "i", CRIT)
    assert d["valid"] and d["choice"] == "beta" and d["model"] == "claude-haiku-5-5"
    assert d["usage"] == {"input_tokens": 1000, "output_tokens": 10} and d["request_id"] == "req_x"
    assert abs(guard.spent - (1000 * 0.10 + 10 * 0.50) / 1e6) < 1e-12 and d["infra"] is False


def test_out_of_set_choice_is_invalid_not_infrastructure():
    d = arms.ControlArm(FakeClient([resp("gamma")])).choose("s", "i", CRIT)
    assert d["valid"] is False and d["infra"] is False and d["choice"] is None


def test_retryable_errors_back_off_and_are_logged_separately_from_latency():
    slept = []
    client = FakeClient([Err(429), Err(529), resp("alpha")])
    d = arms.ControlArm(client, sleep=slept.append).choose("s", "i", CRIT)
    assert d["valid"] and d["retries"] == 2 and d["retry_wait_s"] == 3 and slept == [1, 2]
    assert len(client.calls) == 3


def test_non_retryable_error_is_infra_failure_without_retry():
    client = FakeClient([Err(401)])
    d = arms.ControlArm(client, sleep=lambda s: None).choose("s", "i", CRIT)
    assert d["infra"] is True and d["valid"] is False and len(client.calls) == 1


def test_spend_cap_raises():
    guard = arms.SpendGuard(0.00001, arms.CONTROL_PRICING)
    arm = arms.ControlArm(FakeClient([resp("alpha", 1000, 0)]), guard)
    try:
        arm.choose("s", "i", CRIT)
    except arms.SpendCapReached:
        return
    raise AssertionError("expected SpendCapReached")


def test_control_runs_a_full_episode_and_never_carries_jev_labels():
    wf = gen.gen_anchor(2000)
    first_listed = []

    class FirstCandidate(FakeClient):
        def _create(self, **kw):
            self.calls.append(kw)
            names = kw["tools"][0]["input_schema"]["properties"]["choice"]["enum"]
            first_listed.append(names[0])
            return resp(names[0])

    row = core.run_episode_v2(wf, arms.ControlArm(FirstCandidate([])), 1, arms.CONTROL_PRICING, "control")
    assert row["arm"] == "control" and row["n_selector_calls"] >= 1
    assert not [k for k in row if k.startswith("jev_")]
    assert row["truth_pos"] == 0 and row["initial_choice_correct"] is True  # first-listed == truth in order 1
    assert first_listed[0] == core.truth_at_start(wf)


def test_forced_trap_probe_gives_control_and_jev_the_same_state_but_bills_only_selector_calls():
    wf = gen.gen_anchor(2000)
    client = FakeClient([])
    row = core.run_episode_v2(wf, arms.ControlArm(client), 0, arms.CONTROL_PRICING, "control", forced_first=True)
    assert row["steps"][0]["choice"] == wf["trap"] and row["n_selector_calls"] == len(client.calls)


class StubJevClient:
    def __init__(self):
        self.calls = []

    def ask_choice(self, model, state, instructions, criteria, name="q"):
        self.calls.append((model, list(criteria)))
        return core.v1.make_decision(next(iter(criteria)), valid=True, usage={"input_tokens": 200, "output_tokens": 10},
                                     model=model)


def test_jev_arm_uses_pinned_model_and_shared_spend_guard():
    guard = arms.SpendGuard(1.0, {"usd_per_million_input_tokens": 0.042, "usd_per_million_output_tokens": 0.0})
    stub = StubJevClient()
    d = arms.JevArm(stub, guard=guard).choose("s", "i", CRIT)
    assert stub.calls[0][0] == "jev-1.13.0" and d["choice"] == "alpha"
    assert abs(guard.spent - 200 * 0.042 / 1e6) < 1e-15
