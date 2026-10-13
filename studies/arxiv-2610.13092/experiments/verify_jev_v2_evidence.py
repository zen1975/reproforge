"""CI-safe integrity verifier for committed jev-live-systemone-check-v2 evidence (no network, no keys).

Verifies per-arm evidence files and, when both arms of a phase exist, the paired analysis file.
Exit 0 with NOT_RUN when nothing is committed yet. Integrity only: poor results verify fine.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import jev_v2_analysis as an  # noqa: E402

EVIDENCE = HERE.parent / "evidence"


def verify_dir(evidence_dir: Path = EVIDENCE) -> dict:
    """Tags: `pilot` (generator g1), `pilot2` (g2 calibration), `test`. Files: jev_v2_<tag>_{jev,control}.result.json
    and jev_v2_<tag>_analysis.json."""
    report, errors = {}, []
    tags = sorted({p.name.split("_")[2] for p in evidence_dir.glob("jev_v2_*_*.json")}) if evidence_dir.exists() else []
    for tag in tags:
        evs = {}
        for arm in ("jev", "control"):
            path = evidence_dir / f"jev_v2_{tag}_{arm}.result.json"
            if path.exists():
                evs[arm] = json.loads(path.read_text())
                errs = an.verify_arm(evs[arm])
                report[f"{tag}_{arm}"] = "OK" if not errs else errs
                errors += errs
        analysis_path = evidence_dir / f"jev_v2_{tag}_analysis.json"
        if analysis_path.exists():
            if len(evs) == 2:
                errs = an.verify_analysis(json.loads(analysis_path.read_text()), evs["jev"], evs["control"])
            else:
                errs = ["analysis present without both arm evidence files"]
            report[f"{tag}_analysis"] = "OK" if not errs else errs
            errors += errs
    status = "NOT_RUN" if not report else ("EVIDENCE_VERIFIED" if not errors else "EVIDENCE_INVALID")
    return {"status": status, "report": report}


def main() -> int:
    out = verify_dir()
    print(json.dumps(out, indent=2))
    return 1 if out["status"] == "EVIDENCE_INVALID" else 0


if __name__ == "__main__":
    sys.exit(main())
