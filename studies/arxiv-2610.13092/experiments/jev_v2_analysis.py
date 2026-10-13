"""Paired analysis and integrity verification for jev-live-systemone-check-v2 evidence (offline, no keys).

Contrasts are control - Jev on identical (instance, order, episode type) units. Uncertainty: instance-cluster
bootstrap (orders and episode types of one instance are not independent) with a fixed seed, plus exact McNemar
for paired binary outcomes. Descriptive only: no multiplicity-adjusted significance, no causal claim.
"""
from __future__ import annotations

import importlib.util
import json
import math
import random
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import jev_v2_arms as arms  # noqa: E402
import jev_v2_core as core  # noqa: E402
import jev_v2_run as run  # noqa: E402

BOOT_SEED, BOOT_N = 20261014, 2000
SECRET_PATTERNS = [re.compile(p, re.I) for p in (
    r"bearer\s+[a-z0-9._\-]{8,}", r"\bsk-[a-z0-9_\-]{8,}", r"authorization", r"x-api-key",
    r"api[_-]?key\s*[:=]\s*\S{8,}")]
RESOLVED = {"jev": "jev-1.13.0", "control": arms.CONTROL_MODEL}

_spec = importlib.util.spec_from_file_location("jev_audit", HERE / "run_efficiency_transfer_audit.py")
audit = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(audit)  # classify_transfer / pct_change from the frozen published-aggregate audit


def _key(r):
    return (r["workflow_id"], r["order_idx"], r["episode_type"])


def pair_rows(jev_rows, ctrl_rows):
    cj, cc = {_key(r): r for r in jev_rows}, {_key(r): r for r in ctrl_rows}
    return [(cj[k], cc[k]) for k in sorted(cj) if k in cc]


def _ratio(num, den):
    return None if den == 0 else num / den


def _mcnemar(pairs, f):
    b = sum(f(j) and not f(c) for j, c in pairs)   # Jev only
    c_ = sum(f(c) and not f(j) for j, c in pairs)  # control only
    n = b + c_
    if n == 0:
        return {"jev_only": b, "control_only": c_, "p_exact_two_sided": 1.0}
    k = min(b, c_)
    p = min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n)
    return {"jev_only": b, "control_only": c_, "p_exact_two_sided": p}


def contrast(name, pairs, select, num, den, binary=False):
    sel = [(j, c) for j, c in pairs if select(j)]
    if not sel:
        return {"name": name, "n_pairs": 0, "note": "no pairs"}
    clusters = {}
    for j, c in sel:
        a = clusters.setdefault(j["workflow_id"], [0.0, 0.0, 0.0, 0.0])
        a[0] += num(j); a[1] += den(j); a[2] += num(c); a[3] += den(c)  # noqa: E702

    def stat(cl):
        sj, dj = sum(x[0] for x in cl), sum(x[1] for x in cl)
        sc, dc = sum(x[2] for x in cl), sum(x[3] for x in cl)
        rj, rc = _ratio(sj, dj), _ratio(sc, dc)
        return rj, rc, (None if rj is None or rc is None else rc - rj)

    vals = list(clusters.values())
    rj, rc, point = stat(vals)
    rng = random.Random(f"{BOOT_SEED}:{name}")
    boots = []
    for _ in range(BOOT_N):
        s = stat([vals[rng.randrange(len(vals))] for _ in vals])[2]
        if s is not None:
            boots.append(s)
    boots.sort()
    ci = [boots[int(0.025 * (len(boots) - 1))], boots[int(round(0.975 * (len(boots) - 1)))]] if boots else None
    out = {"name": name, "n_pairs": len(sel), "n_instance_clusters": len(vals), "jev": rj, "control": rc,
           "diff_control_minus_jev": point, "ci95_cluster_bootstrap": ci}
    if binary:
        out["mcnemar"] = _mcnemar(sel, lambda r: bool(num(r)))
    return out


def analyze(jev_ev: dict, ctrl_ev: dict) -> dict:
    pairs = pair_rows(jev_ev["rows"], ctrl_ev["rows"])
    nat = lambda r: r["episode_type"] == "natural"  # noqa: E731
    stress_nat = lambda r: nat(r) and r["family"] != "anchor"  # noqa: E731
    anchor_nat = lambda r: nat(r) and r["family"] == "anchor"  # noqa: E731
    rec = lambda r: r["episode_type"] == "forced_trap" and r["family"] != "irreversible"  # noqa: E731
    irr = lambda r: r["episode_type"] == "forced_trap" and r["family"] == "irreversible"  # noqa: E731
    one = lambda r: 1  # noqa: E731
    ok = lambda r: 1 if r["initial_choice_correct"] is True else 0  # noqa: E731
    fin = lambda r: 1 if r["final_success"] else 0  # noqa: E731
    c = [
        contrast("decision_initial_correct__stress_natural", pairs, stress_nat, ok, one, True),
        contrast("decision_initial_correct__anchor_natural", pairs, anchor_nat, ok, one, True),
        contrast("final_success__stress_natural", pairs, stress_nat, fin, one, True),
        contrast("final_success__anchor_natural", pairs, anchor_nat, fin, one, True),
        contrast("recovery_final_success__forced_trap_recoverable_PRIMARY_C5", pairs, rec, fin, one, True),
        contrast("recovery_final_success__forced_trap_irreversible_negative_control", pairs, irr, fin, one, True),
        contrast("cost_per_delivered_success_usd__natural", pairs, nat, lambda r: r["cost_usd"], fin),
        contrast("time_per_delivered_success_s__natural", pairs, nat, lambda r: r["workflow_latency_total_s"], fin),
        contrast("decision_latency_per_call_s__natural", pairs, nat, lambda r: r["decision_latency_total_s"],
                 lambda r: r["n_selector_calls"]),
    ]
    by_family = {}
    for fam in sorted({j["family"] for j, _ in pairs}):
        by_family[fam] = {
            "natural_final_success": contrast(f"final_success__{fam}_natural", pairs,
                                              lambda r, f=fam: nat(r) and r["family"] == f, fin, one, True),
            "forced_trap_final_success": contrast(f"final_success__{fam}_forced", pairs,
                                                  lambda r, f=fam: r["episode_type"] == "forced_trap"
                                                  and r["family"] == f, fin, one, True)}
    by_order = {str(o): contrast(f"initial_correct__order{o}", pairs,
                                 lambda r, o=o: stress_nat(r) and r["order_idx"] == o, ok, one, True)
                for o in run.ORDERS}
    agg_j, agg_c = jev_ev["aggregate"]["natural"], ctrl_ev["aggregate"]["natural"]

    def pct(f):
        return audit.pct_change(agg_j[f], agg_c[f]) if agg_j[f] and agg_c[f] else None
    d_dec, d_task = pct("decision_latency_per_call_s"), pct("task_latency_per_attempt_s")
    d_deliv = pct("time_per_delivered_success_s")
    transfer = None
    if None not in (d_dec, d_task, d_deliv):
        transfer = {"jev_vs_control_pct": {"decision_latency": d_dec, "task_latency": d_task, "delivered_time": d_deliv},
                    "class_time": audit.classify_transfer(d_dec, d_task, d_deliv),
                    "note": "Jev relative to control. OVERHEAD_ABSORPTION is not designed to occur (no auxiliary "
                            "overhead); speed/cost compare different providers and are reference values."}
    return {
        "experiment_id": run.EXPERIMENT_ID, "phase": jev_ev["phase"], "n_paired_units": len(pairs),
        "bootstrap": {"seed": BOOT_SEED, "resamples": BOOT_N, "cluster": "instance"},
        "contrasts": c, "by_family": by_family, "by_order": by_order, "transfer_classification": transfer,
        "interpretation_guards": [
            "A Jev decision advantage is not an agent advantage unless delivered-success metrics agree.",
            "Both arms near 0% or 100% means non-discriminating, not support.",
            "Stressor families target Jev's documented weak spots; read them as a stress test, not a C-vs-J verdict.",
        ],
        "claim_scope": run.CLAIM_SCOPE,
    }


# ------------------------------------------------------------------ verification
def _close(a, b):
    if a is None or b is None:
        return a is b
    if isinstance(a, dict):
        return isinstance(b, dict) and a.keys() == b.keys() and all(_close(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return isinstance(b, list) and len(a) == len(b) and all(_close(x, y) for x, y in zip(a, b, strict=True))
    if isinstance(a, (int, float)) and not isinstance(a, bool):
        return math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-12)
    return a == b


def verify_arm(ev: dict) -> list[str]:
    errs: list[str] = []
    req = lambda cond, msg: None if cond else errs.append(msg)  # noqa: E731
    arm, phase = ev.get("arm"), ev.get("phase")
    req(ev.get("experiment_id") == run.EXPERIMENT_ID, "experiment_id mismatch")
    req(arm in RESOLVED and phase in ("pilot", "test"), "bad arm/phase")
    if errs:
        return errs
    req(ev.get("execution_environment") == "local", "execution_environment must be local")
    req(ev.get("claim_scope") == run.CLAIM_SCOPE, "claim_scope altered")
    if phase == "test":
        req(run.FREEZE_SHA256 is not None and ev.get("freeze_sha256") == run.FREEZE_SHA256,
            "test evidence does not match the pinned freeze hash")
    blob = json.dumps(ev)
    for pat in SECRET_PATTERNS:
        req(not pat.search(blob), f"credential-like content matches /{pat.pattern}/")
    ident = ev.get("identity", {})
    req(ident.get("resolved_model") == RESOLVED[arm], "identity.resolved_model != pinned model")
    if arm == "jev":
        for probe in ("pinned_probe", "alias_probe"):
            req(set((ident.get(probe) or {}).get("headers", {})) <= run.v1.KEPT_HEADERS, "non-allowlisted headers")
    rows = ev.get("rows", [])
    complete = ev.get("status") == "COMPLETED"
    if complete:
        req(len(rows) == ev.get("expected_rows") == run.expected_rows(phase), "row count != expected")
    insts = {w["id"]: w for w in run.instances_for(phase)}
    seen = set()
    for r in rows:
        k = _key(r)
        req(k not in seen, f"duplicate row {k}")
        seen.add(k)
        wf = insts.get(r["workflow_id"])
        req(wf is not None and wf["family"] == r["family"], f"row not from the {phase} generator: {r['workflow_id']}")
        req(r["arm"] == arm, "row arm mismatch")
        req(not [x for x in r if x.startswith("jev_")], "arm-specific field names in a row")
        if wf:
            order_list = list(core.build_criteria(wf, r["order_idx"]))
            req(r["truth_pos"] == order_list.index(core.truth_at_start(wf)) and r["trap_pos"] == order_list.index(wf["trap"]),
                f"position record mismatch {k}")
            req(r["start_distance"] == core.distance_to_goal(wf, core.MachineV2(wf).state, []),
                f"start_distance mismatch {k}")
        req(r["number_of_steps"] <= r["step_budget"], f"budget exceeded {k}")
    if rows:
        req(_close(ev.get("aggregate"), run.aggregate(rows)), "aggregate does not match rows")
    req(ev.get("spend_usd", 0) <= ev.get("spend_cap_usd", 0) * 1.05 + 1e-9, "spend exceeds cap")
    return errs


def verify_analysis(an: dict, jev_ev: dict, ctrl_ev: dict) -> list[str]:
    errs = []
    if jev_ev.get("status") != "COMPLETED" or ctrl_ev.get("status") != "COMPLETED":
        errs.append("analysis requires COMPLETED evidence for both arms")
    elif not _close(an, analyze(jev_ev, ctrl_ev)):
        errs.append("analysis does not match recomputation from the two evidence files")
    return errs


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("jev"), ap.add_argument("control"), ap.add_argument("--out")  # noqa: B018
    args = ap.parse_args(argv)
    jev_ev, ctrl_ev = json.loads(Path(args.jev).read_text()), json.loads(Path(args.control).read_text())
    errs = verify_arm(jev_ev) + verify_arm(ctrl_ev)
    if errs:
        print(json.dumps({"status": "EVIDENCE_INVALID", "errors": errs}, indent=2))
        return 1
    an = analyze(jev_ev, ctrl_ev)
    text = json.dumps(an, indent=2, sort_keys=True)
    if args.out:
        Path(args.out).write_text(text + "\n")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
