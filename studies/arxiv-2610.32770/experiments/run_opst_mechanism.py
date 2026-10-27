"""Run the frozen OPST mechanism evaluations and write result/Evidence JSON.

Usage (from repository root):
    python studies/arxiv-2610.32770/experiments/run_opst_mechanism.py [--write]

Without --write the result is printed only. Acceptance criteria are fixed in
studies/arxiv-2610.32770/manifest.yaml (pre-registered before the first run).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STUDY = HERE.parent
ROOT = STUDY.parents[1]
sys.path.insert(0, str(HERE))

import opst_mechanism as m  # noqa: E402

ALPHA_PAPER = 0.8
# Strictly positive pair for limit checks; near-degenerate pair for the bound check.
P_POS, Q_POS = [0.7, 0.2, 0.1], [0.1, 0.3, 0.6]
P_SHARP, Q_SHARP = [1 - 2e-9, 1e-9, 1e-9], [1e-9, 1e-9, 1 - 2e-9]
ALPHA_SWEEP = [1e-3, 1e-2, 0.2, 0.5, 0.8, 0.99, 0.999]
ALPHA_TO_0 = [0.2, 0.05, 0.01, 1e-3, 1e-4]
ALPHA_TO_1 = [0.8, 0.95, 0.99, 0.999, 0.9999]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _strictly_decreasing(xs: list[float]) -> bool:
    return all(b < a for a, b in zip(xs, xs[1:]))


def objective_properties(div) -> dict:
    fwd, rev = m.kl(Q_POS, P_POS), m.kl(P_POS, Q_POS)
    err0 = [abs(div(P_POS, Q_POS, a) / a - fwd) for a in ALPHA_TO_0]
    err1 = [abs(div(P_POS, Q_POS, a) / (1 - a) - rev) for a in ALPHA_TO_1]
    bound_rows = []
    for p, q, name in ((P_POS, Q_POS, "positive"), (P_SHARP, Q_SHARP, "near_degenerate")):
        for a in ALPHA_SWEEP:
            d = div(p, q, a)
            bound_rows.append({"pair": name, "alpha": a, "d": d, "h_alpha": m.binary_entropy(a), "within_bound": 0 <= d <= m.binary_entropy(a) + 1e-12})
    limit0 = _strictly_decreasing(err0) and err0[-1] / fwd < 1e-2
    limit1 = _strictly_decreasing(err1) and err1[-1] / rev < 1e-2
    bounded = all(r["within_bound"] for r in bound_rows)
    return {
        "forward_kl_q_p": fwd,
        "reverse_kl_p_q": rev,
        "alpha_to_0": {"alphas": ALPHA_TO_0, "abs_error_d_over_alpha_vs_forward_kl": err0, "holds": limit0},
        "alpha_to_1": {"alphas": ALPHA_TO_1, "abs_error_d_over_1_minus_alpha_vs_reverse_kl": err1, "holds": limit1},
        "bounded_by_h_alpha": {"rows": bound_rows, "violations": sum(not r["within_bound"] for r in bound_rows), "holds": bounded},
        "d_at_paper_alpha_positive_pair": div(P_POS, Q_POS, ALPHA_PAPER),
        "all_stated_properties_hold": limit0 and limit1 and bounded,
    }


def c1_objective() -> dict:
    printed = objective_properties(m.d_alpha_printed)
    consistent = objective_properties(m.d_alpha_consistent)
    passed = consistent["all_stated_properties_hold"]
    return {
        "claim_id": "C1-objective-semantics",
        "printed_form": printed,
        "gkd_consistent_form": consistent,
        "printed_form_matches_stated_properties": printed["all_stated_properties_hold"],
        "verdict": "PASS" if passed else "FAIL",
    }


def c2_selection() -> dict:
    fixture = json.loads((STUDY / "fixtures" / "opst_selection_v1.json").read_text())
    seen = {m.normalize_question(q) for q in fixture["prior_round_questions"]}
    decisions = m.select_samples(fixture["samples"], seen)
    rows = []
    for s, d in zip(fixture["samples"], decisions, strict=True):
        rows.append({**d, "expected": s["expected"], "match": d["reason"] == s["expected"]})
    kept_wrong = [s["id"] for s, d in zip(fixture["samples"], decisions, strict=True) if d["keep"] and "ground_truth_answer" in s and s["ground_truth_answer"] != s["candidate_answer"]]
    matched = sum(r["match"] for r in rows)
    return {
        "claim_id": "C2-sample-selection",
        "evaluation_id": fixture["evaluation_id"],
        "cases": len(rows),
        "matched": matched,
        "rows": rows,
        "kept_count": sum(r["keep"] for r in rows),
        "kept_with_wrong_candidate_answer": kept_wrong,
        "verdict": "PASS" if matched == len(rows) else "FAIL",
    }


def c3_ema() -> dict:
    theta0 = [0.0, 1.0]
    target = [1.0, -1.0]
    rounds = [[target] * 5, [target] * 5]
    no_ema = m.run_rounds(theta0, rounds, beta=1.0)
    ema = m.run_rounds(theta0, rounds, beta=0.05)
    k = ema["ema_updates"]
    closed_form = [t + (1 - 0.05) ** k * (a - t) for a, t in zip(theta0, target, strict=True)]
    err = max(abs(x - y) for x, y in zip(ema["returned"], closed_form, strict=True))
    checks = {
        "beta_1_teacher_equals_student": no_ema["returned"] == no_ema["student"],
        "updates_per_gradient_step": k == 10,
        "carry_over_closed_form_max_abs_error": err,
        "carry_over_matches_closed_form": err < 1e-12,
        "returned_model_is_teacher_not_student": ema["returned"] != ema["student"],
    }
    passed = all(v for key, v in checks.items() if key != "carry_over_closed_form_max_abs_error")
    return {"claim_id": "C3-ema-teacher", "checks": checks, "returned": ema["returned"], "verdict": "PASS" if passed else "FAIL"}


def c4_loss() -> dict:
    a, b = [0.6, 0.4], [0.3, 0.7]
    pad = [0.5, 0.5]
    short = ([[a]], [[b]], [[1]])
    padded = ([[a, pad, pad]], [[b, [0.9, 0.1], [0.1, 0.9]]], [[1, 0, 0]])
    per_token = m.d_alpha_consistent(a, b, ALPHA_PAPER)
    l_short = m.opst_loss(*short, ALPHA_PAPER)
    l_padded = m.opst_loss(*padded, ALPHA_PAPER)
    # Two samples of different length: each sample contributes 1/B.
    student = [[a], [a, a, a, a]]
    teacher = [[b], [a, a, a, a]]
    mask = [[1], [1, 1, 1, 1]]
    l_batch = m.opst_loss(student, teacher, mask, ALPHA_PAPER)
    checks = {
        "padding_invariant": abs(l_short - l_padded) < 1e-15,
        "per_sample_mean_then_batch_mean": abs(l_batch - per_token / 2) < 1e-15,
        "token_pooled_value_would_be": per_token / 5,
    }
    passed = checks["padding_invariant"] and checks["per_sample_mean_then_batch_mean"]
    return {"claim_id": "C4-loss-aggregation", "checks": checks, "verdict": "PASS" if passed else "FAIL"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="write result and Evidence JSON into evidence/")
    args = parser.parse_args()

    impl = HERE / "opst_mechanism.py"
    fixture = STUDY / "fixtures" / "opst_selection_v1.json"
    hashes = {
        "implementation_sha256": _sha256(impl),
        "runner_sha256": _sha256(Path(__file__)),
        "fixture_sha256": _sha256(fixture),
    }
    claims = [c1_objective(), c2_selection(), c3_ema(), c4_loss()]
    result = {
        "study_id": "arxiv-2610.32770",
        "run_id": "opst-mechanism-v1",
        "frozen_evaluations": ["opst-objective-semantics-v1", "opst-sample-selection-v1", "opst-ema-loss-semantics-v1"],
        "environment": {"python": platform.python_version(), "implementation": platform.python_implementation(), "dependencies": "standard library only"},
        "artifact_hashes": hashes,
        "paper_alpha": ALPHA_PAPER,
        "claims": claims,
        "not_paper_evidence": "Deterministic mechanism checks only. No model, benchmark or paper-level accuracy was run.",
    }
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.write:
        out = STUDY / "evidence"
        (out / "opst_mechanism_v1.result.json").write_text(text)
        notes = {
            "C1-objective-semantics": "Printed Sec. 3.5 mixture weights do not satisfy the paper's own stated limits and H(alpha) bound; the GKD-consistent form does. Downstream analogues use the consistent form as a ReproForge interpretation.",
            "C2-sample-selection": "Frozen synthetic fixture. The gate retains zero-consensus samples, and a consistently reproduced wrong candidate answer passes both filters (boundary result).",
            "C3-ema-teacher": "Weight bookkeeping of Algorithm 1 on toy vectors; EMA per gradient step, carry-over across rounds, teacher returned.",
            "C4-loss-aggregation": "Masked per-sample token mean followed by batch mean; padding-invariant.",
        }
        for c in claims:
            metrics = {k: v for k, v in c.items() if k not in ("claim_id", "verdict", "rows", "printed_form", "gkd_consistent_form")}
            if c["claim_id"] == "C1-objective-semantics":
                metrics = {
                    "printed_form_matches_stated_properties": c["printed_form_matches_stated_properties"],
                    "printed_limit_alpha_to_0_holds": c["printed_form"]["alpha_to_0"]["holds"],
                    "printed_limit_alpha_to_1_holds": c["printed_form"]["alpha_to_1"]["holds"],
                    "printed_bound_violations": c["printed_form"]["bounded_by_h_alpha"]["violations"],
                    "consistent_all_properties_hold": c["gkd_consistent_form"]["all_stated_properties_hold"],
                }
            evidence = {
                "claim_id": c["claim_id"],
                "run_id": "opst-mechanism-v1",
                "artifact_hashes": hashes,
                "metrics": metrics,
                "verdict": c["verdict"],
                "notes": notes[c["claim_id"]],
            }
            (out / f"{c['claim_id'].split('-')[0]}.{c['claim_id'].split('-', 1)[1]}.evidence.json").write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    sys.stdout.write(text)
    return 0 if all(c["verdict"] == "PASS" for c in claims) else 1


if __name__ == "__main__":
    raise SystemExit(main())
