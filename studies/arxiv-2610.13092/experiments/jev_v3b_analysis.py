"""Analysis and integrity verification for jev-live-systemone-check-v3b (offline, no keys).

Cells are (arm, overhead level) with arm in {jev, control, b} and level in {O0, O1}. Transfer classes use the
frozen audit rule (`classify_transfer`), separately for time and for cost, on natural episodes with failures in
the numerator. Paired contrasts use the v2/v3a machinery (instance-cluster bootstrap, exact McNemar).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import jev_closure_metrics as cm  # noqa: E402
import jev_v2_analysis as v2an  # noqa: E402
import jev_v2_core as core  # noqa: E402
import jev_v3_analysis as v3an  # noqa: E402
import jev_v3b_run as run  # noqa: E402

EVIDENCE = HERE.parent / "evidence"
audit = v2an.audit
PAIRINGS = v3an.PAIRINGS            # name -> (first arm, second arm); diff = second - first
SLOT = v3an.SLOT_NAMES


def _nat(rows):
    return [r for r in rows if r["episode_type"] == "natural"]


def _tot(rows):
    n, succ = len(rows), sum(bool(r["final_success"]) for r in rows)
    calls = sum(r["n_selector_calls"] for r in rows)
    dec_cost = sum(r["cost_usd"] for r in rows)
    aux_cost = sum(r["aux_cost_usd"] for r in rows)
    wall = sum(r["workflow_latency_total_s"] for r in rows)
    aux_t = sum(r["aux_latency_total_s"] for r in rows)
    return {
        "n": n, "success": succ,
        "decision_latency_per_call": sum(r["decision_latency_total_s"] for r in rows) / calls if calls else None,
        "task_latency_per_attempt": wall / n if n else None,
        "time_per_success": wall / succ if succ else None,
        "decision_cost_per_call": dec_cost / calls if calls else None,
        "task_cost_per_attempt": (dec_cost + aux_cost) / n if n else None,
        "cost_per_success": (dec_cost + aux_cost) / succ if succ else None,
        "aux_share_of_task_time": aux_t / wall if wall else None,
        "aux_share_of_task_cost": aux_cost / (dec_cost + aux_cost) if dec_cost + aux_cost else None,
    }


def _classify(new: dict, base: dict, keys: tuple) -> dict | None:
    if any(not new[k] or not base[k] for k in keys):
        return None
    vals = [audit.pct_change(new[k], base[k]) for k in keys]
    return {"pct_change": dict(zip(("decision", "task", "delivered"), vals, strict=True)),
            "class": audit.classify_transfer(*vals)}


def transfer(rows_new: list[dict], rows_base: list[dict]) -> dict:
    a, b = _tot(_nat(rows_new)), _tot(_nat(rows_base))
    return {
        "time": _classify(a, b, ("decision_latency_per_call", "task_latency_per_attempt", "time_per_success")),
        "cost": _classify(a, b, ("decision_cost_per_call", "task_cost_per_attempt", "cost_per_success")),
        "new_success_natural": f"{a['success']}/{a['n']}", "base_success_natural": f"{b['success']}/{b['n']}",
    }


def _relabel(out: dict, a: str, b: str) -> dict:
    out = dict(out)
    for old, new in (("jev", a), ("control", b), ("diff_control_minus_jev", f"diff_{b}_minus_{a}")):
        if old in out:
            out[new] = out.pop(old)
    if "mcnemar" in out:
        m = out["mcnemar"]
        out["mcnemar"] = {f"{a}_only": m["jev_only"], f"{b}_only": m["control_only"],
                          "p_exact_two_sided": m["p_exact_two_sided"]}
    return out


def aux_effect(rows_o0: list[dict], rows_o1: list[dict], arm: str) -> dict:
    """O1 vs O0 on identical (instance, order, episode type) units: did the auxiliary stage change success?"""
    pairs = v2an.pair_rows(rows_o0, rows_o1)
    nat = lambda r: r["episode_type"] == "natural"  # noqa: E731
    rec = lambda r: r["episode_type"] == "forced_trap"  # noqa: E731
    one = lambda r: 1  # noqa: E731
    fin = lambda r: 1 if r["final_success"] else 0  # noqa: E731
    return {"final_success__natural": _relabel(v2an.contrast(f"aux_{arm}:final_success__natural", pairs, nat, fin, one,
                                                              True), "O0", "O1"),
            "final_success__forced_trap": _relabel(v2an.contrast(f"aux_{arm}:final_success__forced_trap", pairs, rec,
                                                                 fin, one, True), "O0", "O1")}


def analyze(evs: dict) -> dict:
    """evs[(arm, level)] = evidence dict."""
    rows = {k: v["rows"] for k, v in evs.items()}
    out = {"pairings": {}, "transfer": {}, "aux_effect": {}, "cells": {}}
    for level in run.LEVELS:
        for name, (first, second) in PAIRINGS.items():
            pairs = v2an.pair_rows(rows[(first, level)], rows[(second, level)])
            out["pairings"][f"{name}@{level}"] = {"n_paired_units": len(pairs),
                                                  **v3an.pair_contrasts(pairs, f"{name}@{level}", first, second)}
            # transfer: the faster/cheaper-per-decision candidate is `new`; base is the reference arm
            new, base = {"C_vs_J": ("jev", "control"), "C_vs_B": ("control", "b"), "J_vs_B": ("jev", "b")}[name]
            out["transfer"][f"{SLOT[new]}_vs_{SLOT[base]}@{level}"] = transfer(rows[(new, level)], rows[(base, level)])
    for arm in run.ARMS:
        out["aux_effect"][SLOT[arm]] = aux_effect(rows[(arm, "O0")], rows[(arm, "O1")], SLOT[arm])
    for (arm, level), r in sorted(rows.items()):
        out["cells"][f"{SLOT[arm]}@{level}"] = {"overall": cm.metrics(r), "by_family": cm.family_metrics(r),
                                                "transfer_inputs_natural": _tot(_nat(r))}
    return {
        "experiment_id": run.EXPERIMENT_ID, "phase": "test", "families": list(run.FAMILIES),
        "bootstrap": {"seed": v2an.BOOT_SEED, "resamples": v2an.BOOT_N, "cluster": "instance"},
        **out,
        "classification_rule": "frozen audit classify_transfer: NO_LOCAL_SAVING if decision delta >= 0; else "
                               "OVERHEAD_ABSORPTION if task delta >= 0; else DELIVERY_PARADOX if delivered delta >= 0; "
                               "else TRANSFERRED. Deltas are the new arm relative to the base arm (negative = saving).",
        "interpretation_guards": [
            "A decision-level advantage is not an agent advantage unless delivered-success metrics agree.",
            "Both compared cells near 0% or 100% means non-discriminating, not support.",
            "Speed/cost compare different providers (reference values); Jev cost = tokens x assumed price.",
            "The auxiliary stage is a T3A-style analogue, not the paper's; B is an analogue, not the paper's B.",
        ],
        "claim_scope": run.CLAIM_SCOPE,
    }


# ------------------------------------------------------------------ verification
def verify_cell(ev: dict) -> list[str]:
    errs: list[str] = []
    req = lambda cond, msg: None if cond else errs.append(msg)  # noqa: E731
    arm, level, phase = ev.get("arm"), ev.get("overhead"), ev.get("phase")
    req(ev.get("experiment_id") == run.EXPERIMENT_ID, "experiment_id mismatch")
    req(arm in run.ARMS and level in run.LEVELS and phase == "test", "bad arm/overhead/phase")
    if errs:
        return errs
    req(ev.get("execution_environment") == "local", "execution_environment must be local")
    req(ev.get("claim_scope") == run.CLAIM_SCOPE, "claim_scope altered")
    req(ev.get("generator_version") == gen_version() and ev.get("families") == list(run.FAMILIES), "generator/families")
    req(ev.get("arm_label") == run.v3run.ARM_LABEL[arm], "arm label altered")
    req(run.FREEZE_SHA256 is not None and ev.get("freeze_sha256") == run.FREEZE_SHA256,
        "evidence does not match the pinned v3b freeze hash")
    req(ev.get("v3a_freeze_sha256") == run.v3run.FREEZE_SHA256 and ev.get("v2_freeze_sha256") == run.v2run.FREEZE_SHA256,
        "evidence does not match the v2/v3a pins")
    blob = json.dumps(ev)
    for pat in v2an.SECRET_PATTERNS:
        req(not pat.search(blob), f"credential-like content matches /{pat.pattern}/")
    ident = ev.get("identity", {})
    req(ident.get("resolved_model") == run.v3run.RESOLVED[arm], "identity.resolved_model != pinned model")
    if level == "O1":
        req((ident.get("aux_identity") or {}).get("resolved_model") == run.auxarms.AUX_MODEL, "aux model not pinned")
    if arm == "jev":
        for probe in ("pinned_probe", "alias_probe"):
            req(set((ident.get(probe) or {}).get("headers", {})) <= run.v1.KEPT_HEADERS, "non-allowlisted headers")
    rows = ev.get("rows", [])
    if ev.get("status") == "COMPLETED":
        req(len(rows) == ev.get("expected_rows") == run.expected_rows("test"), "row count != expected")
    insts = {w["id"]: w for w in run.instances_for("test")}
    seen = set()
    for r in rows:
        k = v2an._key(r)
        req(k not in seen, f"duplicate row {k}")
        seen.add(k)
        wf = insts.get(r["workflow_id"])
        req(wf is not None and wf["family"] == r["family"], f"row not from the test generator: {r['workflow_id']}")
        req(r["arm"] == arm and r.get("overhead") == level, "row arm/overhead mismatch")
        req(not [x for x in r if x.startswith("jev_")], "arm-specific field names in a row")
        action_calls = r["n_selector_calls"] - r["verification_calls"]
        if level == "O0":
            req(r["aux_calls"] == 0 and r["aux_cost_usd"] == 0, f"aux fields set in an O0 row {k}")
        else:
            req(r["aux_calls"] >= action_calls, f"aux calls fewer than action decisions {k}")
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
    req(ev.get("aux_spend_usd", 0) <= ev.get("aux_spend_cap_usd", 0) * 1.05 + 1e-9, "aux spend exceeds cap")
    req(ev.get("spend_cap_usd", 0) <= run.CELL_CAP_USD[arm] + 1e-9, "spend cap above the per-cell cap")
    return errs


def gen_version() -> str:
    return run.gen.GENERATOR_VERSION


def verify_analysis(an: dict, evs: dict) -> list[str]:
    if len(evs) != len(run.ARMS) * len(run.LEVELS) or any(e.get("status") != "COMPLETED" for e in evs.values()):
        return ["analysis requires COMPLETED evidence for all six cells"]
    return [] if v2an._close(an, analyze(evs)) else ["analysis does not match recomputation from the evidence files"]


def load_cells(evidence_dir: Path = EVIDENCE) -> dict:
    evs = {}
    for arm in run.ARMS:
        for level in run.LEVELS:
            p = evidence_dir / f"jev_v3b_test_{arm}_{level}.result.json"
            if p.exists():
                evs[(arm, level)] = json.loads(p.read_text())
    return evs


def verify_dir(evidence_dir: Path = EVIDENCE) -> dict:
    report, errors = {}, []
    evs = load_cells(evidence_dir)
    for (arm, level), ev in sorted(evs.items()):
        errs = verify_cell(ev)
        report[f"test_{arm}_{level}"] = "OK" if not errs else errs
        errors += errs
    ap = evidence_dir / "jev_v3b_test_analysis.json"
    if ap.exists():
        errs = verify_analysis(json.loads(ap.read_text()), evs)
        report["test_analysis"] = "OK" if not errs else errs
        errors += errs
    status = "NOT_RUN" if not report else ("EVIDENCE_VERIFIED" if not errors else "EVIDENCE_INVALID")
    return {"status": status, "report": report}


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--out")
    args = ap.parse_args(argv)
    evs = load_cells()
    errs = [e for ev in evs.values() for e in verify_cell(ev)]
    if errs or len(evs) != len(run.ARMS) * len(run.LEVELS):
        print(json.dumps({"status": "EVIDENCE_INVALID_OR_INCOMPLETE", "errors": errs, "cells": len(evs)}, indent=2))
        return 1
    an = analyze(evs)
    text = json.dumps(an, indent=2, sort_keys=True)
    if args.out:
        Path(args.out).write_text(text + "\n")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
