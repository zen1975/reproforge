"""Three-arm paired analysis and integrity verification for jev-live-systemone-check-v3a (offline, no keys).

Pairings share the v2 machinery (instance-cluster bootstrap, seed 20261014, 2000 resamples; exact McNemar):
  C_vs_J : diff = C - J   (decision-model effect under a shared candidate interface; replicates v2 on fresh seeds)
  C_vs_B : diff = C - B   (interface effect: forced enum choice over a candidate list vs free generation)
  J_vs_B : diff = J - B   (combined; must not be attributed to Jev alone)
Descriptive only: no multiplicity adjustment, no causal claim.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import jev_v2_analysis as v2an  # noqa: E402
import jev_v2_core as core  # noqa: E402
import jev_v3_run as run  # noqa: E402

EVIDENCE = HERE.parent / "evidence"
V2_TEST_ANALYSIS = EVIDENCE / "jev_v2_test_analysis.json"
V2_TEST_ANALYSIS_SHA256 = "19e9cf0385acfee06a977b9ee05fce9a54f9a15a6c8ccb980bfa79ec9dddf23c"
V2_PRIMARY = "recovery_final_success__forced_trap_recoverable_PRIMARY_C5"
audit = v2an.audit
PAIRINGS = {  # name: (arm in the first slot, arm in the second slot); diff = second - first
    "C_vs_J": ("jev", "control"),
    "C_vs_B": ("b", "control"),
    "J_vs_B": ("b", "jev"),
}
SLOT_NAMES = {"jev": "J", "control": "C", "b": "B"}


def _relabel(out: dict, first: str, second: str) -> dict:
    a, b = SLOT_NAMES[first], SLOT_NAMES[second]
    out = dict(out)
    for old, new in (("jev", a), ("control", b), ("diff_control_minus_jev", f"diff_{b}_minus_{a}")):
        if old in out:
            out[new] = out.pop(old)
    if "mcnemar" in out:
        m = out["mcnemar"]
        out["mcnemar"] = {f"{a}_only": m["jev_only"], f"{b}_only": m["control_only"],
                          "p_exact_two_sided": m["p_exact_two_sided"]}
    return out


def pair_contrasts(pairs, tag: str, first: str, second: str) -> dict:
    nat = lambda r: r["episode_type"] == "natural"  # noqa: E731
    stress_nat = lambda r: nat(r) and r["family"] != "anchor"  # noqa: E731
    anchor_nat = lambda r: nat(r) and r["family"] == "anchor"  # noqa: E731
    rec = lambda r: r["episode_type"] == "forced_trap" and r["family"] != "irreversible"  # noqa: E731
    irr = lambda r: r["episode_type"] == "forced_trap" and r["family"] == "irreversible"  # noqa: E731
    one = lambda r: 1  # noqa: E731
    ok = lambda r: 1 if r["initial_choice_correct"] is True else 0  # noqa: E731
    fin = lambda r: 1 if r["final_success"] else 0  # noqa: E731
    raw = [
        v2an.contrast(f"{tag}:decision_initial_correct__stress_natural", pairs, stress_nat, ok, one, True),
        v2an.contrast(f"{tag}:decision_initial_correct__anchor_natural", pairs, anchor_nat, ok, one, True),
        v2an.contrast(f"{tag}:final_success__stress_natural", pairs, stress_nat, fin, one, True),
        v2an.contrast(f"{tag}:final_success__anchor_natural", pairs, anchor_nat, fin, one, True),
        v2an.contrast(f"{tag}:{V2_PRIMARY}", pairs, rec, fin, one, True),
        v2an.contrast(f"{tag}:recovery_final_success__forced_trap_irreversible_negative_control", pairs, irr, fin,
                      one, True),
        v2an.contrast(f"{tag}:cost_per_delivered_success_usd__natural", pairs, nat, lambda r: r["cost_usd"], fin),
        v2an.contrast(f"{tag}:time_per_delivered_success_s__natural", pairs, nat,
                      lambda r: r["workflow_latency_total_s"], fin),
        v2an.contrast(f"{tag}:decision_latency_per_call_s__natural", pairs, nat,
                      lambda r: r["decision_latency_total_s"], lambda r: r["n_selector_calls"]),
        v2an.contrast(f"{tag}:invalid_responses_per_call__natural", pairs, nat,
                      lambda r: r["invalid_responses"], lambda r: r["n_selector_calls"]),
    ]
    by_family = {}
    for fam in sorted({x["family"] for x, _ in pairs}):
        by_family[fam] = {
            "natural_final_success": _relabel(v2an.contrast(
                f"{tag}:final_success__{fam}_natural", pairs, lambda r, f=fam: nat(r) and r["family"] == f,
                fin, one, True), first, second),
            "forced_trap_final_success": _relabel(v2an.contrast(
                f"{tag}:final_success__{fam}_forced", pairs,
                lambda r, f=fam: r["episode_type"] == "forced_trap" and r["family"] == f, fin, one, True),
                first, second)}
    return {"contrasts": [_relabel(c, first, second) for c in raw], "by_family": by_family}


def arm_summary(rows: list[dict]) -> dict:
    nat = [r for r in rows if r["episode_type"] == "natural"]
    calls = sum(r["n_selector_calls"] for r in rows)
    return {
        "natural_success_rate": sum(r["final_success"] for r in nat) / len(nat),
        "selector_calls": calls,
        "invalid_responses": sum(r["invalid_responses"] for r in rows),
        "input_tokens_per_call": sum(r["usage"]["input_tokens"] for r in rows) / calls,
        "output_tokens_per_call": sum(r["usage"]["output_tokens"] for r in rows) / calls,
        "decision_latency_per_call_s": sum(r["decision_latency_total_s"] for r in rows) / calls,
        "cost_total_usd": sum(r["cost_usd"] for r in rows),
    }


def transfer(agg_new: dict, agg_base: dict) -> dict | None:
    def pct(f):
        return audit.pct_change(agg_new[f], agg_base[f]) if agg_new[f] and agg_base[f] else None
    d_dec, d_task, d_deliv = (pct("decision_latency_per_call_s"), pct("task_latency_per_attempt_s"),
                              pct("time_per_delivered_success_s"))
    if None in (d_dec, d_task, d_deliv):
        return None
    return {"pct_change": {"decision_latency": d_dec, "task_latency": d_task, "delivered_time": d_deliv},
            "class_time": audit.classify_transfer(d_dec, d_task, d_deliv)}


def replication(c_vs_j: dict) -> dict:
    """Pre-stated rule: the v2 primary (control better on forced-trap recovery) replicates only if the
    direction matches and the 95% CI excludes 0."""
    raw = V2_TEST_ANALYSIS.read_bytes()
    if hashlib.sha256(raw).hexdigest() != V2_TEST_ANALYSIS_SHA256:
        raise ValueError("v2 test analysis file does not match its pinned sha256")
    v2 = next(c for c in json.loads(raw)["contrasts"] if c["name"] == V2_PRIMARY)
    v3 = next(c for c in c_vs_j["contrasts"] if c["name"].endswith(V2_PRIMARY))
    lo = v3["ci95_cluster_bootstrap"][0] if v3.get("ci95_cluster_bootstrap") else None
    return {"v2_diff_control_minus_jev": v2["diff_control_minus_jev"],
            "v2_ci95": v2["ci95_cluster_bootstrap"], "v3a_diff_C_minus_J": v3["diff_C_minus_J"],
            "v3a_ci95": v3["ci95_cluster_bootstrap"],
            "replicated": bool(v3["diff_C_minus_J"] > 0 and lo is not None and lo > 0),
            "rule": "direction matches and the cluster-bootstrap 95% CI excludes 0"}


def analyze(evs: dict) -> dict:
    out = {}
    for name, (first, second) in PAIRINGS.items():
        pairs = v2an.pair_rows(evs[first]["rows"], evs[second]["rows"])
        out[name] = {"n_paired_units": len(pairs), **pair_contrasts(pairs, name, first, second)}
    nat = {arm: evs[arm]["aggregate"]["natural"] for arm in run.ARMS}
    return {
        "experiment_id": run.EXPERIMENT_ID, "phase": evs["jev"]["phase"],
        "bootstrap": {"seed": v2an.BOOT_SEED, "resamples": v2an.BOOT_N, "cluster": "instance"},
        "pairings": out,
        "arm_summary": {SLOT_NAMES[a]: arm_summary(evs[a]["rows"]) for a in run.ARMS},
        "transfer_classification": {"J_vs_B": transfer(nat["jev"], nat["b"]), "C_vs_B": transfer(nat["control"], nat["b"]),
                                    "J_vs_C": transfer(nat["jev"], nat["control"]),
                                    "note": "No auxiliary overhead in v3a: OVERHEAD_ABSORPTION is not testable here; "
                                            "speed/cost compare different providers (reference values only)."},
        "replication_of_v2_primary": replication(out["C_vs_J"]),
        "interpretation_guards": [
            "B is an analogue, not the paper's B; B-vs-C is an interface contrast, C-vs-J a decision-model contrast, "
            "J-vs-B must not be attributed to Jev alone.",
            "A decision-level (speed/token) advantage is not an agent advantage unless delivered-success metrics agree.",
            "Both compared cells near 0% or 100% means non-discriminating, not support.",
            "B rows for the three order_idx values are independent replicates, not order conditions.",
        ],
        "claim_scope": run.CLAIM_SCOPE,
    }


# ------------------------------------------------------------------ verification
def verify_arm(ev: dict) -> list[str]:
    errs: list[str] = []
    req = lambda cond, msg: None if cond else errs.append(msg)  # noqa: E731
    arm, phase = ev.get("arm"), ev.get("phase")
    req(ev.get("experiment_id") == run.EXPERIMENT_ID, "experiment_id mismatch")
    req(arm in run.ARMS and phase in ("pilot", "test"), "bad arm/phase")
    if errs:
        return errs
    req(ev.get("execution_environment") == "local", "execution_environment must be local")
    req(ev.get("claim_scope") == run.CLAIM_SCOPE, "claim_scope altered")
    req(ev.get("generator_version") == run.gen.GENERATOR_VERSION, "generator version must be the frozen g2")
    req(ev.get("arm_label") == run.ARM_LABEL[arm], "arm label altered")
    if phase == "test":
        req(run.FREEZE_SHA256 is not None and ev.get("freeze_sha256") == run.FREEZE_SHA256,
            "test evidence does not match the pinned v3a freeze hash")
        req(ev.get("v2_freeze_sha256") == run.v2run.FREEZE_SHA256, "test evidence does not match the v2 pin")
    blob = json.dumps(ev)
    for pat in v2an.SECRET_PATTERNS:
        req(not pat.search(blob), f"credential-like content matches /{pat.pattern}/")
    ident = ev.get("identity", {})
    req(ident.get("resolved_model") == run.RESOLVED[arm], "identity.resolved_model != pinned model")
    if arm == "jev":
        for probe in ("pinned_probe", "alias_probe"):
            req(set((ident.get(probe) or {}).get("headers", {})) <= run.v1.KEPT_HEADERS, "non-allowlisted headers")
    rows = ev.get("rows", [])
    if ev.get("status") == "COMPLETED":
        req(len(rows) == ev.get("expected_rows") == run.expected_rows(phase), "row count != expected")
    insts = {w["id"]: w for w in run.instances_for(phase)}
    seen = set()
    for r in rows:
        k = v2an._key(r)
        req(k not in seen, f"duplicate row {k}")
        seen.add(k)
        wf = insts.get(r["workflow_id"])
        req(wf is not None and wf["family"] == r["family"], f"row not from the {phase} generator: {r['workflow_id']}")
        req(r["arm"] == arm, "row arm mismatch")
        req(not [x for x in r if x.startswith("jev_")], "arm-specific field names in a row")
        if wf:
            order_list = list(core.build_criteria(wf, r["order_idx"]))
            req(r["truth_pos"] == order_list.index(core.truth_at_start(wf))
                and r["trap_pos"] == order_list.index(wf["trap"]), f"position record mismatch {k}")
            req(r["start_distance"] == core.distance_to_goal(wf, core.MachineV2(wf).state, []),
                f"start_distance mismatch {k}")
        req(r["number_of_steps"] <= r["step_budget"], f"budget exceeded {k}")
    if rows:
        req(v2an._close(ev.get("aggregate"), run.v2run.aggregate(rows)), "aggregate does not match rows")
    req(ev.get("spend_usd", 0) <= ev.get("spend_cap_usd", 0) * 1.05 + 1e-9, "spend exceeds cap")
    req(ev.get("spend_cap_usd", 0) <= run.ARM_CAP_USD[arm] + 1e-9, "spend cap above the per-arm cap")
    return errs


def verify_analysis(an: dict, evs: dict) -> list[str]:
    if any(evs[a].get("status") != "COMPLETED" for a in run.ARMS):
        return ["analysis requires COMPLETED evidence for all three arms"]
    return [] if v2an._close(an, analyze(evs)) else ["analysis does not match recomputation from the evidence files"]


def verify_dir(evidence_dir: Path = EVIDENCE) -> dict:
    """Files: jev_v3a_<tag>_{jev,control,b}.result.json and jev_v3a_<tag>_analysis.json (tags: pilot, test)."""
    report, errors = {}, []
    tags = sorted({p.name.split("_")[2] for p in evidence_dir.glob("jev_v3a_*_*.json")}) if evidence_dir.exists() else []
    for tag in tags:
        evs = {}
        for arm in run.ARMS:
            path = evidence_dir / f"jev_v3a_{tag}_{arm}.result.json"
            if path.exists():
                evs[arm] = json.loads(path.read_text())
                errs = verify_arm(evs[arm])
                report[f"{tag}_{arm}"] = "OK" if not errs else errs
                errors += errs
        ap = evidence_dir / f"jev_v3a_{tag}_analysis.json"
        if ap.exists():
            errs = (verify_analysis(json.loads(ap.read_text()), evs) if len(evs) == len(run.ARMS)
                    else ["analysis present without all three arm evidence files"])
            report[f"{tag}_analysis"] = "OK" if not errs else errs
            errors += errs
    status = "NOT_RUN" if not report else ("EVIDENCE_VERIFIED" if not errors else "EVIDENCE_INVALID")
    return {"status": status, "report": report}


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("jev"), ap.add_argument("control"), ap.add_argument("b"), ap.add_argument("--out")  # noqa: B018
    args = ap.parse_args(argv)
    evs = {a: json.loads(Path(p).read_text()) for a, p in (("jev", args.jev), ("control", args.control), ("b", args.b))}
    errs = [e for ev in evs.values() for e in verify_arm(ev)]
    if errs:
        print(json.dumps({"status": "EVIDENCE_INVALID", "errors": errs}, indent=2))
        return 1
    an = analyze(evs)
    text = json.dumps(an, indent=2, sort_keys=True)
    if args.out:
        Path(args.out).write_text(text + "\n")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
