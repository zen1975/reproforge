"""Audit ReproForge's Δ implementation against pinned official released episodes."""

from __future__ import annotations

import gzip
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
METRIC = ROOT / "capabilities" / "agent.evidence-aware-stopping-gate" / "contrast.py"
PINNED_COMMIT = "2e6404e542b4afdafa3d54d9b18eb1c28c2bafc8"


def _load_metric():
    spec = importlib.util.spec_from_file_location("contrast_audit", METRIC)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load contrast")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_jsonl_gz(path):
    with gzip.open(path, "rt") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: run_official_episode_audit.py <official-repo-checkout>")
    official = Path(sys.argv[1]).resolve()
    paper_values = json.loads(
        (official / "experiments" / "episodes" / "paper_values.json").read_text()
    )
    metric = _load_metric()
    fail_regimes = {
        "persistent",
        "recover_after_1",
        "recover_after_2",
        "recover_after_3",
        "late_onset_from_3",
    }
    keys = []
    episode_root = official / "experiments" / "episodes"
    for key in sorted(paper_values):
        if (episode_root / f"{key}.jsonl.gz").exists():
            keys.append(key)
    rows = []
    all_match = True
    for key in keys:
        episodes = _load_jsonl_gz(
            official / "experiments" / "episodes" / f"{key}.jsonl.gz"
        )
        filtered = [episode for episode in episodes if episode["regime"] in fail_regimes]
        measured = metric.time_matched_contrast(
            filtered, bootstrap_samples=2000, seed=0
        )
        expected = paper_values[key]
        exact_delta = measured["delta"] == expected["delta"]
        exact_ci = (
            measured["ci_low"] == expected["ci_low"]
            and measured["ci_high"] == expected["ci_high"]
        )
        match = exact_delta and exact_ci
        all_match = all_match and match
        rows.append(
            {
                "key": key,
                "measured_delta": measured["delta"],
                "expected_delta": expected["delta"],
                "measured_ci": [measured["ci_low"], measured["ci_high"]],
                "expected_ci": [expected["ci_low"], expected["ci_high"]],
                "exact_delta_match": exact_delta,
                "exact_ci_match": exact_ci,
                "match": match,
                "episode_count": len(episodes),
                "failure_episode_count": len(filtered),
            }
        )

    print(
        json.dumps(
            {
                "audit_id": "official-episodes-delta-audit-v2-all-released",
                "official_repository": "bennidict23/judged-useless-queried-anyway",
                "official_commit": PINNED_COMMIT,
                "cells_audited": len(rows),
                "all_cells_exact_match": all_match,
                "rows": rows,
                "boundary": (
                    "OFFICIAL_AUDIT of released CC BY 4.0 episode data using "
                    "ReproForge's separate Δ implementation. No author data is vendored."
                ),
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
