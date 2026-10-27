import importlib.util
import json
import math
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT / "studies" / "arxiv-2610.32770"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


m = _load("opst_mechanism", STUDY / "experiments" / "opst_mechanism.py")
runner = _load("run_opst_mechanism", STUDY / "experiments" / "run_opst_mechanism.py")


def test_kl_basics():
    assert m.kl([0.5, 0.5], [0.5, 0.5]) == 0.0
    assert m.kl([1.0, 0.0], [0.5, 0.5]) == pytest.approx(math.log(2))
    assert m.kl([0.5, 0.5], [1.0, 0.0]) == math.inf
    with pytest.raises(ValueError):
        m.kl([0.5, 0.6], [0.5, 0.5])


def test_divergences_vanish_on_identical_distributions():
    p = [0.2, 0.3, 0.5]
    for a in (0.1, 0.5, 0.8):
        assert m.d_alpha_printed(p, p, a) == pytest.approx(0.0, abs=1e-15)
        assert m.d_alpha_consistent(p, p, a) == pytest.approx(0.0, abs=1e-15)


def test_forms_coincide_only_at_half():
    p, q = [0.7, 0.2, 0.1], [0.1, 0.3, 0.6]
    assert m.d_alpha_printed(p, q, 0.5) == pytest.approx(m.d_alpha_consistent(p, q, 0.5), rel=1e-12)
    assert m.d_alpha_printed(p, q, 0.8) != pytest.approx(m.d_alpha_consistent(p, q, 0.8), rel=1e-3)


def test_alpha_domain_is_open_interval():
    for div in (m.d_alpha_printed, m.d_alpha_consistent):
        for a in (0.0, 1.0):
            with pytest.raises(ValueError):
                div([1.0], [1.0], a)


def test_c1_consistent_form_satisfies_stated_properties():
    result = runner.c1_objective()
    assert result["gkd_consistent_form"]["all_stated_properties_hold"]
    assert result["verdict"] == "PASS"


def test_c1_printed_form_breaks_stated_properties():
    result = runner.c1_objective()
    printed = result["printed_form"]
    assert not result["printed_form_matches_stated_properties"]
    assert not printed["alpha_to_0"]["holds"]
    assert printed["bounded_by_h_alpha"]["violations"] > 0


def test_pseudo_verification_requires_both_checks():
    assert m.pseudo_verify("A", "A", "A")
    assert not m.pseudo_verify("A", "B", "A")
    assert not m.pseudo_verify("A", "A", "B")


def test_consensus_gate_discards_only_full_agreement():
    assert m.consensus(["A", "A"], "A") == 1.0
    assert m.consensus(["B", "C"], "A") == 0.0
    with pytest.raises(ValueError):
        m.consensus([], "A")
    base = {"fresh_answer": "A", "paraphrase_answer": "A", "candidate_answer": "A"}
    decisions = m.select_samples([
        {**base, "id": "all", "question": "q1", "student_rollouts": ["A", "A", "A"]},
        {**base, "id": "none", "question": "q2", "student_rollouts": ["B", "B", "B"]},
    ])
    assert [d["reason"] for d in decisions] == ["TRIVIAL", "KEPT"]


def test_c2_frozen_fixture_matches():
    result = runner.c2_selection()
    assert result["matched"] == result["cases"] == 12
    assert result["kept_with_wrong_candidate_answer"] == ["s06-consistent-generator-error"]


def test_select_samples_records_seen_questions_for_next_round():
    seen = set()
    m.select_samples([{"id": "x", "question": "Q", "candidate_answer": "A", "fresh_answer": "A", "paraphrase_answer": "A", "student_rollouts": ["B"]}], seen)
    assert seen == {"q"}


def test_c3_ema_and_c4_loss():
    assert runner.c3_ema()["verdict"] == "PASS"
    assert runner.c4_loss()["verdict"] == "PASS"


def test_ema_rejects_invalid_beta():
    with pytest.raises(ValueError):
        m.ema_update([0.0], [1.0], 0.0)


def test_loss_rejects_fully_masked_sample():
    with pytest.raises(ValueError):
        m.opst_loss([[[0.5, 0.5]]], [[[0.5, 0.5]]], [[0]], 0.8)


def test_committed_evidence_matches_current_code():
    result_path = STUDY / "evidence" / "opst_mechanism_v1.result.json"
    if not result_path.exists():
        pytest.skip("evidence not yet produced")
    committed = json.loads(result_path.read_text())
    hashes = committed["artifact_hashes"]
    assert hashes["implementation_sha256"] == runner._sha256(STUDY / "experiments" / "opst_mechanism.py")
    assert hashes["fixture_sha256"] == runner._sha256(STUDY / "fixtures" / "opst_selection_v1.json")
    assert all(c["verdict"] == "PASS" for c in committed["claims"])
