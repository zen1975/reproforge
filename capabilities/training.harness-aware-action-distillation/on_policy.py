"""Provider-neutral on-policy preference-record construction for HAD."""

from __future__ import annotations

from typing import Iterable, NamedTuple


class VisitedState(NamedTuple):
    state_id: str
    state: str
    actions: tuple[str, ...]
    harness_admissible_actions: frozenset[str]
    held_objects: frozenset[str]
    no_effect_actions: frozenset[str]
    student_action: str


class PairedTeacherRecord(NamedTuple):
    state_id: str
    student_action: str
    teacher_with_harness_action: str
    teacher_without_harness_action: str
    active_contrast: bool
    positive_valid: bool
    rejection_reason: str | None


def validate_preferred_action(
    action: str,
    *,
    admissible_actions: frozenset[str],
    held_objects: frozenset[str],
    no_effect_actions: frozenset[str],
    required_object: str | None = None,
) -> tuple[bool, str | None]:
    if action not in admissible_actions:
        return False, "not_admissible"
    if action in no_effect_actions:
        return False, "known_no_effect"
    if required_object is not None and required_object not in held_objects:
        return False, "required_object_not_held"
    return True, None


def build_paired_record(
    visited: VisitedState,
    *,
    teacher_with_harness_action: str,
    teacher_without_harness_action: str,
    required_object: str | None = None,
) -> PairedTeacherRecord:
    valid, reason = validate_preferred_action(
        teacher_with_harness_action,
        admissible_actions=visited.harness_admissible_actions,
        held_objects=visited.held_objects,
        no_effect_actions=visited.no_effect_actions,
        required_object=required_object,
    )
    return PairedTeacherRecord(
        state_id=visited.state_id,
        student_action=visited.student_action,
        teacher_with_harness_action=teacher_with_harness_action,
        teacher_without_harness_action=teacher_without_harness_action,
        active_contrast=teacher_with_harness_action != teacher_without_harness_action,
        positive_valid=valid,
        rejection_reason=reason,
    )


def summarize_pairs(records: Iterable[PairedTeacherRecord]) -> dict[str, float | int]:
    rows = tuple(records)
    n = len(rows)
    active = sum(int(row.active_contrast) for row in rows)
    valid = sum(int(row.positive_valid) for row in rows)
    valid_active = sum(int(row.active_contrast and row.positive_valid) for row in rows)
    return {
        "pairs": n,
        "active_contrasts": active,
        "valid_positive": valid,
        "valid_active_contrasts": valid_active,
        "contrast_rate": active / n if n else 0.0,
        "valid_active_rate": valid_active / n if n else 0.0,
    }
