"""Derived, deterministic closure metrics from raw jev-live-systemone-check evidence (offline, no keys).

Not part of any freeze: it only re-expresses committed rows (no new measurement, no change to the frozen
analysis). Per arm and per family, in the layout asked for by the lightweight-closure directive.

    python jev_closure_metrics.py --prefix jev_v3a_test --arms jev control b --out ../evidence/jev_v3a_test_metrics.json
    python jev_closure_metrics.py --prefix jev_v3a_test --arms jev control b --check ../evidence/jev_v3a_test_metrics.json

Caveats recorded in the output: per-call latencies are not stored in the rows, so `median_decision_latency_s`
is the median over episodes of the per-episode mean call latency (not a per-call median); Jev cost is
tokens x an assumed price; cost/time per success keep failures in the numerator.
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EVIDENCE = HERE.parent / "evidence"
CAVEATS = [
    "median_decision_latency_s = median over episodes of (episode decision latency / episode selector calls); "
    "per-call latencies are not stored in the rows.",
    "Jev cost = input tokens x assumed US$0.042/Mtok (the API returns no cost field); other arms use list prices.",
    "cost_per_success and time_per_success keep failures in the numerator (total over all episodes / successes).",
    "recovery_success_rate = final success on forced_trap episodes of the eight recoverable families "
    "(irreversible is the negative control and excluded); recovery_success_among_deviations is also given.",
    "Auxiliary cost/time columns appear only when rows carry aux fields (v3b).",
]


def _rate(n, d):
    return None if d == 0 else n / d


def _is(r, t):
    return r["episode_type"] == t


def metrics(rows: list[dict]) -> dict:
    nat = [r for r in rows if _is(r, "natural")]
    forced_rec = [r for r in rows if _is(r, "forced_trap") and r["family"] != "irreversible"]
    calls = sum(r["n_selector_calls"] for r in rows)
    lat = sum(r["decision_latency_total_s"] for r in rows)
    succ = sum(bool(r["final_success"]) for r in rows)
    dev = [r for r in rows if r["deviation_events"] > 0]
    cost = sum(r["cost_usd"] for r in rows)
    wall = sum(r["workflow_latency_total_s"] for r in rows)
    per_ep = [r["decision_latency_total_s"] / r["n_selector_calls"] for r in rows if r["n_selector_calls"]]
    out = {
        "episode_count": len(rows),
        "natural_episode_count": len(nat),
        "forced_trap_recoverable_episode_count": len(forced_rec),
        "infrastructure_failures": sum(bool(r["infrastructure_failure"]) for r in rows),
        "invalid_responses": sum(r["invalid_responses"] for r in rows),
        "initial_choice_accuracy": _rate(sum(r["initial_choice_correct"] is True for r in nat), len(nat)),
        "recovery_success_rate": _rate(sum(bool(r["final_success"]) for r in forced_rec), len(forced_rec)),
        "recovery_success_among_deviations": _rate(sum(bool(r["recovery_success"]) for r in dev), len(dev)),
        "final_success_rate": _rate(succ, len(rows)),
        "final_success_rate_natural": _rate(sum(bool(r["final_success"]) for r in nat), len(nat)),
        "premature_completion_rate": _rate(sum(bool(r["premature_completion"]) for r in rows), len(rows)),
        "selector_calls": calls,
        "mean_decision_latency_s": _rate(lat, calls),
        "median_decision_latency_s": statistics.median(per_ep) if per_ep else None,
        "total_input_tokens": sum(r["usage"]["input_tokens"] for r in rows),
        "total_output_tokens": sum(r["usage"]["output_tokens"] for r in rows),
        "decision_cost_usd": cost,
        "cost_per_success_usd": _rate(cost, succ),
        "time_per_success_s": _rate(wall, succ),
    }
    if rows and "aux_cost_usd" in rows[0]:
        aux_cost = sum(r["aux_cost_usd"] for r in rows)
        aux_lat = sum(r["aux_latency_total_s"] for r in rows)
        out |= {"aux_latency_total_s": aux_lat, "aux_cost_usd": aux_cost,
                "aux_input_tokens": sum(r["aux_usage"]["input_tokens"] for r in rows),
                "aux_output_tokens": sum(r["aux_usage"]["output_tokens"] for r in rows),
                "total_cost_usd": cost + aux_cost, "total_cost_per_success_usd": _rate(cost + aux_cost, succ),
                "aux_share_of_task_time": _rate(aux_lat, wall)}
    return out


def family_metrics(rows: list[dict]) -> dict:
    out = {}
    for fam in sorted({r["family"] for r in rows}):
        fr = [r for r in rows if r["family"] == fam]
        nat = [r for r in fr if _is(r, "natural")]
        forced = [r for r in fr if _is(r, "forced_trap")]
        out[fam] = {
            "N_instances": len({r["workflow_id"] for r in fr}), "N_episodes": len(fr),
            "initial_choice_accuracy": _rate(sum(r["initial_choice_correct"] is True for r in nat), len(nat)),
            "recovery_final_success_forced_trap": _rate(sum(bool(r["final_success"]) for r in forced), len(forced)),
            "final_success_natural": _rate(sum(bool(r["final_success"]) for r in nat), len(nat)),
        }
    return out


def build(prefix: str, arms: list[str], evidence_dir: Path = EVIDENCE) -> dict:
    out = {"source": prefix, "caveats": CAVEATS, "arms": {}}
    for arm in arms:
        ev = json.loads((evidence_dir / f"{prefix}_{arm}.result.json").read_text())
        out["arms"][arm] = {"status": ev["status"], "resolved_model": ev["identity"].get("resolved_model"),
                            "overall": metrics(ev["rows"]), "by_family": family_metrics(ev["rows"])}
    return out


def _close(a, b):
    if isinstance(a, dict):
        return isinstance(b, dict) and a.keys() == b.keys() and all(_close(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return isinstance(b, list) and len(a) == len(b) and all(_close(x, y) for x, y in zip(a, b, strict=True))
    if isinstance(a, float) or isinstance(b, float):
        return a is not None and b is not None and abs(a - b) <= 1e-9 * max(1.0, abs(a), abs(b))
    return a == b


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prefix", required=True)
    ap.add_argument("--arms", nargs="+", required=True)
    ap.add_argument("--out")
    ap.add_argument("--check")
    args = ap.parse_args(argv)
    built = build(args.prefix, args.arms)
    if args.check:
        ok = _close(json.loads(Path(args.check).read_text()), built)
        print(json.dumps({"status": "METRICS_MATCH" if ok else "METRICS_MISMATCH"}))
        return 0 if ok else 1
    text = json.dumps(built, indent=2, sort_keys=True)
    if args.out:
        Path(args.out).write_text(text + "\n")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
