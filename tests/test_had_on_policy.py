import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "capabilities" / "training.harness-aware-action-distillation" / "on_policy.py"


def _load():
    spec = importlib.util.spec_from_file_location("had_on_policy_test", MODULE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_pair_builder_tracks_active_valid_contrast():
    mod = _load()
    visited = mod.VisitedState(
        state_id="s1",
        state="holding mug",
        actions=("go sink", "wait"),
        harness_admissible_actions=frozenset({"go sink"}),
        held_objects=frozenset({"mug"}),
        no_effect_actions=frozenset({"wait"}),
        student_action="wait",
    )
    row = mod.build_paired_record(
        visited,
        teacher_with_harness_action="go sink",
        teacher_without_harness_action="wait",
    )
    assert row.active_contrast is True
    assert row.positive_valid is True
    assert row.rejection_reason is None


def test_pair_builder_rejects_no_effect_positive():
    mod = _load()
    visited = mod.VisitedState(
        state_id="s1",
        state="holding mug",
        actions=("go sink", "wait"),
        harness_admissible_actions=frozenset({"go sink", "wait"}),
        held_objects=frozenset({"mug"}),
        no_effect_actions=frozenset({"wait"}),
        student_action="wait",
    )
    row = mod.build_paired_record(
        visited,
        teacher_with_harness_action="wait",
        teacher_without_harness_action="go sink",
    )
    assert row.positive_valid is False
    assert row.rejection_reason == "known_no_effect"


def test_pair_summary_is_fail_safe_on_empty():
    mod = _load()
    assert mod.summarize_pairs([]) == {
        "pairs": 0,
        "active_contrasts": 0,
        "valid_positive": 0,
        "valid_active_contrasts": 0,
        "contrast_rate": 0.0,
        "valid_active_rate": 0.0,
    }
