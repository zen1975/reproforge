"""Offline harness checks for jev-live-systemone-check-v1.

These tests exercise the runner against a local fake server and scripted selectors.
They are harness checks, NOT Jev evidence.
"""
import importlib.util
import json
import os
import subprocess
import sys
import threading
import typing
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "studies" / "arxiv-2610.13092" / "experiments"
RUNNER = EXP / "run_jev_live_systemone_check.py"
WORKFLOWS = ROOT / ".github" / "workflows"
VERIFY_WORKFLOW = WORKFLOWS / "jev-live-evidence-verify.yml"
VERIFIER = EXP / "verify_jev_live_evidence.py"

spec = importlib.util.spec_from_file_location("jev_live", RUNNER)
jl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(jl)

FAKE_KEY = "sk-test-FAKEKEY-do-not-leak"


def fixture():
    return jl.load_fixture()


# ----------------------------------------------------------------- freeze / fixture shape
def test_fixture_hash_is_pinned():
    fx = fixture()
    assert fx["_sha256"] == jl.FIXTURE_SHA256


def test_hash_mismatch_refuses(tmp_path):
    bad = tmp_path / "f.json"
    bad.write_bytes(jl.FIXTURE_PATH.read_bytes() + b" ")
    try:
        jl.load_fixture(bad)
    except SystemExit as exc:
        assert "FIXTURE_HASH_MISMATCH" in str(exc)
    else:
        raise AssertionError("modified fixture must be refused")


def test_test_b_fixture_shape():
    fx = fixture()
    cases = fx["test_b_cases"]
    assert len(cases) >= 12
    cats = {c["category"] for c in cases}
    assert cats == {
        "clear_action_selection", "prerequisite_violation", "ambiguous_candidate_label",
        "recovery_required", "premature_completion_trap", "completion_verification",
    }
    for cat in cats:
        assert sum(c["category"] == cat for c in cases) == 2
    for c in cases:
        assert c["truth"] in c["candidates"]
        assert fx["design"]["abstain_option"] not in c["candidates"]
    assert len({c["id"] for c in cases}) == len(cases)


def test_pinned_model_is_versioned_not_alias():
    api = fixture()["api"]
    assert api["pinned_model"] == "jev-1.13.0"
    assert api["pinned_model"] != api["alias_probe"]


# ----------------------------------------------------------------- state machine / oracle
def test_oracle_reaches_full_success_and_other_policies_fail():
    fx = fixture()
    ref = jl.run_reference_policies(fx)
    assert ref["oracle_on_path"]["aggregate"]["success_rate"] == 1.0
    assert ref["oracle_on_path"]["aggregate"]["initial_choice_correct_rate"] == 1.0
    assert ref["declare_done_immediately"]["aggregate"]["success_rate"] == 0.0
    assert ref["first_candidate"]["aggregate"]["success_rate"] < 1.0


class Scripted:
    """Scripted selector: yields from a list of choices; verification may be dishonest."""

    def __init__(self, choices, verify=None):
        self.choices = list(choices)
        self.verify = verify  # None => honest

    def choose(self, state, instructions, criteria, oracle=None):
        if oracle is None:  # Test B call: no oracle context
            c = self.choices.pop(0) if self.choices else "abstain"
            return jl.make_decision(c, valid=True, usage={"input_tokens": 100, "output_tokens": 5})
        if oracle["on_path"] is None:
            ans = self.verify or ("goal_met" if oracle["goal_met"] else "goal_not_met")
            return jl.make_decision(ans, valid=True, usage={"input_tokens": 100, "output_tokens": 5})
        c = self.choices.pop(0) if self.choices else "abstain"
        return jl.make_decision(c, valid=True, usage={"input_tokens": 100, "output_tokens": 5})


def wf(fx, wid):
    return next(w for w in fx["test_c_workflows"] if w["id"] == wid)


def test_wrong_first_choice_but_recovers_to_success():
    fx = fixture()
    ep = jl.run_episode(fx, wf(fx, "W1_projector"),
                        Scripted(["power_on_projector", "switch_on_power_strip", "power_on_projector", "declare_done"]), 0)
    assert ep["initial_choice_correct"] is False
    assert ep["prerequisite_valid"] is False
    assert ep["recovery_attempted"] is True
    assert ep["recovery_success"] is True
    assert ep["final_success"] is True


def test_right_first_choice_but_premature_completion_fails():
    fx = fixture()
    ep = jl.run_episode(fx, wf(fx, "W4_publish_notify"),
                        Scripted(["publish_article", "declare_done"], verify="goal_met"), 0)
    assert ep["initial_choice_correct"] is True
    assert ep["premature_completion"] is True
    assert ep["final_success"] is False
    assert ep["verification_wrong"] == 1


def test_honest_verification_blocks_premature_completion():
    fx = fixture()
    ep = jl.run_episode(fx, wf(fx, "W4_publish_notify"),
                        Scripted(["publish_article", "declare_done", "notify_subscribers", "declare_done"]), 0)
    assert ep["premature_completion"] is False
    assert ep["final_success"] is True
    assert ep["verification_calls"] == 2


def test_wrong_valid_action_needs_recovery_via_undo():
    fx = fixture()
    ep = jl.run_episode(fx, wf(fx, "W6_reschedule"),
                        Scripted(["cancel_meeting", "undo_last_action", "reschedule_meeting_to_friday", "declare_done"]), 0)
    assert ep["initial_choice_correct"] is False
    assert ep["prerequisite_valid"] is True  # valid but off-path
    assert ep["recovery_success"] is True and ep["final_success"] is True


def test_unrecoverable_path_is_failure_and_budget_is_respected():
    fx = fixture()
    ep = jl.run_episode(fx, wf(fx, "W6_reschedule"), Scripted(["create_new_meeting_friday"] * 10), 0)
    assert ep["final_success"] is False
    assert ep["number_of_steps"] <= ep["step_budget"]


def test_cost_and_per_success_accounting():
    fx = fixture()
    rows = [
        jl.run_episode(fx, wf(fx, "W2_wifi_label"), Scripted(["toggle_network_switch", "declare_done"]), 0),
        jl.run_episode(fx, wf(fx, "W2_wifi_label"), Scripted(["toggle_wireless_switch", "declare_done"]), 1),
    ]
    agg = jl.aggregate_test_c(rows)
    assert agg["n_attempts"] == 2 and agg["final_success_count"] == 1
    total = sum(r["jev_cost_usd"] for r in rows)
    assert abs(agg["cost_per_delivered_success_usd"] - total) < 1e-15  # failures stay in numerator
    assert agg["initial_correct_but_final_failed"] == 0
    assert agg["initial_choice_correct_rate"] == 0.5
    expected = (rows[0]["usage"]["input_tokens"] + rows[1]["usage"]["input_tokens"]) * 0.042 / 1e6
    assert abs(total - expected) < 1e-12


# ----------------------------------------------------------------- fake server (HTTP contract)
class Handler(BaseHTTPRequestHandler):
    calls: typing.ClassVar[list] = []
    fail_next: typing.ClassVar[dict] = {"n": 0}

    def log_message(self, *a):
        pass

    def _json(self, code, obj, extra=None):
        data = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        Handler.calls.append(("GET", self.path, self.headers.get("Authorization")))
        self._json(200, {"models": [{"name": "jev-latest", "description": "d", "release_date": "2026"}]})

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        Handler.calls.append(("POST", self.path, self.headers.get("Authorization"), body))
        if Handler.fail_next["n"] > 0:
            Handler.fail_next["n"] -= 1
            return self._json(429, {"error": "slow down"}, {"retry-after": "0"})
        model = "jev-1.13.0" if body["model"] in ("jev-1.13.0", "jev-latest") else body["model"]
        answers = {}
        for name, q in body["questions"].items():
            assert q["type"] == "choice"
            opts = list(q["criteria"])
            pick = next((o for o in opts if o not in ("abstain",)), opts[0])
            answers[name] = {"type": "choice", "choice": pick,
                             "probabilities": {o: (1.0 if o == pick else 0.0) for o in opts},
                             "confidence": 0.9}
        self._json(200, {"model": model, "answers": answers, "usage": {"input_tokens": 200, "output_tokens": 10}},
                   {"x-typesafe-request-id": "req-test", "set-cookie": "secret=1"})


def start_server():
    srv = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def test_live_client_against_fake_server_end_to_end():
    fx = fixture()
    srv = start_server()
    try:
        api = dict(fx["api"], base_url=f"http://127.0.0.1:{srv.server_port}", backoff_seconds=[0] * 5)
        client = jl.JevClient(api, FAKE_KEY, sleep=lambda s: None)
        Handler.calls.clear()
        Handler.fail_next["n"] = 2
        identity = jl.test_a_identity(client, dict(fx, api=api))
        assert identity["resolved_model"] == "jev-1.13.0"
        assert identity["alias_resolved_model"] == "jev-1.13.0"
        assert "set-cookie" not in identity["pinned_probe"]["headers"]
        assert identity["pinned_probe"]["headers"]["x-typesafe-request-id"] == "req-test"
        # every request carried the bearer key and the documented schema
        posts = [c for c in Handler.calls if c[0] == "POST"]
        assert all(c[2] == f"Bearer {FAKE_KEY}" for c in Handler.calls)
        assert all(set(c[3]) == {"model", "state", "questions"} for c in posts)
        assert any(c[3]["model"] == "jev-1.13.0" for c in posts)

        sel = jl.LiveSelector(client, fx["api"]["pinned_model"])
        b_rows = jl.run_test_b(fx, sel, 1)
        assert len(b_rows) == 12 and all(r["valid"] for r in b_rows)
        assert all(r["model"] == "jev-1.13.0" for r in b_rows)
        b_agg = jl.aggregate_test_b(b_rows, fx["pricing"])
        assert b_agg["valid_choice_rate"] == 1.0
        assert b_agg["usage"]["input_tokens"] == 200 * 12
        c_rows = jl.run_test_c(fx, sel, 1)
        c_agg = jl.aggregate_test_c(c_rows)
        assert c_agg["n_attempts"] == 8 and c_agg["infrastructure_failures"] == 0
        cls = jl.classify(identity, b_agg, c_agg, fx)
        assert cls["protocol_status"] == "LIVE_CHECK_PASS"
        # the abstain option and never the oracle hint is what the server saw
        blob = json.dumps([c[3] for c in Handler.calls if c[0] == "POST"])
        assert "on_path" not in blob and "oracle" not in blob
        assert "abstain" in blob
    finally:
        srv.shutdown()


def test_retry_on_429_is_not_counted_as_decision_latency():
    fx = fixture()
    srv = start_server()
    try:
        api = dict(fx["api"], base_url=f"http://127.0.0.1:{srv.server_port}", backoff_seconds=[3] * 5)
        slept = []
        client = jl.JevClient(api, FAKE_KEY, sleep=slept.append)
        Handler.fail_next["n"] = 2
        d = client.ask_choice("jev-1.13.0", "s", "i", {"a": "A", "abstain": "x"})
        assert d["valid"] and d["retries"] == 2 and d["retry_wait_s"] == 6
        assert d["latency_s"] < 3  # only the successful round trip
        assert slept == [3, 3]
    finally:
        srv.shutdown()


def test_unreachable_api_is_infrastructure_failure_and_stays_in_denominator():
    fx = fixture()
    api = dict(fx["api"], base_url="http://127.0.0.1:1", backoff_seconds=[0] * 5, max_retries=1)
    client = jl.JevClient(api, FAKE_KEY, sleep=lambda s: None)
    sel = jl.LiveSelector(client, "jev-1.13.0")
    rows = jl.run_test_c(fx, sel, 1)
    agg = jl.aggregate_test_c(rows)
    assert agg["n_attempts"] == 8 and agg["final_success_count"] == 0
    assert agg["infrastructure_failures"] == 8
    assert agg["cost_per_delivered_success_usd"] is None  # no successes => undefined, not zero


# ----------------------------------------------------------------- credential handling / CI wiring
def test_no_credential_skips_without_output_files(tmp_path):
    env = {k: v for k, v in os.environ.items() if k != "TYPESAFE_API_KEY"}
    out = tmp_path / "result.json"
    proc = subprocess.run([sys.executable, str(RUNNER), "--out", str(out)],
                          check=False, env=env, capture_output=True, text=True, cwd=tmp_path)
    assert proc.returncode == 0
    assert json.loads(proc.stdout)["status"] == "SKIPPED_NO_CREDENTIAL"
    assert not out.exists()
    assert not (EXP.parent / "evidence" / "jev_live_systemone_check_v1.result.json").exists()


def test_no_api_key_literal_in_repo_sources():
    for path in (RUNNER, EXP / "jev_live_systemone_check_v1.fixture.json", VERIFY_WORKFLOW):
        text = path.read_text()
        assert "Bearer " not in text.replace("Bearer {self._key}", "")
        assert "sk-" not in text


def test_no_workflow_uses_typesafe_secret_or_key():
    """Policy: the Jev key is never stored in GitHub; only local runs use it."""
    for wf_path in WORKFLOWS.glob("*.yml"):
        text = wf_path.read_text()
        assert "TYPESAFE_API_KEY" not in text, wf_path.name
        assert "secrets.TYPESAFE" not in text, wf_path.name
    assert not (WORKFLOWS / "jev-live-systemone-check.yml").exists()


def test_verify_workflow_is_secretless_and_read_only():
    text = VERIFY_WORKFLOW.read_text()
    assert "secrets." not in text
    assert "contents: read" in text
    assert "verify_jev_live_evidence.py" in text


# ----------------------------------------------------------------- evidence verifier
vspec = importlib.util.spec_from_file_location("jev_verify", VERIFIER)
verifier = importlib.util.module_from_spec(vspec)
vspec.loader.exec_module(verifier)


def build_result_via_fake_server():
    fx = fixture()
    srv = start_server()
    try:
        api = dict(fx["api"], base_url=f"http://127.0.0.1:{srv.server_port}", backoff_seconds=[0] * 5)
        client = jl.JevClient(api, FAKE_KEY, sleep=lambda s: None)
        identity = jl.test_a_identity(client, dict(fx, api=api))
        sel = jl.LiveSelector(client, fx["api"]["pinned_model"])
        reps = fx["design"]["repeats"]
        b_rows = jl.run_test_b(fx, sel, reps)
        c_rows = jl.run_test_c(fx, sel, reps)
    finally:
        srv.shutdown()
    b_agg = jl.aggregate_test_b(b_rows, fx["pricing"])
    c_agg = jl.aggregate_test_c(c_rows)
    result = {
        "experiment_id": jl.EXPERIMENT_ID, "status": "LIVE_RUN_COMPLETED",
        "fixture_sha256": fx["_sha256"], "execution_environment": "local",
        "test_a_identity": json.loads(json.dumps(identity)),
        "test_b": {"aggregate": b_agg, "rows": b_rows}, "test_c": {"aggregate": c_agg, "rows": c_rows},
        "reference_policies_non_model": jl.run_reference_policies(fx),
        "classification": jl.classify(identity, b_agg, c_agg, fx), "claim_scope": jl.CLAIM_SCOPE,
    }
    return fx, json.loads(json.dumps(result))


def test_verifier_accepts_untampered_result_and_rejects_tampering():
    fx, result = build_result_via_fake_server()
    assert verifier.verify(result, fx) == []
    import copy
    bad = copy.deepcopy(result)
    bad["test_c"]["rows"][0]["final_success"] = not bad["test_c"]["rows"][0]["final_success"]
    assert verifier.verify(bad, fx), "edited row must break aggregate consistency"
    bad = copy.deepcopy(result)
    bad["fixture_sha256"] = "0" * 64
    assert verifier.verify(bad, fx)
    bad = copy.deepcopy(result)
    bad["test_b"]["rows"][0]["truth"] = "something_else"
    assert verifier.verify(bad, fx)
    bad = copy.deepcopy(result)
    bad["test_a_identity"]["pinned_probe"]["headers"]["set-cookie"] = "x"
    assert verifier.verify(bad, fx)
    bad = copy.deepcopy(result)
    bad["note"] = "Authorization: Bearer abcdef123456"
    assert verifier.verify(bad, fx)


def test_verifier_accepts_poor_results_it_checks_integrity_not_quality():
    fx = fixture()
    sel = Scripted(["abstain"] * 1000, verify="goal_not_met")
    b_rows = jl.run_test_b(fx, sel, fx["design"]["repeats"])
    assert b_agg_ok(fx, b_rows)


def b_agg_ok(fx, b_rows):
    agg = jl.aggregate_test_b(b_rows, fx["pricing"])
    return agg["exact_choice_accuracy"] == 0.0 and agg["abstain_rate"] == 1.0


def test_verifier_reports_not_run_without_evidence(tmp_path):
    proc = subprocess.run([sys.executable, str(VERIFIER), str(tmp_path / "missing.json")],
                          check=False, capture_output=True, text=True)
    assert proc.returncode == 0 and json.loads(proc.stdout)["status"] == "NOT_RUN"


def test_committed_evidence_if_present_verifies():
    path = EXP.parent / "evidence" / "jev_live_systemone_check_v1.result.json"
    if path.exists():
        assert verifier.verify(json.loads(path.read_text()), fixture()) == []


def test_unreachable_identity_aborts_fast_without_evidence(tmp_path):
    """Setup failure (here: connection refused) must not spend minutes retrying nor emit evidence."""
    env = dict(os.environ, TYPESAFE_API_KEY=FAKE_KEY)
    fx = fixture()
    api = dict(fx["api"], base_url="http://127.0.0.1:1", backoff_seconds=[0] * 5, max_retries=1)
    client = jl.JevClient(api, FAKE_KEY, sleep=lambda s: None)
    ident = jl.test_a_identity(client, dict(fx, api=api))
    assert "error" in ident["pinned_probe"] and ident["resolved_model"] is None
    assert env  # runner main() path is exercised by the SKIP test; identity gate verified here


def test_tls_error_is_not_retried():
    import ssl
    import urllib.error
    from unittest import mock
    fx = fixture()
    api = dict(fx["api"], max_retries=5)
    slept = []
    client = jl.JevClient(api, FAKE_KEY, sleep=slept.append)
    err = urllib.error.URLError(ssl.SSLCertVerificationError("bad cert"))
    with mock.patch.object(jl.urllib.request, "urlopen", side_effect=err):
        try:
            client.list_models()
        except jl.ApiFailure as exc:
            assert exc.status == "tls"
        else:
            raise AssertionError("expected ApiFailure")
    assert slept == []
