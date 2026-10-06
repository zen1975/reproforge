from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"


def test_piped_workflow_commands_fail_closed():
    offenders = []
    for path in sorted(WORKFLOWS.glob("*.yml")):
        text = path.read_text()
        if "| tee" in text and "set -o pipefail" not in text:
            offenders.append(path.name)
    assert offenders == [], f"piped workflow commands can mask failures: {offenders}"
