import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
ROW = re.compile(r"^\| \[`(arxiv-[^`]+)`\]\([^)]*\) \| [^|]+ \| `([A-Z_]+)` \| `([A-Z_]+)` \| (complete|open) \|$")


def _index_rows():
    text = (ROOT / "studies" / "README.md").read_text()
    return {m.group(1): m.groups()[1:] for m in map(ROW.match, text.splitlines()) if m}


def test_study_index_matches_status_files():
    rows = _index_rows()
    expected = {}
    for status_path in sorted((ROOT / "studies").glob("arxiv-*/status.yaml")):
        status = yaml.safe_load(status_path.read_text())
        expected[status["study_id"]] = (
            status["lifecycle"],
            status["reproduction_status"],
            "complete" if status["free_light_phase_complete"] else "open",
        )
    assert rows == expected
