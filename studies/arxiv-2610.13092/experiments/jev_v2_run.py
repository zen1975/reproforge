"""Per-arm runner for jev-live-systemone-check-v2 (LOCAL ONLY; keys only in the process environment).

    TYPESAFE_API_KEY=...  SSL_CERT_FILE=/etc/ssl/cert.pem python jev_v2_run.py --arm jev     --phase pilot --out X.json
    ANTHROPIC_API_KEY=... python jev_v2_run.py --arm control --phase pilot --out Y.json

One process = one arm = one key = one sanitized evidence file (leak-checked against that arm's key).
Phase `test` is refused until the freeze hash below is pinned (design step 4). Without a key the runner
prints SKIPPED_NO_CREDENTIAL and exits 0 without writing evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import jev_v2_arms as arms  # noqa: E402
import jev_v2_core as core  # noqa: E402
import jev_v2_generator as gen  # noqa: E402

v1 = core.v1
EXPERIMENT_ID = "jev-live-systemone-check-v2"
FREEZE_FILES = ("jev_v2_core.py", "jev_v2_generator.py", "jev_v2_arms.py", "jev_v2_run.py")
FREEZE_SHA256 = None  # pinned at design step 4 (freeze + pre-registration); `test` phase refused until then
SPEND_CAP_USD = 5.0
ORDERS = (0, 1, 2)
KEY_ENV = {"jev": "TYPESAFE_API_KEY", "control": "ANTHROPIC_API_KEY"}
PRICING = {"jev": {"usd_per_million_input_tokens": 0.042, "usd_per_million_output_tokens": 0.0},
           "control": arms.CONTROL_PRICING}
CLAIM_SCOPE = (
    "Stress test on Jev 1.13's documented weak spots plus a neutral anchor, with a paired comparison against a "
    "named LLM candidate-interface control. Not an ALFWorld/AndroidWorld reproduction and not an estimate of "
    "the paper's effect sizes; descriptive only."
)


def freeze_sha256() -> str:
    h = hashlib.sha256()
    for name in FREEZE_FILES:
        h.update(name.encode() + b"\0" + (HERE / name).read_bytes() + b"\0")
    return h.hexdigest()


def instances_for(phase: str) -> list[dict]:
    seeds = gen.PILOT_SEEDS if phase == "pilot" else gen.TEST_SEEDS
    return gen.generate(seeds)


def expected_rows(phase: str) -> int:
    return len(instances_for(phase)) * len(ORDERS) * 2  # natural + forced_trap per instance and order


# ------------------------------------------------------------------ summaries
def _rate(n, d):
    return None if d == 0 else n / d


def summarize(rows: list[dict]) -> dict:
    n = len(rows)
    succ = [r for r in rows if r["final_success"]]
    dev = [r for r in rows if r["deviation_events"] > 0]
    nat = [r for r in rows if r["episode_type"] == "natural"]
    calls = sum(r["n_selector_calls"] for r in rows)
    lat = sum(r["decision_latency_total_s"] for r in rows)
    cost = sum(r["cost_usd"] for r in rows)
    wall = sum(r["workflow_latency_total_s"] for r in rows)
    return {
        "n_episodes": n,
        "initial_choice_correct_rate": _rate(sum(r["initial_choice_correct"] is True for r in nat), len(nat)),
        "initial_error_rate": _rate(sum(r["initial_choice_correct"] is False for r in nat), len(nat)),
        "prerequisite_valid_rate": _rate(sum(r["prerequisite_valid"] for r in rows), n),
        "deviation_episodes": len(dev),
        "recovery_attempted_among_deviations": _rate(sum(r["recovery_attempted"] for r in dev), len(dev)),
        "recovery_success_among_deviations": _rate(sum(r["recovery_success"] for r in dev), len(dev)),
        "premature_completion_count": sum(r["premature_completion"] for r in rows),
        "verification_wrong_count": sum(r["verification_wrong"] for r in rows),
        "invalid_responses": sum(r["invalid_responses"] for r in rows),
        "infrastructure_failures": sum(r["infrastructure_failure"] for r in rows),
        "final_success_count": len(succ),
        "success_rate": _rate(len(succ), n),
        "initial_correct_but_final_failed": sum(
            r["initial_choice_correct"] is True and not r["final_success"] for r in nat),
        "initial_wrong_but_final_success": sum(
            r["initial_choice_correct"] is False and r["final_success"] for r in nat),
        "selector_calls": calls,
        "decision_latency_per_call_s": _rate(lat, calls),
        "decision_cost_per_call_usd": _rate(cost, calls),
        "decision_cost_total_usd": cost,
        "task_latency_per_attempt_s": _rate(wall, n),
        "task_cost_per_attempt_usd": _rate(cost, n),
        "cost_per_delivered_success_usd": _rate(cost, len(succ)),
        "time_per_delivered_success_s": _rate(wall, len(succ)),
        "retry_wait_total_s_excluded_from_latency": sum(r["retry_wait_total_s"] for r in rows),
        "boundary": "Cost counts selector tokens only; the local machine has no environment or auxiliary-LLM cost.",
    }


def aggregate(rows: list[dict]) -> dict:
    nat = [r for r in rows if r["episode_type"] == "natural"]
    forced = [r for r in rows if r["episode_type"] == "forced_trap"]
    recoverable = [r for r in forced if r["family"] != "irreversible"]
    fams = sorted({r["family"] for r in rows})
    stress_nat = [r for r in nat if r["family"] != "anchor"]
    return {
        "all": summarize(rows),
        "natural": summarize(nat) if nat else None,
        "forced_trap": summarize(forced) if forced else None,
        "forced_trap_recoverable_primary_c5": summarize(recoverable) if recoverable else None,
        "forced_trap_irreversible_negative_control": summarize(
            [r for r in forced if r["family"] == "irreversible"]) if forced else None,
        "by_family": {f: {"natural": summarize([r for r in nat if r["family"] == f]) if nat else None,
                          "forced_trap": summarize([r for r in forced if r["family"] == f]) if forced else None}
                      for f in fams},
        "by_order_natural": {str(o): summarize([r for r in nat if r["order_idx"] == o])
                             for o in ORDERS if any(r["order_idx"] == o for r in nat)},
        "difficulty_window": {
            "definition": "fraction of natural stress-family episodes (anchor excluded, all orders) with "
                          "initial_choice_correct == False; pre-registered window [0.10, 0.60]",
            "initial_error_rate": _rate(sum(r["initial_choice_correct"] is False for r in stress_nat),
                                        len(stress_nat)),
        },
    }


# ------------------------------------------------------------------ run loop
def run_phase(selector, arm: str, instances: list[dict], pricing: dict, progress=lambda m: None,
              checkpoint=None) -> tuple[list[dict], str]:
    rows: list[dict] = []
    status = "COMPLETED"
    try:
        for i, wf in enumerate(instances):
            for order in ORDERS:
                for forced in (False, True):
                    row = core.run_episode_v2(wf, selector, order, pricing, arm, forced_first=forced)
                    rows.append(row)
                    if checkpoint:
                        checkpoint(row)
            progress(f"{i + 1}/{len(instances)} instances ({wf['family']})")
    except arms.SpendCapReached as exc:
        status = "INCOMPLETE_SPEND_CAP"
        progress(f"STOP: {exc}")
    except KeyboardInterrupt:
        status = "INCOMPLETE_INTERRUPTED"
    except Exception as exc:  # noqa: BLE001 - recorded in the evidence status, never swallowed
        status = f"INCOMPLETE_ERROR:{type(exc).__name__}"
        progress(f"ERROR: {type(exc).__name__}")
    return rows, status


def build_evidence(arm: str, phase: str, rows: list[dict], status: str, identity: dict, spent: float) -> dict:
    return {
        "experiment_id": EXPERIMENT_ID, "phase": phase, "arm": arm, "status": status,
        "arm_label": "Jev (jev-1.13.0)" if arm == "jev" else f"LLM candidate-interface control ({arms.CONTROL_MODEL})",
        "freeze_sha256": freeze_sha256(), "execution_environment": "local",
        "spend_usd": spent, "spend_cap_usd": SPEND_CAP_USD,
        "expected_rows": expected_rows(phase), "identity": identity,
        "aggregate": aggregate(rows) if rows else None, "rows": rows, "claim_scope": CLAIM_SCOPE,
    }


# ------------------------------------------------------------------ identity probes (live)
def jev_identity(client) -> dict:
    return v1.test_a_identity(client, v1.load_fixture())


def control_identity(client) -> dict:
    ident = {"timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
             "requested_model": arms.CONTROL_MODEL}
    try:
        m = client.models.retrieve(arms.CONTROL_MODEL)
        ident["model_info"] = {k: getattr(m, k, None) for k in ("id", "display_name", "max_input_tokens", "max_tokens")}
    except Exception as exc:  # noqa: BLE001
        ident["model_info"] = {"error": type(exc).__name__}
    probe = arms.ControlArm(client).choose("The system is ready.", "Is the system ready?",
                                           {"yes": "Ready.", "no": "Not ready."})
    ident["probe"] = {k: probe.get(k) for k in ("valid", "model", "usage", "latency_s", "request_id", "stop_reason")}
    ident["resolved_model"] = probe.get("model")
    return ident


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", choices=("jev", "control"), required=True)
    ap.add_argument("--phase", choices=("pilot", "test"), required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--cap-usd", type=float, default=SPEND_CAP_USD)
    args = ap.parse_args(argv)
    key = os.environ.get(KEY_ENV[args.arm], "").strip()
    if not key:
        print(json.dumps({"experiment_id": EXPERIMENT_ID, "arm": args.arm, "status": "SKIPPED_NO_CREDENTIAL",
                          "detail": f"{KEY_ENV[args.arm]} is not set; no API call, no evidence."}, indent=2))
        return 0
    if args.phase == "test" and (FREEZE_SHA256 is None or FREEZE_SHA256 != freeze_sha256()):
        print("REFUSED: test phase requires the pinned freeze hash (design step 4).", file=sys.stderr)
        return 4
    pricing = PRICING[args.arm]
    guard = arms.SpendGuard(min(args.cap_usd, SPEND_CAP_USD), pricing)
    if args.arm == "jev":
        client = v1.JevClient(v1.load_fixture()["api"], key)
        identity = jev_identity(client)
        ok = identity.get("resolved_model") == "jev-1.13.0"
        selector = arms.JevArm(client, guard=guard)
    else:
        try:
            import anthropic
        except ImportError:
            print("pip install 'anthropic>=1,<2' (optional extra: reproforge[control])", file=sys.stderr)
            return 5
        client = anthropic.Anthropic(api_key=key, max_retries=0, timeout=60.0)
        identity = control_identity(client)
        ok = identity.get("resolved_model") == arms.CONTROL_MODEL
        selector = arms.ControlArm(client, guard=guard)
    if not ok:
        print(json.dumps({"status": "ABORTED_IDENTITY_FAILED", "identity_keys": sorted(identity)}), file=sys.stderr)
        return 3
    partial = Path(args.out + ".partial.jsonl")
    with partial.open("w") as fh:
        rows, status = run_phase(
            selector, args.arm, instances_for(args.phase), pricing,
            progress=lambda m: print(f"[{time.strftime('%H:%M:%S')}] {m}", file=sys.stderr, flush=True),
            checkpoint=lambda r: (fh.write(json.dumps(r) + "\n"), fh.flush()))
    evidence = build_evidence(args.arm, args.phase, rows, status, json.loads(json.dumps(identity)), guard.spent)
    text = json.dumps(evidence, indent=2, sort_keys=True)
    if key in text:
        print("ABORT: credential value found in output; refusing to write.", file=sys.stderr)
        return 2
    Path(args.out).write_text(text + "\n")
    partial.unlink(missing_ok=True)
    print(json.dumps({"arm": args.arm, "phase": args.phase, "status": status, "rows": len(rows),
                      "spend_usd": guard.spent}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
