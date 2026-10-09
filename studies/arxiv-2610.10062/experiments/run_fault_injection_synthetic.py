"""Run the independent synthetic fault-injection benchmark."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
MODULE = ROOT / "capabilities" / "agent.tool-fault-auditor" / "fault_audit.py"
OUTPUT = ROOT / "studies" / "arxiv-2610.10062" / "evidence" / "fault_synthetic_v1.result.json"


def main() -> None:
    spec = importlib.util.spec_from_file_location("fault_audit", MODULE)
    if spec is None or spec.loader is None:
        raise RuntimeError("module unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    result = module.run_synthetic()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in result.items() if key != "trials"}, sort_keys=True))


if __name__ == "__main__":
    main()
