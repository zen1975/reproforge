"""Offline checks for the derived closure metrics (no keys, no network)."""
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "studies" / "arxiv-2610.13092" / "experiments"
sys.path.insert(0, str(EXP))
spec = importlib.util.spec_from_file_location("jev_closure_metrics", EXP / "jev_closure_metrics.py")
cm = importlib.util.module_from_spec(spec)
sys.modules["jev_closure_metrics"] = cm
spec.loader.exec_module(cm)


def row(fam, typ, ok, init=True, calls=2, lat=1.0, cost=0.001, wall=2.0, infra=False, invalid=0, dev=0):
    return {"family": fam, "episode_type": typ, "final_success": ok, "initial_choice_correct": init if typ == "natural" else None,
            "n_selector_calls": calls, "decision_latency_total_s": lat, "cost_usd": cost, "workflow_latency_total_s": wall,
            "infrastructure_failure": infra, "invalid_responses": invalid, "deviation_events": dev,
            "recovery_success": bool(dev and ok), "premature_completion": False, "workflow_id": f"{fam}-1",
            "usage": {"input_tokens": 100, "output_tokens": 10}}


def test_metrics_keep_failures_in_numerators_and_split_recovery_from_the_negative_control():
    rows = [row("anchor", "natural", True), row("injected", "natural", False, init=False, dev=1),
            row("injected", "forced_trap", True, dev=1), row("irreversible", "forced_trap", False, dev=1)]
    m = cm.metrics(rows)
    assert m["episode_count"] == 4 and m["natural_episode_count"] == 2
    assert m["initial_choice_accuracy"] == 0.5 and m["recovery_success_rate"] == 1.0  # irreversible excluded
    assert m["final_success_rate"] == 0.5 and abs(m["cost_per_success_usd"] - 0.004 / 2) < 1e-12
    assert m["time_per_success_s"] == 8.0 / 2 and m["total_input_tokens"] == 400
    assert m["median_decision_latency_s"] == 0.5 and m["mean_decision_latency_s"] == 0.5
    assert "aux_cost_usd" not in m


def test_family_metrics_and_aux_columns():
    rows = [dict(row("injected", "natural", True), aux_cost_usd=0.002, aux_latency_total_s=1.0,
                 aux_usage={"input_tokens": 50, "output_tokens": 20})]
    assert cm.metrics(rows)["total_cost_usd"] == 0.003 and cm.metrics(rows)["aux_share_of_task_time"] == 0.5
    fm = cm.family_metrics([row("injected", "natural", True), row("injected", "forced_trap", False)])
    assert fm["injected"]["N_episodes"] == 2 and fm["injected"]["recovery_final_success_forced_trap"] == 0.0


def test_check_mode_detects_a_changed_file(tmp_path, monkeypatch):
    ev = {"status": "COMPLETED", "identity": {"resolved_model": "m"}, "rows": [row("anchor", "natural", True)]}
    (tmp_path / "p_x.result.json").write_text(json.dumps(ev))
    monkeypatch.setattr(cm, "EVIDENCE", tmp_path)
    built = cm.build("p", ["x"], tmp_path)
    good = tmp_path / "m.json"
    good.write_text(json.dumps(built))
    assert cm._close(json.loads(good.read_text()), built)
    built["arms"]["x"]["overall"]["episode_count"] = 99
    assert not cm._close(json.loads(good.read_text()), built)
