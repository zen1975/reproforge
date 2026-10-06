from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_root_agent_guide_exists():
    guide = ROOT / "AGENTS.md"
    assert guide.exists()
    text = guide.read_text()
    assert "free/lightweight verification" in text
    assert "local/heavy verification" in text
    assert "real implementation" in text


def test_every_study_has_agent_guide():
    studies = sorted((ROOT / "studies").glob("arxiv-*"))
    assert studies
    missing = [
        study.name
        for study in studies
        if (study / "status.yaml").exists() and not (study / "AGENTS.md").exists()
    ]
    assert missing == []


def test_every_capability_has_agent_guide():
    capabilities = [
        path.parent
        for path in (ROOT / "capabilities").glob("*/capability.yaml")
    ]
    assert capabilities
    missing = [
        capability.name
        for capability in capabilities
        if not (capability / "AGENTS.md").exists()
    ]
    assert missing == []


def test_study_guides_cover_local_and_real_work():
    for status in (ROOT / "studies").glob("arxiv-*/status.yaml"):
        text = (status.parent / "AGENTS.md").read_text().lower()
        assert "local/heavy" in text
        assert "real implementation" in text


def test_capability_guides_keep_heavy_work_in_studies():
    for manifest in (ROOT / "capabilities").glob("*/capability.yaml"):
        text = (manifest.parent / "AGENTS.md").read_text().lower()
        assert "heavy/local" in text or "local/heavy" in text
        assert "real implementation" in text
