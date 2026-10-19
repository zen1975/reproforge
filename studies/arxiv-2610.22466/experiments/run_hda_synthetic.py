"""Run a frozen, synthetic HDA mechanism test; not a paper benchmark."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CAPABILITY_DIR = ROOT / "capabilities" / "research.harness-delta-attribution-auditor"
sys.path.insert(0, str(CAPABILITY_DIR))
from attribution import attribute_gains, mean, paired_bootstrap_ci  # noqa: E402

STUDY_DIR = Path(__file__).resolve().parents[1]
FIXTURE_PATH = STUDY_DIR / "fixtures" / "hda_synthetic_v1.json"
OUTPUT_PATH = STUDY_DIR / "evidence" / "hda_synthetic_v1.result.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    search = fixture["search"]
    base = [row["baseline"] for row in search]
    scaled = [row["compute_matched_baseline"] for row in search]
    evolved = [row["evolved"] for row in search]
    neutralized = [row["neutralized_evolved"] for row in search]
    settings = fixture["local_bootstrap_analogue"]
    bootstrap = paired_bootstrap_ci(
        base,
        evolved,
        resamples=settings["resamples"],
        seed=settings["seed"],
        alpha=settings["alpha"],
    )
    attribution = attribute_gains(
        base,
        scaled,
        evolved,
        neutralized,
        significant_positive_gain=bootstrap["significant_positive_gain"],
    )
    held = fixture["heldout"]
    held_base = mean(row["baseline"] for row in held)
    held_evolved = mean(row["evolved"] for row in held)
    expected = fixture["expected"]
    checks = {
        "delta": abs(attribution["delta"] - expected["delta"]) < 1e-12,
        "components": all(
            abs(attribution["raw_components"][key] - value) < 1e-12
            for key, value in expected["raw_components"].items()
        ),
        "reported_shares": all(
            abs(attribution["reported_shares_percent"][key] - value) < 1e-9
            for key, value in expected["reported_shares_percent"].items()
        ),
        "heldout_gain": abs((held_evolved - held_base) - expected["heldout_gain"]) < 1e-12,
        "bootstrap_positive": bootstrap["significant_positive_gain"],
    }
    result = {
        "evaluation_id": fixture["evaluation_id"],
        "evaluation_type": fixture["evaluation_type"],
        "paper_reproduction": False,
        "fixture_frozen": fixture["frozen"],
        "search_task_count": len(search),
        "heldout_task_count": len(held),
        "search_significance": bootstrap,
        "attribution": attribution,
        "heldout_transfer": {
            "baseline_score": held_base,
            "evolved_score": held_evolved,
            "gain": held_evolved - held_base,
            "used_for_tuning": False,
            "interpretation": (
                "Synthetic split-only illustration; not evidence of real generalization."
            ),
        },
        "compute_units_per_task": fixture["compute_units_per_task"],
        "expected_values_match": checks,
        "all_expected_values_match": all(checks.values()),
        "artifact_hashes": {
            "fixture_sha256": _sha256(FIXTURE_PATH),
            "implementation_sha256": _sha256(CAPABILITY_DIR / "attribution.py"),
        },
        "limitations": [
            "No LLM, model weights, author code, or published benchmark was run.",
            (
                "The bootstrap parameters are independent local analogue settings, "
                "not inferred paper settings."
            ),
            (
                "Compute matching and overfitting neutralization are represented by "
                "declared synthetic score vectors, not executed harness variants."
            ),
            (
                "The synthetic prefix fixture is for arithmetic and guard testing only; "
                "it does not support a real-world transfer claim."
            ),
        ],
    }
    OUTPUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_expected_values_match"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
