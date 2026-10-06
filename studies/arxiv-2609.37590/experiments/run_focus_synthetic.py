"""Frozen synthetic mechanism/protocol benchmark for FOCUS core."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CORE = ROOT / "capabilities" / "agent.decision-preserving-context-compressor" / "compressor.py"


def _load():
    spec = importlib.util.spec_from_file_location("focus_core", CORE)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load compressor")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _spans(mod, n):
    return [
        mod.Span(f"s_{i}", f"reason-{i}", f"action-{i}", f"observation-{i}")
        for i in range(1, n + 1)
    ]


def run():
    mod = _load()
    cases = []

    # Default N=3, tau=0.3: any span cited by >=1/3 rollouts is retained.
    result = mod.compress(
        _spans(mod, 6),
        [
            {"s_1", "s_3"},
            {"s_1", "s_3", "s_5"},
            {"s_1", "s_4"},
        ],
        tau=0.3,
    )
    expected = ("s_1", "s_3", "s_4", "s_5")
    cases.append({
        "id":"citation-frequency-selection",
        "retained":result.retained_ids,
        "expected":expected,
        "pass":result.retained_ids == expected,
    })

    # A low-citation state/negative-constraint span is dropped optimistically.
    optimistic = mod.compress(
        _spans(mod, 5),
        [{"s_1", "s_2"}, {"s_1"}, {"s_1", "s_2"}],
        tau=0.3,
    )
    # Defensive verification rescues s_4 without removing utility-retained spans.
    defensive = mod.compress(
        _spans(mod, 5),
        [{"s_1", "s_2"}, {"s_1"}, {"s_1", "s_2"}],
        tau=0.3,
        rescued_ids={"s_4"},
    )
    cases.append({
        "id":"defensive-rescue",
        "optimistic_retained":optimistic.retained_ids,
        "defensive_retained":defensive.retained_ids,
        "pass":(
            "s_4" not in optimistic.retained_ids
            and "s_4" in defensive.retained_ids
            and set(optimistic.retained_ids).issubset(defensive.retained_ids)
        ),
    })

    # Known limitation: a set-valued plan can cite only a generalized procedure,
    # causing per-entity spans to receive zero utility and be pruned.
    limitation = mod.compress(
        _spans(mod, 6),
        [{"s_1"}, {"s_1"}, {"s_1"}],
        tau=0.3,
    )
    entity_spans = {"s_3", "s_4", "s_5", "s_6"}
    cases.append({
        "id":"set-valued-goal-limitation",
        "entity_spans_dropped":sorted(entity_spans & set(limitation.dropped_ids)),
        "expected_negative_evidence":True,
        "pass":entity_spans.issubset(set(limitation.dropped_ids)),
    })

    # Whole-span integrity: selector returns span ids only; it never truncates fields.
    original = _spans(mod, 3)
    integrity = mod.compress(original, [{"s_2"}, {"s_2"}, {"s_2"}], tau=0.3)
    retained_objects = [span for span in original if span.id in integrity.retained_ids]
    cases.append({
        "id":"whole-span-integrity",
        "retained_ids":integrity.retained_ids,
        "pass":(
            len(retained_objects) == 1
            and retained_objects[0].reasoning == "reason-2"
            and retained_objects[0].action == "action-2"
            and retained_objects[0].observation == "observation-2"
        ),
    })

    passed = sum(int(case["pass"]) for case in cases)
    return {
        "experiment_id":"focus-synthetic-protocol-v1",
        "paper_defaults":{"N":3,"tau":0.3},
        "case_count":len(cases),
        "passed":passed,
        "pass_rate":passed/len(cases),
        "all_pass":passed==len(cases),
        "cases":cases,
        "boundary":"Synthetic deterministic protocol/mechanism test. Rollout dependencies are frozen fixtures, not LLM-generated paper benchmark trajectories."
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True, default=list))
