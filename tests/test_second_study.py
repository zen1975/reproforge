import importlib.util
from pathlib import Path

from reproforge.intake import validate_intake_identity
from reproforge.registry import load_capability
from reproforge.validation import load_document, validate_document

ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT / "studies" / "arxiv-2610.03315"
CAPABILITY = ROOT / "capabilities" / "agent.trajectory-budget-serializer"


def _load_allocator():
    path = CAPABILITY / "serializer.py"
    spec = importlib.util.spec_from_file_location("reproforge_trajectory_allocator", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.allocate_budgets


def test_second_study_authoritative_intake_verifies():
    manifest = load_document(STUDY / "manifest.yaml")
    source = load_document(STUDY / "source-metadata.json")
    schema = load_document(ROOT / "schemas" / "intake-source.schema.json")
    assert validate_document(source, schema) == []
    result = validate_intake_identity(manifest, source)
    assert result["status"] == "VERIFIED"
    assert result["errors"] == []


def test_second_capability_descriptor_validates():
    capability = load_capability(
        CAPABILITY / "capability.yaml",
        ROOT / "schemas" / "capability.schema.json",
    )
    assert capability["status"] == "experimental"
    assert capability["evidence"]["reproduction_status"] == "PARTIAL"


def test_allocator_is_deterministic_and_budget_bounded():
    allocate = _load_allocator()
    args = ([800, 800, 800], ["ok", "warning", "error"], 1200)
    first = allocate(*args)
    second = allocate(*args)
    assert first == second
    assert sum(first) <= 1200
    assert first[2] >= first[1] >= first[0]


def test_allocator_preserves_full_lengths_when_already_within_budget():
    allocate = _load_allocator()
    assert allocate([100, 200], ["ok", "error"], 500) == [100, 200]
