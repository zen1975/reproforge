"""Frozen synthetic mechanism/protocol verification for HAD."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CORE = ROOT / "capabilities" / "training.harness-aware-action-distillation" / "had.py"


def _load():
    spec = importlib.util.spec_from_file_location("had_core", CORE)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load HAD core")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run():
    had = _load()

    harness = had.HarnessRecord(
        admissible_actions=frozenset({
            "go sink",
            "go cabinet",
            "clean plate object=plate",
            "put plate object=plate",
            "wait",
        }),
        held_objects=frozenset({"plate"}),
        no_effect_actions=frozenset({"wait"}),
    )

    changed_valid = had.build_preference(
        teacher_with_harness_action="go sink",
        teacher_without_harness_action="go cabinet",
        harness=harness,
    )
    same_action = had.build_preference(
        teacher_with_harness_action="go sink",
        teacher_without_harness_action="go sink",
        harness=harness,
    )
    invalid_unheld_harness = had.HarnessRecord(
        admissible_actions=frozenset({"put plate object=plate", "go sink"}),
        held_objects=frozenset(),
        no_effect_actions=frozenset(),
    )
    invalid_unheld = had.build_preference(
        teacher_with_harness_action="put plate object=plate",
        teacher_without_harness_action="go sink",
        harness=invalid_unheld_harness,
    )
    invalid_unavailable = had.build_preference(
        teacher_with_harness_action="teleport",
        teacher_without_harness_action="go sink",
        harness=harness,
    )
    invalid_no_effect = had.build_preference(
        teacher_with_harness_action="wait",
        teacher_without_harness_action="go sink",
        harness=harness,
    )

    margin = had.action_margin(
        [-0.20, -0.30],
        [-1.00, -1.20],
    )
    pref_loss = had.masked_preference_loss(
        changed_valid,
        positive_action_token_logprobs=[-0.20, -0.30],
        negative_action_token_logprobs=[-1.00, -1.20],
        beta=0.5,
    )
    same_loss = had.masked_preference_loss(
        same_action,
        positive_action_token_logprobs=[-0.20],
        negative_action_token_logprobs=[-0.20],
        beta=0.5,
    )
    invalid_loss = had.masked_preference_loss(
        invalid_unheld,
        positive_action_token_logprobs=[-0.20],
        negative_action_token_logprobs=[-1.00],
        beta=0.5,
    )
    lambda_value = had.gradient_balance_lambda(
        distillation_grad_norm=4.0,
        preference_grad_norm=2.0,
        rho=0.5,
    )
    zero_lambda = had.gradient_balance_lambda(
        distillation_grad_norm=4.0,
        preference_grad_norm=0.0,
        rho=0.5,
    )

    checks = {
        "harness_changes_teacher_action_creates_active_pair": (
            changed_valid.active_contrast and changed_valid.valid_positive
        ),
        "identical_teacher_actions_are_gradient_neutral": (
            not same_action.active_contrast and same_loss == 0.0
        ),
        "unheld_object_positive_is_filtered": (
            not invalid_unheld.valid_positive and invalid_loss == 0.0
        ),
        "unavailable_action_positive_is_filtered": not invalid_unavailable.valid_positive,
        "repeated_no_effect_positive_is_filtered": not invalid_no_effect.valid_positive,
        "action_only_length_normalized_margin": abs(margin - 0.85) < 1e-12,
        "pairwise_logistic_loss_positive": pref_loss > 0.0,
        "beta_default_matches_paper": abs(
            had.preference_loss(margin, beta=0.5) - pref_loss
        ) < 1e-12,
        "gradient_balance_matches_rho_half": abs(lambda_value - 1.0) < 1e-12,
        "zero_preference_gradient_yields_zero_lambda": zero_lambda == 0.0,
    }

    return {
        "experiment_id": "had-synthetic-protocol-v1",
        "beta": 0.5,
        "rho": 0.5,
        "checks": checks,
        "passed": sum(int(v) for v in checks.values()),
        "check_count": len(checks),
        "all_pass": all(checks.values()),
        "example_margin": margin,
        "example_preference_loss": pref_loss,
        "gradient_balance_lambda": lambda_value,
        "boundary": (
            "Independent synthetic mechanism/protocol verification only. "
            "No teacher/student model inference, benchmark rollouts, or paper-level "
            "training result is reproduced here."
        ),
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
