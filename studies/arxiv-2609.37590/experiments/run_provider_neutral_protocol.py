"""Protocol-shape verification for the provider-neutral FOCUS harness."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CAP = ROOT / "capabilities" / "agent.decision-preserving-context-compressor"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run():
    core = _load(CAP / "compressor.py", "focus_core_protocol")
    harness = _load(CAP / "harness.py", "focus_harness_protocol")

    spans = [
        core.Span("s_1", "find email", "lookup", "client@example.com"),
        core.Span("s_2", "old login", "auth", "old password invalid"),
        core.Span("s_3", "new auth", "secret", "NEW_TOKEN"),
        core.Span("s_4", "invoice state", "open", "INV-42 draft"),
        core.Span("s_5", "approval", "queue", "INV-42 approved"),
        core.Span("s_6", "noise", "note", "office lunch Friday"),
    ]

    calls = []
    scripted = [
        """Step: Send approved invoice to client | Depends on: [s_1, s_5]
Step: authenticate if needed | Depends on: [s_3]
Rescued Spans: [s_2] | Reason: prevents repeating invalid password""",
        """Step: authenticate and send | Depends on: [s_1, s_3, s_5]
Rescued Spans: [s_2] | Reason: negative login constraint""",
        """Step: send finance-approved invoice | Depends on: [s_1, s_5]
Rescued Spans: [s_2] | Reason: failed auth state must be preserved""",
    ]

    def draft(**kwargs):
        calls.append(kwargs)
        return scripted[len(calls) - 1]

    under = harness.run_focus(
        spans,
        goal="send approved invoice",
        context_tokens=1900,
        memory_budget_tokens=2048,
        draft=draft,
    )
    over = harness.run_focus(
        spans,
        goal="send approved invoice",
        context_tokens=2500,
        memory_budget_tokens=2048,
        draft=draft,
        rollouts_n=3,
        tau=0.3,
        draft_temperature=0.7,
        seed=42,
    )

    checks = {
        "under_budget_no_compression": (
            not under.compression_triggered
            and under.draft_calls == 0
            and under.retained_ids == tuple(span.id for span in spans)
        ),
        "over_budget_exactly_n_drafts": over.compression_triggered and over.draft_calls == 3,
        "paper_temperature_forwarded": all(call["temperature"] == 0.7 for call in calls),
        "seed_offsets_forwarded": [call["seed"] for call in calls] == [42, 43, 44],
        "dependency_frequency_selection": set(over.retained_ids) >= {"s_1", "s_3", "s_5"},
        "defensive_rescue_union": "s_2" in over.retained_ids and "s_2" in over.rescued_ids,
        "irrelevant_span_pruned": "s_6" in over.dropped_ids,
    }

    return {
        "experiment_id": "focus-provider-neutral-protocol-v1",
        "published_defaults": {
            "rollouts_n": 3,
            "tau": 0.3,
            "draft_temperature": 0.7,
            "seed": 42,
            "officebench_budget_tokens": 2048,
        },
        "checks": checks,
        "passed": sum(int(value) for value in checks.values()),
        "check_count": len(checks),
        "all_pass": all(checks.values()),
        "retained_ids": list(over.retained_ids),
        "dropped_ids": list(over.dropped_ids),
        "utility": over.utility,
        "boundary": (
            "Scripted draft outputs verify the published control-flow semantics only. "
            "This is protocol-shape evidence, not model-quality or benchmark reproduction."
        ),
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
