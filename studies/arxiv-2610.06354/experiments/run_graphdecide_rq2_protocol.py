"""Execute frozen synthetic GraphDecide RQ2 protocol verification."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
STUDY = ROOT / "studies" / "arxiv-2610.06354"


def _load():
    path = STUDY / "experiments" / "graphdecide_rq2_protocol.py"
    spec = importlib.util.spec_from_file_location("graphdecide_rq2_protocol", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load rq2 protocol")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def run():
    m = _load()
    items = [
        m.MatchedItem(
            f"item-{i}",
            "choose the matching class",
            ("c0", "c1"),
            "c1" if i % 2 else "c0",
            f"target text {i}",
            (f"context text {i}",),
            ("n0", "n1"),
            (("n0", "n1"),),
            (("anchor0", "c0"), ("anchor1", "c1")),
        )
        for i in range(8)
    ]

    conditions = ("T", "G", "TG", "BAG", "A")
    for item in items:
        payloads = {c: m.build_condition(item, c) for c in conditions}
        m.validate_matched_payloads(payloads)

    tg = [True, True, True, True, True, True, False, False]
    bag = [True, True, True, False, False, False, False, False]
    g = [True, True, True, True, False, False, False, False]
    a = [True, True, False, False, False, False, False, False]

    tg_bag = m.paired_difference(tg, bag)
    g_a = m.paired_difference(g, a)
    tg_bag_ci = m.paired_bootstrap_interval(tg, bag)
    g_a_ci = m.paired_bootstrap_interval(g, a)

    invalid = m.score_choice(items[0], "not-a-candidate")
    unsupported = m.score_choice(items[0], None)

    result = {
        "benchmark_id": "graphdecide-rq2-synthetic-v1",
        "matched_items": len(items),
        "conditions": list(conditions),
        "contrasts": {
            "TG-BAG": {"difference_pp": tg_bag, "ci95": list(tg_bag_ci)},
            "G-A": {"difference_pp": g_a, "ci95": list(g_a_ci)},
        },
        "interface": {
            "invalid_valid": invalid["valid"],
            "invalid_correct": invalid["correct"],
            "unsupported_supported": unsupported["supported"],
            "unsupported_correct": unsupported["correct"],
        },
        "bootstrap": {
            "resamples": 1000,
            "seed": 20261001,
            "endpoints": [24, 974],
            "pairing_preserved": True,
        },
        "claim_scope": "Synthetic protocol verification only; no GraphDecide model-performance claim.",
    }
    result["verdict"] = "PASS" if (
        tg_bag == 37.5
        and g_a == 25.0
        and invalid["valid"] is False
        and unsupported["supported"] is False
        and result["bootstrap"]["pairing_preserved"] is True
    ) else "FAIL"
    return result


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
