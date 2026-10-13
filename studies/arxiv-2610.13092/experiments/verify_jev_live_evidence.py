"""Integrity verifier for the committed jev-live-systemone-check-v1 evidence (CI-safe, no network, no key).

Checks that the sanitized result JSON is consistent with the frozen fixture and with itself
(aggregates recomputed from rows). It does NOT judge Jev quality: FAIL-valued or poor results
verify fine; only tampering, drift or leaked credentials fail verification.
Exit 0 with NOT_RUN when no evidence file exists yet.
"""
from __future__ import annotations

import importlib.util
import json
import math
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EVIDENCE = HERE.parent / "evidence" / "jev_live_systemone_check_v1.result.json"

_spec = importlib.util.spec_from_file_location("jev_live_runner", HERE / "run_jev_live_systemone_check.py")
runner = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(runner)

SECRET_PATTERNS = [re.compile(p, re.I) for p in (
    r"bearer\s+[a-z0-9._\-]{8,}", r"\bsk-[a-z0-9_\-]{8,}", r"authorization", r"api[_-]?key\s*[:=]\s*\S{8,}",
)]


def _close(a, b) -> bool:
    if a is None or b is None:
        return a is b
    if isinstance(a, dict):
        return isinstance(b, dict) and a.keys() == b.keys() and all(_close(a[k], b[k]) for k in a)
    if isinstance(a, (int, float)) and not isinstance(a, bool):
        return math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-12)
    return a == b


def verify(result: dict, fixture: dict) -> list[str]:
    errs: list[str] = []
    req = lambda cond, msg: None if cond else errs.append(msg)  # noqa: E731
    req(result.get("experiment_id") == runner.EXPERIMENT_ID, "experiment_id mismatch")
    req(result.get("status") == "LIVE_RUN_COMPLETED", "status is not LIVE_RUN_COMPLETED")
    req(result.get("fixture_sha256") == fixture["_sha256"] == runner.FIXTURE_SHA256,
        "fixture_sha256 does not match the frozen fixture")
    req(result.get("execution_environment") == "local", "execution_environment must be 'local'")
    req(result.get("claim_scope") == runner.CLAIM_SCOPE, "claim_scope altered")
    blob = json.dumps(result)
    for pat in SECRET_PATTERNS:
        req(not pat.search(blob), f"credential-like content matches /{pat.pattern}/")
    ident = result.get("test_a_identity", {})
    for probe in ("pinned_probe", "alias_probe"):
        hdrs = (ident.get(probe) or {}).get("headers", {})
        req(set(hdrs) <= runner.KEPT_HEADERS, f"{probe} has non-allowlisted headers")
    req(ident.get("requested_model") == fixture["api"]["pinned_model"], "requested_model mismatch")

    repeats = fixture["design"]["repeats"]
    b_rows = result.get("test_b", {}).get("rows", [])
    c_rows = result.get("test_c", {}).get("rows", [])
    req(len(b_rows) == len(fixture["test_b_cases"]) * repeats, "Test B row count mismatch")
    req(len(c_rows) == len(fixture["test_c_workflows"]) * repeats, "Test C row count mismatch")
    truth = {c["id"]: c["truth"] for c in fixture["test_b_cases"]}
    for r in b_rows:
        req(r["case_id"] in truth and r["truth"] == truth[r["case_id"]], f"Test B truth drift {r.get('case_id')}")
        req(r["correct"] == (r["choice"] == r["truth"]), f"Test B correct flag inconsistent {r['case_id']}")
    wf_ids = {w["id"] for w in fixture["test_c_workflows"]}
    req({r["workflow_id"] for r in c_rows} == wf_ids, "Test C workflow set mismatch")
    for r in c_rows:
        req(r["jev_cost_usd"] >= 0 and r["number_of_steps"] <= r["step_budget"],
            f"Test C row invalid {r['workflow_id']}")

    b_agg = runner.aggregate_test_b(b_rows, fixture["pricing"])
    c_agg = runner.aggregate_test_c(c_rows)
    req(_close(result["test_b"]["aggregate"], b_agg), "Test B aggregate does not match rows")
    req(_close(result["test_c"]["aggregate"], c_agg), "Test C aggregate does not match rows")
    req(_close(result.get("classification"), runner.classify(ident, b_agg, c_agg, fixture)),
        "classification does not match recomputation")
    req(_close(result.get("reference_policies_non_model"), runner.run_reference_policies(fixture)),
        "reference policies do not match deterministic recomputation")
    return errs


def main(path: Path = EVIDENCE) -> int:
    if not path.exists():
        print(json.dumps({"status": "NOT_RUN", "detail": "no committed live evidence yet"}))
        return 0
    fixture = runner.load_fixture()
    errs = verify(json.loads(path.read_text()), fixture)
    print(json.dumps({"status": "EVIDENCE_VERIFIED" if not errs else "EVIDENCE_INVALID", "errors": errs}, indent=2))
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1]) if len(sys.argv) > 1 else EVIDENCE))
