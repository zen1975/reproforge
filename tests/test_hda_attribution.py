from __future__ import annotations

import importlib.util
from pathlib import Path

MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "capabilities"
    / "research.harness-delta-attribution-auditor"
    / "attribution.py"
)
SPEC = importlib.util.spec_from_file_location("hda_attribution", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
attribute_gains = MODULE.attribute_gains
paired_bootstrap_ci = MODULE.paired_bootstrap_ci


def test_hda_components_conserve_observed_gain_and_report_bounded_shares():
    base = [1] * 16 + [0] * 24
    scaled = [1] * 22 + [0] * 18
    evolved = [1] * 32 + [0] * 8
    neutralized = [1] * 26 + [0] * 14
    result = attribute_gains(base, scaled, evolved, neutralized, significant_positive_gain=True)
    assert abs(result["delta"] - 0.4) < 1e-12
    assert abs(result["raw_components"]["O_overfitting"] - 0.15) < 1e-12
    assert abs(result["raw_components"]["T_test_time_scaling"] - 0.15) < 1e-12
    assert abs(result["raw_components"]["G_residual_upper_bound"] - 0.10) < 1e-12
    assert abs(result["raw_identity_error"]) < 1e-12
    assert result["reported_shares_percent"] == {"O": 37.5, "T": 37.5, "G": 25.0}


def test_insignificant_gain_is_not_attributed():
    base = [0, 1, 0, 1] * 10
    result = attribute_gains(base, base, base, base, significant_positive_gain=False)
    assert result["status"] == "WITHIN_NOISE_OR_NO_POSITIVE_GAIN"
    assert result["attribution_assigned"] is False


def test_paired_bootstrap_is_deterministic_for_fixed_local_settings():
    base = [1] * 16 + [0] * 24
    evolved = [1] * 32 + [0] * 8
    first = paired_bootstrap_ci(base, evolved, resamples=2000, seed=20261020)
    second = paired_bootstrap_ci(base, evolved, resamples=2000, seed=20261020)
    assert first == second
    assert first["significant_positive_gain"] is True


def test_rejects_mismatched_pair_lengths():
    try:
        paired_bootstrap_ci([0, 1], [1])
    except ValueError as exc:
        assert "equal lengths" in str(exc)
    else:
        raise AssertionError("mismatched pairs must fail closed")


def test_normalized_reporting_shares_are_capped_and_sum_to_100():
    base = [0, 0, 0, 0]
    scaled = [0, 0, 0, 1]
    evolved = [1, 1, 1, 1]
    neutralized = [0, 0, 0, 0]
    result = attribute_gains(base, scaled, evolved, neutralized, significant_positive_gain=True)
    shares = result["reported_shares_percent"]
    assert shares["O"] == 100.0
    assert shares["T"] == 0.0
    assert shares["G"] == 0.0
    assert sum(shares.values()) == 100.0


def test_nonpositive_gain_is_not_attributed_even_if_flag_is_true():
    base = [1, 1, 0, 0]
    evolved = [0, 1, 0, 0]
    result = attribute_gains(base, base, evolved, evolved, significant_positive_gain=True)
    assert result["attribution_assigned"] is False


def test_rejects_nonfinite_scores():
    try:
        paired_bootstrap_ci([0.0, float("nan")], [1.0, 1.0])
    except ValueError as exc:
        assert "finite" in str(exc)
    else:
        raise AssertionError("nonfinite values must fail closed")
