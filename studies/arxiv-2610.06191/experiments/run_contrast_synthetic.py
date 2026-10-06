"""Synthetic protocol test for the time-matched contrast."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
METRIC = ROOT / "capabilities" / "agent.evidence-aware-stopping-gate" / "contrast.py"


def _load():
    spec = importlib.util.spec_from_file_location("contrast", METRIC)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load contrast")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _trajectory(question_id, judgments, finish_at):
    actions = ["search"] * (len(judgments) + 1)
    if finish_at is not None:
        actions[finish_at] = "finish"
    return {"question_id": question_id, "actions": actions, "judgments": judgments}


def run():
    mod = _load()

    evidence_integrating = []
    clock_driven = []
    for q in range(40):
        # matched decision t=4:
        # all-useless trajectories answer, mixed-evidence trajectories continue.
        evidence_integrating.append(
            _trajectory(f"e{q}", ["USELESS"] * 4, 4)
        )
        evidence_integrating.append(
            _trajectory(f"e{q}", ["USELESS", "USEFUL", "USELESS", "USELESS"], None)
        )

        # clock-driven: both exposure groups answer at the same decision time.
        clock_driven.append(
            _trajectory(f"c{q}", ["USELESS"] * 4, 4)
        )
        clock_driven.append(
            _trajectory(f"c{q}", ["USEFUL", "USELESS", "USELESS", "USELESS"], 4)
        )

    positive = mod.time_matched_contrast(
        evidence_integrating, t_min=4, t_max=4, bootstrap_samples=200, seed=1
    )
    zero = mod.time_matched_contrast(
        clock_driven, t_min=4, t_max=4, bootstrap_samples=200, seed=1
    )

    return {
        "experiment_id": "time-matched-contrast-synthetic-v1",
        "evidence_integrating_delta": positive["delta"],
        "clock_driven_delta": zero["delta"],
        "positive_expected": positive["delta"] > 0.9,
        "zero_expected": abs(zero["delta"]) < 1e-12,
        "all_pass": positive["delta"] > 0.9 and abs(zero["delta"]) < 1e-12,
        "boundary": "Synthetic metric semantics test only; no paper episodes or model outputs are used.",
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
