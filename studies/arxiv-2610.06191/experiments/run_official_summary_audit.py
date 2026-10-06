"""Audit lightweight released-episode summaries against pinned official artifacts."""

from __future__ import annotations

import gzip
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SUMMARY = ROOT / "capabilities" / "agent.evidence-aware-stopping-gate" / "summary.py"
PINNED_COMMIT = "2e6404e542b4afdafa3d54d9b18eb1c28c2bafc8"


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_jsonl_gz(path: Path) -> list[dict]:
    with gzip.open(path, "rt") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: run_official_summary_audit.py <official-repo-checkout>")

    official = Path(sys.argv[1]).resolve()
    ours = _load_module(SUMMARY, "reproforge_summary")
    official_delta = _load_module(
        official / "judged_useless" / "delta.py",
        "official_delta_for_summary_audit",
    )
    paper_values = json.loads(
        (official / "experiments" / "episodes" / "paper_values.json").read_text()
    )
    episode_root = official / "experiments" / "episodes"

    rows = []
    mean6_matches = 0
    answer_matches = 0
    persistent_cells = 0
    for key in sorted(paper_values):
        path = episode_root / f"{key}.jsonl.gz"
        if not path.exists():
            continue
        episodes = _load_jsonl_gz(path)
        measured_mean6 = ours.mean6_success(episodes)
        expected_mean6 = paper_values[key]["mean6"]
        mean6_match = measured_mean6 == expected_mean6
        mean6_matches += int(mean6_match)

        persistent = [e for e in episodes if e["regime"] == "persistent"]
        ours_answer = ours.answer_rate_after_run(persistent, k=5)
        official_answer = official_delta.answer_rate_after_run(persistent, k=5)
        answer_match = ours_answer == official_answer
        answer_matches += int(answer_match)
        persistent_cells += 1

        rows.append(
            {
                "key": key,
                "episode_count": len(episodes),
                "mean6": measured_mean6,
                "paper_mean6": expected_mean6,
                "mean6_exact_match": mean6_match,
                "answer_after_5_useless": ours_answer,
                "official_answer_after_5_useless": official_answer,
                "answer_summary_exact_match": answer_match,
            }
        )

    all_match = (
        len(rows) == mean6_matches
        and persistent_cells == answer_matches
        and bool(rows)
    )
    print(
        json.dumps(
            {
                "audit_id": "official-episode-summary-audit-v1",
                "official_repository": "bennidict23/judged-useless-queried-anyway",
                "official_commit": PINNED_COMMIT,
                "cells_audited": len(rows),
                "mean6_exact_matches": mean6_matches,
                "answer_summary_cells": persistent_cells,
                "answer_summary_exact_matches": answer_matches,
                "all_exact_match": all_match,
                "rows": rows,
                "boundary": (
                    "OFFICIAL_AUDIT of released CC BY 4.0 episode summaries. "
                    "mean6 is checked against stored paper_values; answer-after-five "
                    "is checked against the pinned official toolkit. Original model "
                    "episodes are not regenerated."
                ),
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
