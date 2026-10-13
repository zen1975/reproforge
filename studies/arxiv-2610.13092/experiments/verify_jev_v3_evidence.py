"""CI-safe integrity verifier for committed jev-live-systemone-check-v3a evidence (no network, no keys).

Exit 0 with NOT_RUN when nothing is committed yet. Integrity only: poor results verify fine.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import jev_v3_analysis as an  # noqa: E402


def main() -> int:
    out = an.verify_dir()
    print(json.dumps(out, indent=2))
    return 1 if out["status"] == "EVIDENCE_INVALID" else 0


if __name__ == "__main__":
    sys.exit(main())
